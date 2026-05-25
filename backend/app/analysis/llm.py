"""Analizador opcional con LLM (Claude) para sentimiento/tematica/actores.

Se activa con `USE_LLM_ANALYSIS=true` y `ANTHROPIC_API_KEY` en el .env.
Cae de vuelta al analizador por reglas ante cualquier error, para que el
monitor nunca deje de funcionar.
"""
from __future__ import annotations

import json

from ..config import ElectionConfig, Settings
from .analyzer import AnalysisResult, RuleBasedAnalyzer


class LLMAnalyzer:
    def __init__(self, config: ElectionConfig, settings: Settings):
        from anthropic import Anthropic  # import diferido (dependencia opcional)

        self.config = config
        self.settings = settings
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.fallback = RuleBasedAnalyzer(config)

        self._topics_desc = ", ".join(f"{t.id} ({t.name})" for t in config.topics)
        self._actors_desc = ", ".join(f"{a.id} ({a.name})" for a in config.actors)

    def analyze(self, text: str) -> AnalysisResult:
        prompt = (
            "Eres un analista de escucha digital para una eleccion. Clasifica el "
            "siguiente texto de redes sociales/noticias y responde SOLO con JSON.\n\n"
            f"Tematicas validas (usa el id): {self._topics_desc}\n"
            f"Actores validos (usa el id, puede ser lista vacia): {self._actors_desc}\n\n"
            "Devuelve un objeto JSON con las claves: "
            '{"sentiment": "positive|neutral|negative", '
            '"sentiment_score": numero entre -1 y 1, '
            '"emotion": "ira|miedo|alegria|tristeza|confianza|null", '
            '"topic": "id de tematica o null", '
            '"actors": ["ids de actores mencionados"]}\n\n'
            f"Texto: {text!r}\n"
        )
        try:
            resp = self.client.messages.create(
                model=self.settings.llm_model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            payload = resp.content[0].text.strip()
            payload = payload[payload.find("{"): payload.rfind("}") + 1]
            data = json.loads(payload)
            return AnalysisResult(
                sentiment=data.get("sentiment", "neutral"),
                sentiment_score=float(data.get("sentiment_score", 0.0)),
                emotion=(data.get("emotion") or None),
                topic=(data.get("topic") or None),
                actors=list(data.get("actors") or []),
            )
        except Exception:
            return self.fallback.analyze(text)
