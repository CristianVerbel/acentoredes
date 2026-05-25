"""Endpoints de metadatos: salud, configuracion del contexto e ingesta manual."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_election_config, get_settings
from ..database import get_db
from ..ingest import build_connectors, run_ingestion
from ..models import Mention

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(Mention)) or 0
    return {"status": "ok", "mentions": count}


@router.get("/config")
def config():
    """Devuelve el contexto electoral (actores, tematicas, fuentes) para el frontend."""
    cfg = get_election_config()
    settings = get_settings()
    connectors = build_connectors(cfg, settings)
    availability = {c.source: c.available for c in connectors}
    return {
        "project": cfg.project.model_dump(),
        "actors": [a.model_dump() for a in cfg.actors],
        "topics": [t.model_dump() for t in cfg.topics],
        "sources": {
            sid: {
                "label": sc.label or sid,
                "enabled": sc.enabled,
                "available": availability.get(sid, False),
            }
            for sid, sc in cfg.sources.items()
        },
        "llm_analysis": settings.use_llm_analysis and bool(settings.anthropic_api_key),
    }


@router.post("/ingest")
def ingest(limit_per_source: int = 100, db: Session = Depends(get_db)):
    """Dispara una ronda de ingesta sobre los conectores con credenciales."""
    result = run_ingestion(db, limit_per_source=limit_per_source)
    return {"inserted": result}
