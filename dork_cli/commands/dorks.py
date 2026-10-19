"""Command 2: collect, update, and develop the dork library."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

from ..config import get_config
from ..db.database import Database
from ..db.models import Dork
from ..utils.console import console, dorks_table

app = typer.Typer(help="Manage the dork library (templates use {target}).")


@app.command("import")
def import_seed(
    path: Path = typer.Argument(
        Path("data/seed_dorks.yaml"),
        help="YAML file with a list of dork entries.",
    ),
):
    """Import dork templates from a YAML seed file."""
    cfg = get_config()
    if not path.exists():
        raise typer.BadParameter(f"File not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    entries = data.get("dorks", data) if isinstance(data, dict) else data
    count = 0
    with Database(cfg.db_path) as db:
        for e in entries:
            if isinstance(e, str):
                e = {"template": e}
            db.add_dork(
                Dork(
                    template=e["template"],
                    category=e.get("category"),
                    risk=e.get("risk", "medium"),
                    tags=e.get("tags"),
                    source="seed",
                )
            )
            count += 1
    console.print(f"[green]Imported {count} dork(s).[/green]")


@app.command("add")
def add(
    template: str = typer.Argument(..., help="Dork template, use {target} for host."),
    category: str = typer.Option(None, "--category", "-c"),
    risk: str = typer.Option("medium", "--risk", "-r"),
    tags: str = typer.Option(None, "--tags"),
):
    """Add a single dork template."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        db.add_dork(Dork(template=template, category=category, risk=risk,
                         tags=tags, source="manual"))
    console.print(f"[green]Added:[/green] {template}")


@app.command("list")
def list_dorks(
    enabled: bool = typer.Option(False, "--enabled", help="Only enabled dorks."),
    category: str = typer.Option(None, "--category", "-c"),
):
    """List dorks in the library."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        rows = db.list_dorks(enabled_only=enabled, category=category)
    console.print(dorks_table(rows))


@app.command()
def edit(
    dork_id: int = typer.Argument(..., help="Dork ID to modify."),
    template: str = typer.Option(None, "--template", "-t",
                                 help="New template (use {target})."),
    category: str = typer.Option(None, "--category", "-c"),
    risk: str = typer.Option(None, "--risk", "-r"),
    tags: str = typer.Option(None, "--tags"),
):
    """Edit an existing dork in place. Only the options you pass change."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        current = db.get_dork(dork_id)
        if not current:
            console.print(f"[red]dork {dork_id} not found[/red]")
            raise typer.Exit(1)
        n = db.update_dork(dork_id, template=template, category=category,
                           risk=risk, tags=tags)
        if not n:
            console.print("[yellow]nothing to change (no options given)[/yellow]")
            raise typer.Exit()
        updated = db.get_dork(dork_id)
    console.print(f"[green]updated dork {dork_id}[/green]")
    console.print(dorks_table([updated]))


