"""Shared rich console and small table helpers."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def targets_table(targets) -> Table:
    t = Table(title="Targets")
    t.add_column("ID", justify="right")
    t.add_column("Sel", justify="center")
    t.add_column("Domain")
    t.add_column("Name")
    t.add_column("Source")
    t.add_column("Program")
    for tg in targets:
        t.add_row(
            str(tg.id or "-"),
            "[green]x[/green]" if tg.selected else "",
            tg.domain,
            tg.name or "",
            tg.source or "",
            tg.program_url or "",
        )
    return t


def dorks_table(dorks) -> Table:
    t = Table(title="Dorks")
    t.add_column("ID", justify="right")
    t.add_column("On", justify="center")
    t.add_column("Category")
    t.add_column("Risk")
    t.add_column("Template")
    for d in dorks:
        t.add_row(
            str(d.id or "-"),
            "[green]x[/green]" if d.enabled else "",
            d.category or "",
            d.risk or "",
            d.template,
        )
    return t


def results_table(rows) -> Table:
    t = Table(title="Results")
    t.add_column("ID", justify="right")
    t.add_column("Target")
    t.add_column("Category")
    t.add_column("Title")
    t.add_column("URL")
    for r in rows:
        t.add_row(
            str(r["id"]),
            r["target_domain"],
            r["dork_category"] or "",
            (r["title"] or "")[:50],
            (r["url"] or "")[:70],
        )
    return t
