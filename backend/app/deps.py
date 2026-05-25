"""Dependencias compartidas de FastAPI (parseo de filtros de consulta)."""
from __future__ import annotations

from datetime import datetime

from dateutil import parser as date_parser
from fastapi import Query

from .queries import Filters


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, OverflowError):
        return None


def get_filters(
    date_from: str | None = Query(None, alias="from", description="ISO date inicio"),
    date_to: str | None = Query(None, alias="to", description="ISO date fin"),
    source: str | None = Query(None, description="Fuente (twitter, news, reddit, youtube...)"),
    actor: str | None = Query(None, description="id de actor"),
    topic: str | None = Query(None, description="id de tematica"),
    sentiment: str | None = Query(None, description="positive | neutral | negative"),
    q: str | None = Query(None, description="busqueda de texto"),
) -> Filters:
    return Filters(
        date_from=_parse_dt(date_from),
        date_to=_parse_dt(date_to),
        source=source,
        actor=actor,
        topic=topic,
        sentiment=sentiment,
        q=q,
    )
