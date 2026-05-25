"""Conector de Noticias / RSS (gratuito, sin credenciales)."""
from __future__ import annotations

from datetime import datetime
from time import mktime

from .base import BaseConnector, RawMention


class NewsRSSConnector(BaseConnector):
    source = "news"

    @property
    def available(self) -> bool:
        cfg = self.config.sources.get("news")
        return bool(cfg and cfg.enabled and cfg.feeds)

    def fetch(self, limit: int = 100) -> list[RawMention]:
        import feedparser

        cfg = self.config.sources.get("news")
        if not cfg:
            return []

        results: list[RawMention] = []
        per_feed = max(1, limit // max(1, len(cfg.feeds)))
        for feed_url in cfg.feeds:
            try:
                parsed = feedparser.parse(feed_url)
            except Exception:
                continue
            for entry in parsed.entries[:per_feed]:
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or ""
                text = (title + ". " + summary).strip()
                if not text:
                    continue
                published = self._parse_date(entry)
                results.append(
                    RawMention(
                        source=self.source,
                        external_id=getattr(entry, "id", None) or getattr(entry, "link", None),
                        author=getattr(parsed.feed, "title", None),
                        text=text,
                        url=getattr(entry, "link", None),
                        published_at=published,
                        # El alcance de un medio se estima alto vs. un post individual.
                        reach=50000,
                        engagement=0,
                    )
                )
        return results[:limit]

    @staticmethod
    def _parse_date(entry) -> datetime:
        struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if struct:
            return datetime.fromtimestamp(mktime(struct))
        return datetime.utcnow()
