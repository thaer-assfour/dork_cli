"""DuckDuckGo HTML provider. Free, for development and low-volume use.

DuckDuckGo supports a narrower set of operators than Google and rate-limits
aggressively, so treat this as the testing default, not the production one.
The HTML layout can change; parsing is best-effort.
"""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import SearchProvider, SearchResult

ENDPOINT = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _clean_url(href: str) -> str:
    # DDG wraps external links as /l/?uddg=<encoded>
    parsed = urlparse(href)
    if parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"
    cost_per_1k_usd = 0.0

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def search(self, query: str, num: int = 10) -> list[SearchResult]:
        resp = httpx.post(
            ENDPOINT,
            data={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[SearchResult] = []
        for i, node in enumerate(soup.select(".result"), start=1):
            if i > num:
                break
            link = node.select_one("a.result__a")
            if not link:
                continue
            snippet_node = node.select_one(".result__snippet")
            results.append(
                SearchResult(
                    title=link.get_text(strip=True),
                    url=_clean_url(link.get("href", "")),
                    snippet=snippet_node.get_text(strip=True) if snippet_node else "",
                    position=i,
                )
            )
        return results
