"""Typed row models for the database tables."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class Target:
    domain: str
    name: str | None = None
    source: str | None = None
    scope: list[str] = field(default_factory=list)
    program_url: str | None = None
    security_txt: str | None = None
    status: str = "new"
    selected: bool = False
    id: int | None = None

    @property
    def scope_json(self) -> str:
        return json.dumps(self.scope)

    @classmethod
    def from_row(cls, row) -> "Target":
        return cls(
            id=row["id"],
            domain=row["domain"],
            name=row["name"],
            source=row["source"],
            scope=json.loads(row["scope_json"]) if row["scope_json"] else [],
            program_url=row["program_url"],
            security_txt=row["security_txt"],
            status=row["status"],
            selected=bool(row["selected"]),
        )


@dataclass
class Dork:
    template: str
    category: str | None = None
    risk: str = "medium"
    tags: str | None = None
    source: str | None = None
    enabled: bool = True
    id: int | None = None

    @classmethod
    def from_row(cls, row) -> "Dork":
        return cls(
            id=row["id"],
            template=row["template"],
            category=row["category"],
            risk=row["risk"],
            tags=row["tags"],
            source=row["source"],
            enabled=bool(row["enabled"]),
        )


@dataclass
class Result:
    scan_id: int
    target_id: int
    dork_id: int
    query: str
    url: str | None = None
    title: str | None = None
    snippet: str | None = None
    position: int | None = None
    http_status: int | None = None
    id: int | None = None
