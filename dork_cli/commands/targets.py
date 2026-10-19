"""Command 1: discover, list, and select bug bounty targets."""

from __future__ import annotations

import typer

from ..config import get_config
from ..db.database import Database
from ..db.models import Target
from ..sources.discloseio import DiscloseIoSource
from ..sources.security_txt import SecurityTxtSource
from ..core.scope import default_scope, normalize_host
from ..utils.console import console, targets_table

app = typer.Typer(help="Discover and manage bug bounty targets.")

_SOURCES = {
    "discloseio": DiscloseIoSource,
    "security_txt": SecurityTxtSource,
}


@app.command()
def discover(
    seed: str = typer.Argument(..., help="Domain or keyword to search by."),
    source: str = typer.Option(
        "discloseio", "--source", "-s",
        help=f"Discovery source: {', '.join(_SOURCES)}",
    ),
    save: bool = typer.Option(
        False, "--save", help="Save all discovered targets (status=new, unselected)."
    ),
):
    """Find candidate targets from a source and optionally store them."""
    if source not in _SOURCES:
        raise typer.BadParameter(f"Unknown source. Choose from: {', '.join(_SOURCES)}")
    cfg = get_config()
    src = _SOURCES[source]()
    console.print(f"[cyan]Discovering via {source} for seed:[/cyan] {seed}")
    found = src.discover(seed)
    if not found:
        console.print("[yellow]No candidates found.[/yellow]")
        raise typer.Exit()

    console.print(targets_table(found))
    console.print(f"[green]{len(found)} candidate(s).[/green]")
    if save:
        with Database(cfg.db_path) as db:
            for t in found:
                db.upsert_target(t)
        console.print(f"[green]Saved {len(found)} target(s) to the database.[/green]")
        console.print("Use 'dork targets select <domain>' to choose which to scan.")


@app.command("add")
def add_manual(
    domain: str = typer.Argument(..., help="Target host, e.g. example.com"),
    name: str = typer.Option(None, "--name"),
    scope: list[str] = typer.Option(
        None, "--scope",
        help="In-scope host pattern(s), e.g. '*.example.com'. Repeatable.",
    ),
    select: bool = typer.Option(True, "--select/--no-select"),
):
    """Add a target by hand (with explicit authorized scope)."""
    cfg = get_config()
    host = normalize_host(domain)
    t = Target(
        domain=host,
        name=name or host,
        source="manual",
        scope=list(scope) if scope else default_scope(host),
        selected=select,
    )
    with Database(cfg.db_path) as db:
        db.upsert_target(t)
    console.print(f"[green]Added[/green] {host} (scope: {', '.join(t.scope)})")


@app.command("list")
def list_targets(
    selected: bool = typer.Option(False, "--selected", help="Only selected targets."),
):
    """List stored targets."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        rows = db.list_targets(selected_only=selected)
    console.print(targets_table(rows))


@app.command()
def select(domain: str = typer.Argument(...)):
    """Mark a target as selected for scanning."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        n = db.set_selected(normalize_host(domain), True)
    msg = "[green]selected[/green]" if n else "[red]not found[/red]"
    console.print(f"{normalize_host(domain)}: {msg}")


@app.command()
def unselect(domain: str = typer.Argument(...)):
    """Unmark a target."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        n = db.set_selected(normalize_host(domain), False)
    msg = "[green]unselected[/green]" if n else "[red]not found[/red]"
    console.print(f"{normalize_host(domain)}: {msg}")
