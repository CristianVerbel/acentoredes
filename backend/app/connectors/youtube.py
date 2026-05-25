"""Conector de YouTube (Data API v3, requiere YOUTUBE_API_KEY).

Busca videos por terminos y los registra como menciones. Sin API key el
conector queda "no disponible". (TikTok e Instagram comparten este patron:
requieren credenciales/partners y se habilitan analogamente.)
"""
from __future__ import annotations

from datetime import datetime

import httpx
from dateutil import parser as date_parser

from .base import BaseConnector, RawMention

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


class YouTubeConnector(BaseConnector):
    source = "youtube"

    @property
    def available(self) -> bool:
        cfg = self.config.sources.get("youtube")
        return bool(cfg and cfg.enabled and self.settings.youtube_api_key)

    def fetch(self, limit: int = 50) -> list[RawMention]:
        cfg = self.config.sources.get("youtube")
        if not cfg or not self.settings.youtube_api_key:
            return []

        query = " ".join(cfg.query_terms) if cfg.query_terms else "elecciones"
        params = {
            "key": self.settings.youtube_api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": min(50, max(1, limit)),
            "relevanceLanguage": "es",
            "order": "date",
        }
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []

        results: list[RawMention] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId")
            text = (snippet.get("title", "") + ". " + snippet.get("description", "")).strip()
            if not text or not video_id:
                continue
            results.append(
                RawMention(
                    source=self.source,
                    external_id=video_id,
                    author=snippet.get("channelTitle"),
                    text=text,
                    url=f"https://youtube.com/watch?v={video_id}",
                    published_at=self._parse_date(snippet.get("publishedAt")),
                    reach=10000,
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
