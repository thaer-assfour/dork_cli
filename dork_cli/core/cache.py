"""SQLite-backed query cache to avoid re-billing the provider for repeats."""

from __future__ import annotations

import hashlib
import json

from ..db.database import Database
from ..providers.base import SearchResult


def cache_key(provider: str, query: str, num: int) -> str:
    raw = f"{provider}::{num}::{query}".encode()
    return hashlib.sha256(raw).hexdigest()


def get_cached(db: Database, provider: str, query: str, num: int,
               ttl_hours: int) -> list[SearchResult] | None:
    key = cache_key(provider, query, num)
    payload = db.cache_get(key, ttl_hours)
    if payload is None:
        return None
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return [SearchResult(**row) for row in rows]


def put_cached(db: Database, provider: str, query: str, num: int,
               results: list[SearchResult]) -> None:
    key = cache_key(provider, query, num)
    payload = json.dumps([r.to_dict() for r in results])
    db.cache_put(key, provider, query, payload)
