"""Serper.dev search provider (Google results as JSON). Production default."""

from __future__ import annotations

import httpx

from .base import SearchProvider, SearchResult

ENDPOINT = "https://google.serper.dev/search"


class SerperProvider(SearchProvider):
    name = "serper"
    cost_per_1k_usd = 1.0  # starter pack rate; confirm in your account

    def __init__(self, api_key: str, timeout: float = 20.0):
        if not api_key:
            raise ValueError(
                "SERPER_API_KEY is not set. Put it in .env or switch "
                "DORK_PROVIDER=duckduckgo."
            )
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, num: int = 10) -> list[SearchResult]:
        resp = httpx.post(
            ENDPOINT,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        results: list[SearchResult] = []
        for i, item in enumerate(data.get("organic", []), start=1):
            results.append(
                SearchResult(
                    title=item.get("title", "") or "",
                    url=item.get("link", "") or "",
                    snippet=item.get("snippet", "") or "",
                    position=item.get("position", i),
                )
            )
        return results
