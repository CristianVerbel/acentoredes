"""Analisis de menciones: sentimiento, emocion, tematica y actores.

Estrategia en dos niveles:
  1. Analizador basado en reglas (lexico en espanol + palabras clave de config).
     Funciona sin dependencias externas ni credenciales.
  2. Analizador con LLM (Claude) opcional, si `use_llm_analysis` esta activo y
     hay `anthropic_api_key`. Ver `llm.py`.

El resultado de `analyze()` es un dict con: sentiment, sentiment_score, emotion,
topic, actors.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from ..config import ElectionConfig

# --- Lexicos en espanol (señales simples, ampliables) -----------------------

POSITIVE_WORDS = {
    "bueno", "buena", "excelente", "gran", "mejor", "apoyo", "apoyamos", "ganar",
    "ganamos", "esperanza", "propuesta", "propuestas", "logro", "logros", "exito",
    "felicidades", "orgullo", "confianza", "honesto", "transparente", "solucion",
    "soluciones", "avance", "progreso", "favor", "votare", "votaremos", "lider",
    "fuerte", "positivo", "acierto", "respeto", "admirable", "increible", "bien",
}

NEGATIVE_WORDS = {
    "malo", "mala", "peor", "corrupto", "corrupcion", "mentira", "mentiroso",
    "fraude", "robo", "robar", "ladron", "fracaso", "crisis", "desastre", "verguenza",
    "rechazo", "rechazamos", "miedo", "inseguridad", "violencia", "incompetente",
    "promesas", "populista", "demagogo", "escandalo", "decepcion", "decepcionante",
    "engano", "traicion", "nefasto", "pesimo", "terrible", "indignante", "abuso",
}

NEGATIONS = {"no", "nunca", "jamas", "ni", "tampoco", "sin"}

EMOTION_LEXICON = {
    "ira": {"corrupto", "fraude", "robo", "ladron", "verguenza", "indignante", "abuso", "traicion", "rabia", "furia"},
    "miedo": {"miedo", "inseguridad", "violencia", "crisis", "amenaza", "temor", "peligro"},
    "alegria": {"esperanza", "felicidades", "orgullo", "exito", "logro", "ganamos", "celebrar"},
    "tristeza": {"decepcion", "fracaso", "decepcionante", "pena", "triste", "lamentable"},
    "confianza": {"confianza", "honesto", "transparente", "lider", "respeto", "creible"},
}


@dataclass
class AnalysisResult:
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    emotion: str | None = None
    topic: str | None = None
    actors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "sentiment": self.sentiment,
            "sentiment_score": round(self.sentiment_score, 4),
            "emotion": self.emotion,
            "topic": self.topic,
            "actors": self.actors,
        }


def _normalize(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return text


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zñ@#]+", text)


class RuleBasedAnalyzer:
    """Analizador determinista basado en lexico y palabras clave de config."""

    def __init__(self, config: ElectionConfig):
        self.config = config
        # Precalcula keywords normalizadas por tematica y alias por actor.
        self._topic_keywords = {
            t.id: {_normalize(k) for k in t.keywords} for t in config.topics
        }
        self._actor_aliases = {
            a.id: {_normalize(al) for al in ([a.name] + a.aliases)} for a in config.actors
        }

    def analyze(self, text: str) -> AnalysisResult:
        norm = _normalize(text)
        tokens = _tokens(norm)

        score = self._sentiment_score(tokens)
        sentiment = self._label(score)
        emotion = self._emotion(tokens, sentiment)
        topic = self._topic(norm)
        actors = self._actors(norm)

        return AnalysisResult(
            sentiment=sentiment,
            sentiment_score=score,
            emotion=emotion,
            topic=topic,
            actors=actors,
        )

    def _sentiment_score(self, tokens: list[str]) -> float:
        raw = 0
        hits = 0
        for i, tok in enumerate(tokens):
            polarity = 0
            if tok in POSITIVE_WORDS:
                polarity = 1
            elif tok in NEGATIVE_WORDS:
                polarity = -1
            if polarity == 0:
                continue
            # Negacion en la ventana de 2 tokens previos invierte la polaridad.
            window = tokens[max(0, i - 2):i]
            if any(w in NEGATIONS for w in window):
                polarity *= -1
            raw += polarity
            hits += 1
        if hits == 0:
            return 0.0
        # Normaliza a rango aprox [-1, 1] con saturacion suave.
        return max(-1.0, min(1.0, raw / (hits + 1)))

    @staticmethod
    def _label(score: float) -> str:
        if score > 0.15:
            return "positive"
        if score < -0.15:
            return "negative"
        return "neutral"

    @staticmethod
    def _emotion(tokens: list[str], sentiment: str) -> str | None:
        best, best_hits = None, 0
        token_set = set(tokens)
        for emotion, words in EMOTION_LEXICON.items():
            hits = len(token_set & words)
            if hits > best_hits:
                best, best_hits = emotion, hits
        if best:
            return best
        if sentiment == "positive":
            return "alegria"
        if sentiment == "negative":
            return "ira"
        return None

    def _topic(self, norm_text: str) -> str | None:
        best, best_hits = None, 0
        for topic_id, keywords in self._topic_keywords.items():
            hits = sum(1 for k in keywords if k and k in norm_text)
            if hits > best_hits:
                best, best_hits = topic_id, hits
        return best

    def _actors(self, norm_text: str) -> list[str]:
        found = []
        for actor_id, aliases in self._actor_aliases.items():
            if any(alias and alias in norm_text for alias in aliases):
                found.append(actor_id)
        return found


def get_analyzer(config: ElectionConfig):
    """Devuelve el analizador activo (LLM si esta configurado, si no por reglas)."""
    from ..config import get_settings

    settings = get_settings()
    if settings.use_llm_analysis and settings.anthropic_api_key:
        try:
            from .llm import LLMAnalyzer

            return LLMAnalyzer(config, settings)
        except Exception:
            # Si falla la inicializacion del LLM, degradamos a reglas.
            pass
    return RuleBasedAnalyzer(config)
