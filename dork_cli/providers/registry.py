"""Resolve a provider name to a configured provider instance."""

from __future__ import annotations

from ..config import Config
from .base import SearchProvider
from .duckduckgo import DuckDuckGoProvider
from .serper import SerperProvider

_PROVIDERS = {
    DuckDuckGoProvider.name: DuckDuckGoProvider,
    SerperProvider.name: SerperProvider,
}


def available_providers() -> list[str]:
    return sorted(_PROVIDERS)


def get_provider(cfg: Config, override: str | None = None) -> SearchProvider:
    name = (override or cfg.provider).strip().lower()
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(available_providers())}"
        )
    if name == SerperProvider.name:
        # Queries Serper's free tier refuses (intext:/allintext:) are routed
        # to DuckDuckGo instead of failing the dork.
        return SerperProvider(
            api_key=cfg.serper_api_key or "",
            fallback=DuckDuckGoProvider(),
        )
    return DuckDuckGoProvider()
