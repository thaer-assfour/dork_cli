"""Import dork templates from an external feed (URL or local file).

Accepts three shapes, auto-detected:
  - JSON: a list of strings, or a list of objects with a dork field
    (one of: template, dork, query, google_dork, ghdb_dork) and optionally
    category / risk / tags.
  - CSV: a header row; the dork column is auto-detected from the same names.
  - lines: one dork per line (blank lines and lines starting with # ignored).

Each imported template is normalized to use {target} and auto-categorized by
its operators when no category is supplied. This is the generic path for
pulling community dork lists such as the Google Hacking Database (GHDB).
"""

from __future__ import annotations

import csv
import io
import json
import re

import httpx

from ..db.models import Dork

_DORK_FIELDS = ("template", "dork", "query", "google_dork", "ghdb_dork", "q")
_SITE_RE = re.compile(r"\bsite:\s*\S+", re.IGNORECASE)

# operator -> category, checked in order
_CATEGORY_RULES = [
    (re.compile(r"\.env\b|ext:env|filename:\.?env|api[_-]?key|client_secret"
                r"|password|token", re.I), "secrets"),
    (re.compile(r"ext:(sql|db|sqlite|bak|old|swp)|filetype:(sql|bak)", re.I), "files"),
    (re.compile(r"inurl:(admin|login|dashboard)|phpmyadmin|grafana", re.I), "panels"),
    (re.compile(r"intitle:\"?index of", re.I), "exposure"),
    (re.compile(r"\.git\b|svn|gitlab", re.I), "vcs"),
    (re.compile(r"traceback|stack trace|sql syntax|warning:|fatal error", re.I),
     "errors"),
    (re.compile(r"s3\.amazonaws|blob\.core\.windows|storage\.googleapis", re.I),
     "cloud"),
    (re.compile(r"ext:(yaml|yml|ini|conf|cfg)|filetype:(conf|ini)", re.I),
     "config"),
]


def categorize(template: str) -> str:
    for rule, cat in _CATEGORY_RULES:
        if rule.search(template):
            return cat
    return "misc"


def normalize_template(raw: str) -> str:
    """Make a raw dork into a {target}-based template."""
    t = raw.strip()
    # Replace a concrete site:example.com with site:{target}
    if _SITE_RE.search(t):
        t = _SITE_RE.sub("site:{target}", t)
    elif "{target}" not in t:
        t = "site:{target} " + t
    return t


def _extract_from_obj(obj: dict) -> str | None:
    for key in _DORK_FIELDS:
        if key in obj and isinstance(obj[key], str) and obj[key].strip():
            return obj[key]
    return None


def _parse_json(text: str) -> list[dict]:
    data = json.loads(text)
    if isinstance(data, dict):
        # common wrappers
        for key in ("data", "dorks", "results", "entries"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            data = [data]
    out = []
    for item in data:
        if isinstance(item, str):
            out.append({"raw": item})
        elif isinstance(item, dict):
            raw = _extract_from_obj(item)
            if raw:
                out.append({
                    "raw": raw,
                    "category": item.get("category"),
                    "risk": item.get("risk"),
                    "tags": item.get("tags"),
                })
    return out


def _parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    out = []
    for row in reader:
        lower = {(k or "").strip().lower(): v for k, v in row.items()}
        raw = next((lower[f] for f in _DORK_FIELDS if lower.get(f)), None)
        if raw:
            out.append({
                "raw": raw,
                "category": lower.get("category"),
                "risk": lower.get("risk"),
                "tags": lower.get("tags"),
            })
    return out


def _parse_lines(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append({"raw": line})
    return out


def parse_feed(text: str, fmt: str = "auto") -> list[dict]:
    text = text.strip()
    if fmt == "auto":
        if text[:1] in "[{":
            fmt = "json"
        elif "," in text.splitlines()[0] and any(
            f in text.splitlines()[0].lower() for f in _DORK_FIELDS
        ):
            fmt = "csv"
        else:
            fmt = "lines"
    if fmt == "json":
        return _parse_json(text)
    if fmt == "csv":
        return _parse_csv(text)
    return _parse_lines(text)


def load_text(source: str, timeout: float = 30.0) -> str:
    """Fetch the feed text from a URL or read it from a local file."""
    if source.startswith(("http://", "https://")):
        resp = httpx.get(source, timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "dork-cli/0.1"})
        resp.raise_for_status()
        return resp.text
    from pathlib import Path
    return Path(source).read_text(encoding="utf-8")


def feed_to_dorks(entries: list[dict], source_label: str,
                  default_risk: str = "medium") -> list[Dork]:
    dorks: list[Dork] = []
    for e in entries:
        template = normalize_template(e["raw"])
        dorks.append(Dork(
            template=template,
            category=e.get("category") or categorize(template),
            risk=e.get("risk") or default_risk,
            tags=e.get("tags"),
            source=source_label,
        ))
    return dorks