@app.command()
def delete(
    dork_id: int = typer.Argument(..., help="Dork ID to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
):
    """Delete a dork. This also removes its stored results (cascade)."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        current = db.get_dork(dork_id)
        if not current:
            console.print(f"[red]dork {dork_id} not found[/red]")
            raise typer.Exit(1)
        console.print(dorks_table([current]))
        if not yes and not typer.confirm(
            "Delete this dork and its results?", default=False
        ):
            raise typer.Abort()
        db.delete_dork(dork_id)
    console.print(f"[green]deleted dork {dork_id}[/green]")


@app.command()
def fetch(
    source: str = typer.Argument(
        ..., help="URL or local file of a dork feed (JSON / CSV / one-per-line)."
    ),
    fmt: str = typer.Option("auto", "--format", "-f",
                            help="auto | json | csv | lines"),
    risk: str = typer.Option("medium", "--risk", "-r",
                             help="Default risk when the feed has none."),
    label: str = typer.Option(None, "--label",
                              help="Source label stored on each dork."),
    dry_run: bool = typer.Option(False, "--dry-run",
                                 help="Show what would be imported, save nothing."),
):
    """Fetch and import dorks from an external feed (e.g. a GHDB export).

    Templates are normalized to use {target} and auto-categorized by their
    operators when the feed gives no category.
    """
    from ..sources import dork_feeds

    cfg = get_config()
    try:
        text = dork_feeds.load_text(source)
    except Exception as exc:
        console.print(f"[red]could not load feed:[/red] {exc}")
        raise typer.Exit(1)

    entries = dork_feeds.parse_feed(text, fmt=fmt)
    if not entries:
        console.print("[yellow]no dorks parsed from feed[/yellow]")
        raise typer.Exit()

    label = label or source
    dorks = dork_feeds.feed_to_dorks(entries, source_label=label, default_risk=risk)
    console.print(f"[cyan]parsed {len(dorks)} dork(s) from {source}[/cyan]")
    console.print(dorks_table(dorks[:20]))
    if len(dorks) > 20:
        console.print(f"... and {len(dorks) - 20} more")

    if dry_run:
        console.print("[yellow]dry run: nothing saved[/yellow]")
        raise typer.Exit()

    with Database(cfg.db_path) as db:
        for d in dorks:
            db.add_dork(d)
    console.print(f"[green]imported {len(dorks)} dork(s).[/green]")


@app.command()
def ghdb(
    category: str = typer.Option(
        None, "--category", "-c",
        help="Only import a GHDB category (exact cat_title, e.g. "
             "'Files Containing Passwords').",
    ),
    limit: int = typer.Option(None, "--limit", "-l",
                              help="Import at most this many dorks."),
    url: str = typer.Option(None, "--url", help="Override the GHDB endpoint."),
    insecure: bool = typer.Option(
        False, "--insecure",
        help="Skip TLS verification (fallback if the cert chain fails).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run",
                                 help="Show what would be imported, save nothing."),
):
    """Import dorks straight from the Exploit-DB Google Hacking Database.

    Fetches the GHDB JSON, extracts each dork, maps its GHDB category to an
    internal one (keeping the GHDB title as a tag), and normalizes it to a
    {target}-based template.
    """
    from ..sources import ghdb as ghdb_src

    cfg = get_config()
    endpoint = url or ghdb_src.GHDB_URL
    console.print(f"[cyan]Fetching GHDB from {endpoint} ...[/cyan]")
    try:
        dorks = ghdb_src.load_ghdb_dorks(
            url=endpoint, verify=not insecure,
            category_filter=category, limit=limit,
        )
    except Exception as exc:
        console.print(f"[red]GHDB fetch failed:[/red] {exc}")
        console.print(
            "If this host is blocked or the cert chain fails, try again from a "
            "network that can reach exploit-db.com, or pass --insecure."
        )
        raise typer.Exit(1)

    if not dorks:
        console.print("[yellow]no dorks parsed from GHDB[/yellow]")
        raise typer.Exit()

    console.print(f"[cyan]parsed {len(dorks)} GHDB dork(s)[/cyan]")
    console.print(dorks_table(dorks[:20]))
    if len(dorks) > 20:
        console.print(f"... and {len(dorks) - 20} more")

    if dry_run:
        console.print("[yellow]dry run: nothing saved[/yellow]")
        raise typer.Exit()

    with Database(cfg.db_path) as db:
        for d in dorks:
            db.add_dork(d)
    console.print(f"[green]imported {len(dorks)} GHDB dork(s).[/green]")


@app.command()
def enable(dork_id: int = typer.Argument(...)):
    """Enable a dork by ID."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        n = db.set_dork_enabled(dork_id, True)
    console.print(f"dork {dork_id}: {'enabled' if n else 'not found'}")


@app.command()
def disable(dork_id: int = typer.Argument(...)):
    """Disable a dork by ID."""
    cfg = get_config()
    with Database(cfg.db_path) as db:
        n = db.set_dork_enabled(dork_id, False)
    console.print(f"dork {dork_id}: {'disabled' if n else 'not found'}")
