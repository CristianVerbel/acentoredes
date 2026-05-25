"""Esquemas Pydantic para las respuestas de la API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MentionOut(BaseModel):
    id: int
    source: str
    author: str | None
    text: str
    url: str | None
    lang: str
    published_at: datetime
    engagement: int
    reach: int
    sentiment: str
    sentiment_score: float
    emotion: str | None
    topic: str | None
    actors: list[str]

    model_config = {"from_attributes": True}


class MentionsPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[MentionOut]


class SentimentBreakdown(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class Summary(BaseModel):
    total_mentions: int
    total_reach: int
    total_engagement: int
    sentiment: SentimentBreakdown
    avg_sentiment_score: float
    net_sentiment: float  # (% positivas - % negativas), rango -100..100
    unique_authors: int
    sources_count: int
    top_topic: str | None
    period_start: datetime | None
    period_end: datetime | None


class TimelinePoint(BaseModel):
    date: str
    total: int
    positive: int
    neutral: int
    negative: int
    net_sentiment: float


class TopicStat(BaseModel):
    id: str
    name: str
    count: int
    positive: int
    neutral: int
    negative: int
    net_sentiment: float
    avg_score: float


class SourceStat(BaseModel):
    source: str
    label: str
    count: int
    positive: int
    neutral: int
    negative: int
    net_sentiment: float


class ShareOfVoiceItem(BaseModel):
    actor_id: str
    name: str
    party: str | None
    color: str
    count: int
    share: float  # porcentaje 0..100
    positive: int
    neutral: int
    negative: int
    net_sentiment: float
    total_reach: int


class EmotionStat(BaseModel):
    emotion: str
    count: int


class ActorTopicCell(BaseModel):
    actor_id: str
    topic_id: str
    count: int
    net_sentiment: float
