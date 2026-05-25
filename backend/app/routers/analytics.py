"""Endpoints analiticos del monitor."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import queries
from ..database import get_db
from ..deps import get_filters
from ..queries import Filters
from ..schemas import (
    EmotionStat,
    ShareOfVoiceItem,
    SourceStat,
    Summary,
    TimelinePoint,
    TopicStat,
)

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/summary", response_model=Summary)
def summary(f: Filters = Depends(get_filters), db: Session = Depends(get_db)):
    return queries.get_summary(db, f)


@router.get("/timeline", response_model=list[TimelinePoint])
def timeline(f: Filters = Depends(get_filters), db: Session = Depends(get_db)):
    return queries.get_timeline(db, f)


@router.get("/topics", response_model=list[TopicStat])
def topics(f: Filters = Depends(get_filters), db: Session = Depends(get_db)):
    return queries.get_topics(db, f)


@router.get("/sources", response_model=list[SourceStat])
def sources(f: Filters = Depends(get_filters), db: Session = Depends(get_db)):
    return queries.get_sources(db, f)


@router.get("/share-of-voice", response_model=list[ShareOfVoiceItem])
def share_of_voice(f: Filters = Depends(get_filters), db: Session = Depends(get_db)):
    return queries.get_share_of_voice(db, f)


@router.get("/emotions", response_model=list[EmotionStat])
def emotions(f: Filters = Depends(get_filters), db: Session = Depends(get_db)):
    return queries.get_emotions(db, f)
