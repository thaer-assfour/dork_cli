"""Dedicated Exploit-DB Google Hacking Database (GHDB) source.

Exploit-DB serves the GHDB as JSON from its listing endpoint when requested
as an AJAX call. The response shape is:

    {
      "recordsTotal": <int>,
      "data": [
        {
          "url_title": "<a href=\"/ghdb/<id>\">the dork text</a>",
          "category": {"cat_id": "9", "cat_title": "Files Containing Passwords"},
          "date": "YYYY-MM-DD",
          ...
        },
        ...
      ]
    }

The dork text lives inside the `url_title` anchor, and the GHDB category is
authoritative. We extract the text, map the GHDB category onto this project's
internal categories, keep the original GHDB title as a tag, and normalize each
dork into a {target}-based template so scans stay scoped.

Network fetch and JSON parsing are separate so parsing is testable offline.
The dork text is third-party data; it is only ever used as a search template.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from ..db.models import Dork
from .dork_feeds import normalize_template, categorize

GHDB_URL = "https://www.exploit-db.com/google-hacking-database"

# A browser-like request; Exploit-DB gates the JSON behind the AJAX header.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": GHDB_URL,
}

# GHDB cat_title -> this project's internal category.
CATEGORY_MAP = {
    "Footholds": "exposure",
    "Files Containing Usernames": "secrets",
    "Sensitive Directories": "exposure",
    "Web Server Detection": "misc",
    "Vulnerable Files": "files",
    "Vulnerable Servers": "misc",
    "Error Messages": "errors",
    "Files Containing Juicy Info": "files",
    "Files Containing Password": "secrets",
    "Files Containing Passwords": "secrets",
    "Sensitive Online Shopping Info": "secrets",
    "Network or Vulnerability Data": "misc",
    "Pages Containing Login Portals": "panels",
    "Various Online Devices": "misc",
    "Advisories and Vulnerabilities": "misc",
}


def extract_dork(url_title: str) -> str:
    """Pull the plain dork text out of the GHDB url_title HTML anchor."""
    cleaned = (url_title or "").replace("\t", "")
    soup = BeautifulSoup(cleaned, "html.parser")
    link = soup.find("a")
    if link is not None:
        return link.get_text(strip=True)
    return soup.get_text(strip=True)


def _map_category(cat_title: str | None, template: str) -> str:
    if cat_title and cat_title in CATEGORY_MAP:
        return CATEGORY_MAP[cat_title]
    return categorize(template)


def parse_ghdb(payload: dict, category_filter: str | None = None,
               limit: int | None = None) -> list[Dork]:
    """Turn a GHDB JSON payload into Dork rows. Pure, no network."""
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    dorks: list[Dork] = []
    for entry in rows:
        raw = extract_dork(entry.get("url_title", ""))
        if not raw:
            continue
        cat_obj = entry.get("category") or {}
        cat_title = cat_obj.get("cat_title") if isinstance(cat_obj, dict) else None
        if category_filter and (cat_title or "").lower() != category_filter.lower():
            continue
        template = normalize_template(raw)
        dorks.append(Dork(
            template=template,
            category=_map_category(cat_title, template),
            risk="medium",
            tags=f"ghdb:{cat_title}" if cat_title else "ghdb",
            source="ghdb",
        ))
        if limit and len(dorks) >= limit:
            break
    return dorks


def fetch_ghdb(url: str = GHDB_URL, verify: bool = True,
               timeout: float = 30.0) -> dict:
    """Fetch the raw GHDB JSON payload from Exploit-DB."""
    resp = httpx.get(url, headers=HEADERS, timeout=timeout,
                     follow_redirects=True, verify=verify)
    resp.raise_for_status()
    return resp.json()


def load_ghdb_dorks(url: str = GHDB_URL, verify: bool = True,
                    category_filter: str | None = None,
                    limit: int | None = None,
                    timeout: float = 30.0) -> list[Dork]:
    payload = fetch_ghdb(url=url, verify=verify, timeout=timeout)
    return parse_ghdb(payload, category_filter=category_filter, limit=limit)
