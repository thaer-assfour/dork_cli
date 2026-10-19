"""Runtime configuration, loaded from environment / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the current working directory if present. Never commit .env.
load_dotenv()


@dataclass(frozen=True)
class Config:
    provider: str
    serper_api_key: str | None
    db_path: Path
    rate_delay: float
    cache_ttl_hours: int

    @classmethod
    def load(cls) -> "Config":
        return cls(
            provider=os.getenv("DORK_PROVIDER", "duckduckgo").strip().lower(),
            serper_api_key=(os.getenv("SERPER_API_KEY") or "").strip() or None,
            db_path=Path(os.getenv("DORK_DB", "./dork.db")).expanduser(),
            rate_delay=float(os.getenv("DORK_RATE_DELAY", "2.0")),
            cache_ttl_hours=int(os.getenv("DORK_CACHE_TTL_HOURS", "72")),
        )


def get_config() -> Config:
    return Config.load()
