"""Endpoint del feed de menciones (paginado)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_filters
from ..models import Mention
from ..queries import Filters, filtered_select
from ..schemas import MentionOut, MentionsPage

router = APIRouter(prefix="/api", tags=["mentions"])


@router.get("/mentions", response_model=MentionsPage)
def list_mentions(
    f: Filters = Depends(get_filters),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: str = Query("recent", pattern="^(recent|engagement|reach)$"),
    db: Session = Depends(get_db),
):
    base = filtered_select(f)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    order = {
        "recent": Mention.published_at.desc(),
        "engagement": Mention.engagement.desc(),
        "reach": Mention.reach.desc(),
    }[sort]

    items = db.scalars(base.order_by(order).limit(limit).offset(offset)).all()
    return MentionsPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[MentionOut.model_validate(m) for m in items],
    )
