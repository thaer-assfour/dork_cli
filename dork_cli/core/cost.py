"""Pre-flight cost / volume estimate for a scan."""

from __future__ import annotations

from dataclasses import dataclass

# Rough per-1000-query USD rates. Confirm in your own provider account;
# these are planning figures only (see README).
RATES = {
    "duckduckgo": 0.0,
    "serper": 1.0,
}


@dataclass
class Estimate:
    queries: int
    provider: str
    usd: float

    def describe(self) -> str:
        if self.usd <= 0:
            return f"{self.queries} queries via {self.provider} (free tier)"
        return (
            f"{self.queries} queries via {self.provider}, "
            f"estimated ${self.usd:.2f}"
        )


def estimate(num_targets: int, num_dorks: int, provider: str) -> Estimate:
    queries = num_targets * num_dorks
    rate = RATES.get(provider, 0.0)
    return Estimate(queries=queries, provider=provider, usd=queries / 1000 * rate)
