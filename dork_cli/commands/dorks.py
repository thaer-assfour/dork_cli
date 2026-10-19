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
