"""Construccion de filtros y agregaciones analiticas sobre las menciones."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import String, cast, func, select
from sqlalchemy.orm import Session

from .config import get_election_config
from .models import Mention
from .schemas import (
    EmotionStat,
    ShareOfVoiceItem,
    SourceStat,
    Summary,
    SentimentBreakdown,
    TimelinePoint,
    TopicStat,
)


@dataclass
class Filters:
    date_from: datetime | None = None
    date_to: datetime | None = None
    source: str | None = None
    actor: str | None = None
    topic: str | None = None
    sentiment: str | None = None
    q: str | None = None


def _conditions(f: Filters):
    conds = []
    if f.date_from:
        conds.append(Mention.published_at >= f.date_from)
    if f.date_to:
        conds.append(Mention.published_at <= f.date_to)
    if f.source:
        conds.append(Mention.source == f.source)
    if f.topic:
        conds.append(Mention.topic == f.topic)
    if f.sentiment:
        conds.append(Mention.sentiment == f.sentiment)
    if f.actor:
        # actors se guarda como JSON (texto en SQLite); buscamos el id citado.
        conds.append(cast(Mention.actors, String).like(f'%"{f.actor}"%'))
    if f.q:
        conds.append(Mention.text.ilike(f"%{f.q}%"))
    return conds


def filtered_select(f: Filters):
    stmt = select(Mention)
    conds = _conditions(f)
    if conds:
        stmt = stmt.where(*conds)
    return stmt


def _net_sentiment(positive: int, negative: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((positive - negative) / total * 100, 1)


def get_summary(db: Session, f: Filters) -> Summary:
    rows = db.scalars(filtered_select(f)).all()
    total = len(rows)
    breakdown = SentimentBreakdown()
    topic_counts: dict[str, int] = defaultdict(int)
    authors: set[str] = set()
    sources: set[str] = set()
    score_sum = 0.0
    reach = 0
    engagement = 0
    pmin: datetime | None = None
    pmax: datetime | None = None

    for m in rows:
        setattr(breakdown, m.sentiment, getattr(breakdown, m.sentiment, 0) + 1)
        score_sum += m.sentiment_score
        reach += m.reach
        engagement += m.engagement
        sources.add(m.source)
        if m.author:
            authors.add(m.author)
        if m.topic:
            topic_counts[m.topic] += 1
        if pmin is None or m.published_at < pmin:
            pmin = m.published_at
        if pmax is None or m.published_at > pmax:
            pmax = m.published_at

    top_topic = max(topic_counts, key=topic_counts.get) if topic_counts else None
    return Summary(
        total_mentions=total,
        total_reach=reach,
        total_engagement=engagement,
        sentiment=breakdown,
        avg_sentiment_score=round(score_sum / total, 4) if total else 0.0,
        net_sentiment=_net_sentiment(breakdown.positive, breakdown.negative, total),
        unique_authors=len(authors),
        sources_count=len(sources),
        top_topic=top_topic,
        period_start=pmin,
        period_end=pmax,
    )


def get_timeline(db: Session, f: Filters) -> list[TimelinePoint]:
    rows = db.scalars(filtered_select(f)).all()
    buckets: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "positive": 0, "neutral": 0, "negative": 0}
    )
    for m in rows:
        day = m.published_at.strftime("%Y-%m-%d")
        buckets[day]["total"] += 1
        buckets[day][m.sentiment] += 1

    points = []
    for day in sorted(buckets):
        b = buckets[day]
        points.append(
            TimelinePoint(
                date=day,
                total=b["total"],
                positive=b["positive"],
                neutral=b["neutral"],
                negative=b["negative"],
                net_sentiment=_net_sentiment(b["positive"], b["negative"], b["total"]),
            )
        )
    return points


def get_topics(db: Session, f: Filters) -> list[TopicStat]:
    config = get_election_config()
    rows = db.scalars(filtered_select(f)).all()
    agg: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "positive": 0, "neutral": 0, "negative": 0, "score": 0.0}
    )
    for m in rows:
        if not m.topic:
            continue
        a = agg[m.topic]
        a["count"] += 1
        a[m.sentiment] += 1
        a["score"] += m.sentiment_score

    stats = []
    for topic_id, a in agg.items():
        topic = config.topic_by_id(topic_id)
        stats.append(
            TopicStat(
                id=topic_id,
                name=topic.name if topic else topic_id,
                count=a["count"],
                positive=a["positive"],
                neutral=a["neutral"],
                negative=a["negative"],
                net_sentiment=_net_sentiment(a["positive"], a["negative"], a["count"]),
                avg_score=round(a["score"] / a["count"], 4) if a["count"] else 0.0,
            )
        )
    return sorted(stats, key=lambda s: s.count, reverse=True)


def get_sources(db: Session, f: Filters) -> list[SourceStat]:
    config = get_election_config()
    rows = db.scalars(filtered_select(f)).all()
    agg: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "positive": 0, "neutral": 0, "negative": 0}
    )
    for m in rows:
        a = agg[m.source]
        a["count"] += 1
        a[m.sentiment] += 1

    stats = []
    for source, a in agg.items():
        src_cfg = config.sources.get(source)
        stats.append(
            SourceStat(
                source=source,
                label=src_cfg.label if src_cfg and src_cfg.label else source,
                count=a["count"],
                positive=a["positive"],
                neutral=a["neutral"],
                negative=a["negative"],
                net_sentiment=_net_sentiment(a["positive"], a["negative"], a["count"]),
            )
        )
    return sorted(stats, key=lambda s: s.count, reverse=True)


def get_share_of_voice(db: Session, f: Filters) -> list[ShareOfVoiceItem]:
    config = get_election_config()
    rows = db.scalars(filtered_select(f)).all()
    agg: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "positive": 0, "neutral": 0, "negative": 0, "reach": 0}
    )
    total_actor_mentions = 0
    for m in rows:
        for actor_id in (m.actors or []):
            a = agg[actor_id]
            a["count"] += 1
            a[m.sentiment] += 1
            a["reach"] += m.reach
            total_actor_mentions += 1

    items = []
    for actor in config.actors:
        a = agg.get(actor.id, {"count": 0, "positive": 0, "neutral": 0, "negative": 0, "reach": 0})
        share = round(a["count"] / total_actor_mentions * 100, 1) if total_actor_mentions else 0.0
        items.append(
            ShareOfVoiceItem(
                actor_id=actor.id,
                name=actor.name,
                party=actor.party,
                color=actor.color,
                count=a["count"],
                share=share,
                positive=a["positive"],
                neutral=a["neutral"],
                negative=a["negative"],
                net_sentiment=_net_sentiment(a["positive"], a["negative"], a["count"]),
                total_reach=a["reach"],
            )
        )
    return sorted(items, key=lambda i: i.count, reverse=True)


def get_emotions(db: Session, f: Filters) -> list[EmotionStat]:
    rows = db.execute(
        filtered_select(f).with_only_columns(Mention.emotion, func.count())
        .where(Mention.emotion.is_not(None))
        .group_by(Mention.emotion)
    ).all()
    return [EmotionStat(emotion=e, count=c) for e, c in rows]
