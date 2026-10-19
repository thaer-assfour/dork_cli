"""Abstract target-source interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..db.models import Target


class TargetSource(ABC):
    #: short name recorded on discovered targets
    name: str = "base"

    @abstractmethod
    def discover(self, seed: str) -> list[Target]:
        """Return candidate targets related to the seed (domain / keyword)."""
        raise NotImplementedError
