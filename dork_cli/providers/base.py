"""Abstract search-provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    position: int

    def to_dict(self) -> dict:
        return asdict(self)


class SearchProvider(ABC):
    #: short name used in config / registry
    name: str = "base"
    #: rough cost in provider credits per 1000 queries, for cost estimates
    cost_per_1k_usd: float = 0.0

    @abstractmethod
    def search(self, query: str, num: int = 10) -> list[SearchResult]:
        """Run one query and return organic results. Raise on hard failure."""
        raise NotImplementedError
