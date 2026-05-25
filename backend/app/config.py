"""Carga de configuracion del monitor: settings de entorno + contexto electoral."""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "election.yaml"


class Settings(BaseSettings):
    """Configuracion de entorno del backend."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{BACKEND_DIR / 'monitor.db'}"
    election_config_path: str = str(DEFAULT_CONFIG_PATH)
    cors_origins: str = "http://localhost:3000"

    # Analisis con LLM (opcional). Si no hay key, se usa el analizador por reglas.
    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-4-20250514"
    use_llm_analysis: bool = False

    # Credenciales opcionales de fuentes reales.
    twitter_bearer_token: str | None = None
    youtube_api_key: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None


# --- Modelos del contexto electoral (election.yaml) -------------------------


class Actor(BaseModel):
    id: str
    name: str
    type: str = "candidate"
    party: str | None = None
    color: str = "#64748b"
    aliases: list[str] = []


class Topic(BaseModel):
    id: str
    name: str
    keywords: list[str] = []


class SourceConfig(BaseModel):
    enabled: bool = False
    label: str = ""
    feeds: list[str] = []
    subreddits: list[str] = []
    query_terms: list[str] = []


class ProjectInfo(BaseModel):
    name: str = "Monitor Electoral"
    language: str = "es"
    country: str = "GENERICO"
    election: str = "Elecciones"
    timezone: str = "UTC"


class ElectionConfig(BaseModel):
    project: ProjectInfo = ProjectInfo()
    actors: list[Actor] = []
    topics: list[Topic] = []
    sources: dict[str, SourceConfig] = {}

    def actor_by_id(self, actor_id: str) -> Actor | None:
        return next((a for a in self.actors if a.id == actor_id), None)

    def topic_by_id(self, topic_id: str) -> Topic | None:
        return next((t for t in self.topics if t.id == topic_id), None)


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()


@functools.lru_cache
def get_election_config() -> ElectionConfig:
    path = Path(get_settings().election_config_path)
    if not path.exists():
        return ElectionConfig()
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = {k: SourceConfig(**(v or {})) for k, v in (raw.get("sources") or {}).items()}
    return ElectionConfig(
        project=ProjectInfo(**(raw.get("project") or {})),
        actors=[Actor(**a) for a in (raw.get("actors") or [])],
        topics=[Topic(**t) for t in (raw.get("topics") or [])],
        sources=sources,
    )
