"""Serper.dev search provider (Google results as JSON). Production default."""

from __future__ import annotations

import httpx

from .base import SearchProvider, SearchResult

ENDPOINT = "https://google.serper.dev/search"

# Serper's free tier rejects queries containing the intext:/allintext:
# operators with HTTP 400 ("Query pattern not allowed for free accounts").
# Such a rejected query is retried on the fallback provider (DuckDuckGo)
# instead of failing the dork outright.
_FREE_TIER_MSG = "not allowed for free accounts"


class SerperProvider(SearchProvider):
    name = "serper"
    cost_per_1k_usd = 1.0  # starter pack rate; confirm in your account

    def __init__(
        self,
        api_key: str,
        timeout: float = 20.0,
        fallback: SearchProvider | None = None,
    ):
        if not api_key:
            raise ValueError(
                "SERPER_API_KEY is not set. Put it in .env or switch "
                "DORK_PROVIDER=duckduckgo."
            )
        self.api_key = api_key
        self.timeout = timeout
        #: provider used for queries Serper's free tier refuses (e.g. intext:)
        self.fallback = fallback

    def _post(self, query: str, num: int) -> httpx.Response:
        return httpx.post(
            ENDPOINT,
            headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=self.timeout,
        )

    def search(self, query: str, num: int = 10) -> list[SearchResult]:
        resp = self._post(query, num)
        # Free-tier accounts reject intext:/allintext:. Route the rejected
        # query to the fallback provider (DuckDuckGo) rather than failing.
        if (
            resp.status_code == 400
            and _FREE_TIER_MSG in resp.text.lower()
            and self.fallback is not None
        ):
            return self.fallback.search(query, num)
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
