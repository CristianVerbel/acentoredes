"""Conector de X / Twitter (API v2, requiere TWITTER_BEARER_TOKEN).

Sin token el conector queda "no disponible" y la ingesta lo omite; la demo
funciona con los datos sembrados. Con token, consulta busquedas recientes.
"""
from __future__ import annotations

from datetime import datetime

import httpx
from dateutil import parser as date_parser

from .base import BaseConnector, RawMention

SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


class TwitterConnector(BaseConnector):
    source = "twitter"

    @property
    def available(self) -> bool:
        cfg = self.config.sources.get("twitter")
        return bool(cfg and cfg.enabled and self.settings.twitter_bearer_token)

    def fetch(self, limit: int = 100) -> list[RawMention]:
        cfg = self.config.sources.get("twitter")
        if not cfg or not self.settings.twitter_bearer_token:
            return []

        query = " OR ".join(cfg.query_terms) if cfg.query_terms else "elecciones"
        query = f"({query}) lang:es -is:retweet"
        headers = {"Authorization": f"Bearer {self.settings.twitter_bearer_token}"}
        params = {
            "query": query,
            "max_results": min(100, max(10, limit)),
            "tweet.fields": "created_at,public_metrics,lang",
            "expansions": "author_id",
            "user.fields": "username",
        }
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(SEARCH_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []

        users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
        results: list[RawMention] = []
        for tweet in data.get("data", []):
            metrics = tweet.get("public_metrics", {})
            engagement = (
                metrics.get("like_count", 0)
                + metrics.get("retweet_count", 0)
                + metrics.get("reply_count", 0)
            )
            results.append(
                RawMention(
                    source=self.source,
                    external_id=tweet["id"],
                    author=users.get(tweet.get("author_id"), None),
                    text=tweet.get("text", ""),
                    url=f"https://x.com/i/web/status/{tweet['id']}",
                    lang=tweet.get("lang", "es"),
                    published_at=self._parse_date(tweet.get("created_at")),
                    engagement=engagement,
                    reach=metrics.get("impression_count", engagement * 20),
                )
            )
        return results

    @staticmethod
    def _parse_date(value: str | None) -> datetime:
        if not value:
            return datetime.utcnow()
        try:
            return date_parser.parse(value).replace(tzinfo=None)
        except Exception:
            return datetime.utcnow()
