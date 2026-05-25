"""Modelo ORM de una mencion en redes/medios."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Mention(Base):
    __tablename__ = "mentions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Identidad de la fuente (para deduplicar la ingesta de conectores reales).
    source: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    lang: Mapped[str] = mapped_column(String(8), default="es")
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    # Alcance/engagement aproximado (likes + shares + comments).
    engagement: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)

    # Resultado del analisis.
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral", index=True)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    emotion: Mapped[str | None] = mapped_column(String(16), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    actors: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("ix_mentions_source_published", Mention.source, Mention.published_at)
