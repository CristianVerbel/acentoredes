"""Siembra datos demo realistas en la base del monitor.

Genera menciones simuladas a lo largo de un periodo, distribuidas por fuente,
actor, tematica, sentimiento y emocion, con tendencias y "picos" de
conversacion. Permite ver el dashboard funcionando sin credenciales de APIs.

Uso:
    python -m scripts.seed_demo --days 75 --per-day 60 --reset
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Permite ejecutar como `python -m scripts.seed_demo` desde backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_election_config  # noqa: E402
from app.database import SessionLocal, engine, init_db  # noqa: E402
from app.models import Mention  # noqa: E402

SOURCES = [
    ("twitter", 0.42, (5, 800)),     # (id, peso, rango engagement)
    ("news", 0.12, (0, 50)),
    ("reddit", 0.18, (2, 400)),
    ("youtube", 0.12, (10, 2000)),
    ("tiktok", 0.10, (50, 5000)),
    ("instagram", 0.06, (20, 3000)),
]

EMOTION_BY_SENTIMENT = {
    "positive": ["alegria", "confianza"],
    "negative": ["ira", "miedo", "tristeza"],
    "neutral": [None, "confianza"],
}

# Plantillas de texto por sentimiento. {actor} y {topic} se sustituyen.
TEMPLATES = {
    "positive": [
        "Me convence la propuesta de {actor} sobre {topic}. Por fin alguien con un plan serio.",
        "Gran intervencion de {actor} en el debate, sobre todo en el tema de {topic}. #Elecciones",
        "{actor} demuestra liderazgo en {topic}. Tiene mi voto.",
        "Excelente la gestion que plantea {actor} para {topic}, ojala se cumpla.",
        "Confio en {actor}, su discurso sobre {topic} fue claro y con propuestas.",
    ],
    "negative": [
        "Otra vez {actor} con promesas vacias sobre {topic}. Pura demagogia.",
        "Es una verguenza lo que dijo {actor} acerca de {topic}. No le creo nada.",
        "{actor} no tiene ni idea de {topic}, sus propuestas son un desastre.",
        "La corrupcion de siempre con {actor}. El tema de {topic} le queda grande.",
        "Decepcionante {actor}, en {topic} solo repite mentiras. #Fraude",
    ],
    "neutral": [
        "{actor} presento hoy su plan sobre {topic}. Habra que ver los detalles.",
        "En el foro se discutio la postura de {actor} frente a {topic}.",
        "Nota: {actor} hablo de {topic} en la entrevista de esta manana.",
        "Comparan las propuestas de los candidatos en {topic}, incluida la de {actor}.",
        "{actor} respondio preguntas sobre {topic} durante la rueda de prensa.",
    ],
}

# Texto sin actor (conversacion general sobre la tematica).
GENERIC_TEMPLATES = {
    "positive": ["Buenas noticias en {topic}, se nota el avance.", "Ojala mejore el tema de {topic}, hay esperanza."],
    "negative": ["La situacion de {topic} esta cada vez peor, es una crisis.", "Indignante el abandono en {topic}."],
    "neutral": ["Se debate sobre {topic} de cara a las elecciones.", "Reporte sobre {topic} en la region."],
}

SCORE_RANGES = {
    "positive": (0.25, 0.9),
    "negative": (-0.9, -0.25),
    "neutral": (-0.12, 0.12),
}


def weighted_choice(pairs):
    r = random.random() * sum(w for _, w, *_ in pairs)
    upto = 0.0
    for item in pairs:
        upto += item[1]
        if r <= upto:
            return item
    return pairs[-1]


def build_args():
    p = argparse.ArgumentParser(description="Siembra datos demo del monitor")
    p.add_argument("--days", type=int, default=75, help="dias hacia atras a cubrir")
    p.add_argument("--per-day", type=int, default=60, help="menciones promedio por dia")
    p.add_argument("--reset", action="store_true", help="borra menciones existentes antes de sembrar")
    p.add_argument("--seed", type=int, default=42, help="semilla aleatoria")
    return p.parse_args()


def main():
    args = build_args()
    random.seed(args.seed)
    init_db()

    config = get_election_config()
    if not config.actors or not config.topics:
        print("ERROR: define actores y tematicas en config/election.yaml")
        sys.exit(1)

    actors = config.actors
    topics = config.topics

    # Cada actor tiene un "lean" de sentimiento (sesgo de la conversacion).
    leans = {}
    base_leans = [
        {"positive": 0.45, "neutral": 0.30, "negative": 0.25},
        {"positive": 0.30, "neutral": 0.30, "negative": 0.40},
        {"positive": 0.38, "neutral": 0.34, "negative": 0.28},
        {"positive": 0.25, "neutral": 0.35, "negative": 0.40},
    ]
    for i, actor in enumerate(actors):
        leans[actor.id] = base_leans[i % len(base_leans)]

    # Share of voice base por actor (algunos dominan la conversacion).
    sov_weights = [0.36, 0.30, 0.22, 0.12]
    actor_pairs = [(a, sov_weights[i % len(sov_weights)]) for i, a in enumerate(actors)]

    # Picos de conversacion: (dia_relativo, topic_id, sentimiento_dominante, multiplicador)
    spikes = [
        (args.days - 12, "corrupcion", "negative", 2.6),
        (args.days - 30, "economia", "negative", 1.9),
        (args.days - 5, "seguridad", "negative", 2.2),
        (args.days - 45, "salud", "positive", 1.6),
    ]
    spike_map = {d: (t, s, m) for d, t, s, m in spikes}

    db = SessionLocal()
    if args.reset:
        db.query(Mention).delete()
        db.commit()

    now = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    total = 0
    eid = int(datetime.utcnow().timestamp())

    for day_offset in range(args.days):
        day = now - timedelta(days=args.days - 1 - day_offset)
        # Volumen diario con variacion + tendencia creciente hacia el final.
        trend = 1.0 + 0.5 * (day_offset / args.days)
        count = int(random.gauss(args.per_day * trend, args.per_day * 0.25))
        count = max(5, count)

        spike = spike_map.get(day_offset)
        if spike:
            count = int(count * spike[2])

        for _ in range(count):
            source_id, _, eng_range = weighted_choice(SOURCES)

            # Actor (o conversacion generica ~15%).
            if random.random() < 0.15:
                actor = None
            else:
                actor = weighted_choice(actor_pairs)[0]

            # Tematica: si hay pico, sesga hacia su topic.
            if spike and random.random() < 0.55:
                topic = config.topic_by_id(spike[0]) or random.choice(topics)
            else:
                topic = random.choice(topics)

            # Sentimiento.
            if spike and random.random() < 0.6:
                sentiment = spike[1]
            elif actor is not None:
                lean = leans[actor.id]
                sentiment = random.choices(
                    ["positive", "neutral", "negative"],
                    weights=[lean["positive"], lean["neutral"], lean["negative"]],
                )[0]
            else:
                sentiment = random.choices(
                    ["positive", "neutral", "negative"], weights=[0.3, 0.4, 0.3]
                )[0]

            text = _render_text(sentiment, actor, topic)
            score = round(random.uniform(*SCORE_RANGES[sentiment]), 3)
            emotion = random.choice(EMOTION_BY_SENTIMENT[sentiment])
            engagement = random.randint(*eng_range)
            reach = engagement * random.randint(8, 40) + (50000 if source_id == "news" else 0)
            published = day + timedelta(
                hours=random.randint(-11, 11), minutes=random.randint(0, 59)
            )

            eid += 1
            db.add(
                Mention(
                    source=source_id,
                    external_id=f"demo-{eid}",
                    author=_fake_author(source_id),
                    text=text,
                    url=None,
                    lang="es",
                    published_at=published,
                    engagement=engagement,
                    reach=reach,
                    sentiment=sentiment,
                    sentiment_score=score,
                    emotion=emotion,
                    topic=topic.id,
                    actors=[actor.id] if actor else [],
                )
            )
            total += 1

        db.commit()

    db.close()
    print(f"OK: sembradas {total} menciones demo en {args.days} dias.")


def _render_text(sentiment, actor, topic):
    if actor is None:
        tpl = random.choice(GENERIC_TEMPLATES[sentiment])
        return tpl.format(topic=topic.name.lower())
    tpl = random.choice(TEMPLATES[sentiment])
    return tpl.format(actor=actor.name, topic=topic.name.lower())


def _fake_author(source_id):
    handles = ["ciudadano", "ana", "carlos", "votante", "maria", "elpueblo", "juan", "noticias", "analista"]
    if source_id == "news":
        return random.choice(["Diario Nacional", "Radio Capital", "Portal Noticias", "El Observador"])
    return f"@{random.choice(handles)}{random.randint(1, 9999)}"


if __name__ == "__main__":
    main()
