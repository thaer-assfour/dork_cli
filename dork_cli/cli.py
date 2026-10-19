"""dork-cli entry point. Wires the four independent commands."""

from __future__ import annotations

import typer

from . import __version__
from .commands import dorks, scan, targets, triage

app = typer.Typer(
    name="dork",
    help="Dork-based recon orchestrator for authorized bug bounty programs.",
    no_args_is_help=True,
)

app.add_typer(targets.app, name="targets")
app.add_typer(dorks.app, name="dorks")
app.add_typer(scan.app, name="scan")
app.add_typer(triage.app, name="triage")


@app.command()
def version():
    """Print the version."""
    typer.echo(f"dork-cli {__version__}")


if __name__ == "__main__":
    app()
