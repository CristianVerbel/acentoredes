"""Punto de entrada de la API del Monitor Electoral de escucha digital."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_election_config, get_settings
from .database import init_db
from .routers import analytics, mentions, meta


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    cfg = get_election_config()

    app = FastAPI(
        title=f"{cfg.project.name} - API de Escucha Digital",
        description=(
            "Monitor de temáticas y sentimiento sobre elecciones. "
            "Ingesta menciones de redes/medios, las analiza y expone analíticas."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta.router)
    app.include_router(analytics.router)
    app.include_router(mentions.router)

    @app.get("/")
    def root():
        return {"name": cfg.project.name, "docs": "/docs"}

    return app


app = create_app()
