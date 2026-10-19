"""Simple delay-based rate limiter between queries."""

from __future__ import annotations

import time


class RateLimiter:
    def __init__(self, delay_seconds: float):
        self.delay = max(0.0, delay_seconds)
        self._last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            elapsed = time.monotonic() - self._last
            remaining = self.delay - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last = time.monotonic()
