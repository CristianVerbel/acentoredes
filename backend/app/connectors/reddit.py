"""Conector de Reddit usando los endpoints JSON publicos (sin OAuth).

Para volumen alto o uso continuo conviene usar la API oficial con credenciales
(REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET), pero el endpoint .json publico
permite una demo funcional.
"""
from __future__ import annotations

from datetime import datetime

import httpx

from .base import BaseConnector, RawMention

USER_AGENT = "acentoredes-monitor/0.1 (escucha digital electoral)"


class RedditConnector(BaseConnector):
    source = "reddit"

    @property
    def available(self) -> bool:
        cfg = self.config.sources.get("reddit")
        return bool(cfg and cfg.enabled and cfg.subreddits)

    def fetch(self, limit: int = 100) -> list[RawMention]:
        cfg = self.config.sources.get("reddit")
        if not cfg:
            return []

        results: list[RawMention] = []
        per_sub = max(1, limit // max(1, len(cfg.subreddits)))
        with httpx.Client(timeout=15, headers={"User-Agent": USER_AGENT}) as client:
            for sub in cfg.subreddits:
                try:
                    resp = client.get(
                        f"https://www.reddit.com/r/{sub}/new.json",
                        params={"limit": per_sub},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception:
                    continue
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    text = (post.get("title", "") + ". " + post.get("selftext", "")).strip()
                    if not text:
                        continue
                    results.append(
                        RawMention(
                            source=self.source,
                            external_id=post.get("name"),
                            author=post.get("author"),
                            text=text[:5000],
                            url="https://reddit.com" + post.get("permalink", ""),
                            published_at=datetime.utcfromtimestamp(post.get("created_utc", 0)),
                            engagement=int(post.get("ups", 0)) + int(post.get("num_comments", 0)),
                            reach=int(post.get("ups", 0)) * 10,
                        )
                    )
        return results[:limit]
