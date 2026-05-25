"""Orquestador de ingesta: corre los conectores, analiza y persiste menciones."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .analysis.analyzer import get_analyzer
from .config import ElectionConfig, Settings, get_election_config, get_settings
from .connectors import (
    BaseConnector,
    NewsRSSConnector,
    RedditConnector,
    TwitterConnector,
    YouTubeConnector,
)
from .models import Mention

CONNECTOR_CLASSES = [
    TwitterConnector,
    NewsRSSConnector,
    RedditConnector,
    YouTubeConnector,
]


def build_connectors(config: ElectionConfig, settings: Settings) -> list[BaseConnector]:
    return [cls(config, settings) for cls in CONNECTOR_CLASSES]


def run_ingestion(db: Session, limit_per_source: int = 100) -> dict[str, int]:
    """Ejecuta los conectores disponibles, analiza y guarda menciones nuevas.

    Devuelve un resumen {source: cantidad_insertada}.
    """
    config = get_election_config()
    settings = get_settings()
    analyzer = get_analyzer(config)

    summary: dict[str, int] = {}
    for connector in build_connectors(config, settings):
        if not connector.available:
            summary[connector.source] = 0
            continue
        try:
            raw_mentions = connector.fetch(limit=limit_per_source)
        except Exception:
            summary[connector.source] = 0
            continue

        inserted = 0
        for raw in raw_mentions:
            if raw.external_id and _exists(db, raw.external_id):
                continue
            analysis = analyzer.analyze(raw.text)
            db.add(
                Mention(
                    source=raw.source,
                    external_id=raw.external_id,
                    author=raw.author,
                    text=raw.text,
                    url=raw.url,
                    lang=raw.lang,
                    published_at=raw.published_at,
                    engagement=raw.engagement,
                    reach=raw.reach,
                    **analysis.as_dict(),
                )
            )
            inserted += 1
        db.commit()
        summary[connector.source] = inserted

    return summary


def _exists(db: Session, external_id: str) -> bool:
    return db.scalar(select(Mention.id).where(Mention.external_id == external_id)) is not None
