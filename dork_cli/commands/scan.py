"""Command 3: match selected targets against enabled dorks and store hits."""

from __future__ import annotations

import typer
from rich.progress import Progress

from ..config import get_config
from ..db.database import Database
from ..db.models import Result
from ..providers.registry import get_provider
from ..core import cache
from ..core.cost import estimate
from ..core.query_builder import ScopeError, build_query
from ..core.rate_limiter import RateLimiter
from ..core.scope import effective_scope, is_in_scope
from ..utils.console import console, results_table

app = typer.Typer(help="Run dorks against selected targets.")


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    provider: str = typer.Option(None, "--provider", "-p",
                                 help="Override the configured provider."),
    num: int = typer.Option(10, "--num", "-n", help="Results per query."),
    category: str = typer.Option(None, "--category", "-c",
                                 help="Only use dorks in this category."),
    yes: bool = typer.Option(False, "--yes", "-y",
                             help="Skip the cost confirmation prompt."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore the query cache."),
    note: str = typer.Option(None, "--note", help="Label this scan."),
):
    """Scan: selected targets x enabled dorks, within authorized scope."""
    if ctx.invoked_subcommand is not None:
        return
    cfg = get_config()
    prov_name = (provider or cfg.provider).lower()

    with Database(cfg.db_path) as db:
        targets = db.list_targets(selected_only=True)
        dorks = db.list_dorks(enabled_only=True, category=category)

        if not targets:
            console.print("[red]No selected targets. Use 'dork targets select'.[/red]")
            raise typer.Exit(1)
        if not dorks:
            console.print("[red]No enabled dorks. Import or add some first.[/red]")
            raise typer.Exit(1)

        est = estimate(len(targets), len(dorks), prov_name)
        console.print(
            f"[cyan]Plan:[/cyan] {len(targets)} target(s) x {len(dorks)} dork(s) "
            f"=> {est.describe()}"
        )
        if not yes and not typer.confirm("Proceed?", default=False):
            raise typer.Abort()

        search = get_provider(cfg, override=prov_name)
        limiter = RateLimiter(cfg.rate_delay)
        scan_id = db.create_scan(prov_name, note=note)
        executed = 0
        hits = 0
        skipped_scope = 0

        with Progress() as progress:
            task = progress.add_task(
                "scanning", total=len(targets) * len(dorks)
            )
            for t in targets:
                scope = effective_scope(t.domain, t.scope)
                for d in dorks:
                    progress.advance(task)
                    try:
                        query = build_query(t.domain, d.template)
                    except ScopeError:
                        skipped_scope += 1
                        continue
                    # Scope guard: never query a host outside authorization.
                    if not is_in_scope(t.domain, scope):
                        skipped_scope += 1
                        continue

                    results = None
                    if not no_cache:
                        results = cache.get_cached(
                            db, prov_name, query, num, cfg.cache_ttl_hours
                        )
                    if results is None:
                        limiter.wait()
                        try:
                            results = search.search(query, num=num)
                        except Exception as exc:  # provider/network failure
                            console.print(f"[red]query failed[/red] {query}: {exc}")
                            continue
                        cache.put_cached(db, prov_name, query, num, results)
                    executed += 1

                    for res in results:
                        db.add_result(Result(
                            scan_id=scan_id,
                            target_id=t.id,
                            dork_id=d.id,
                            query=query,
                            url=res.url,
                            title=res.title,
                            snippet=res.snippet,
                            position=res.position,
                        ))
                        hits += 1

        db.finish_scan(scan_id, query_count=executed)
        console.print(
            f"[green]Scan #{scan_id} done.[/green] "
            f"queries={executed} hits={hits} skipped_out_of_scope={skipped_scope}"
        )
        rows = db.results_for_scan(scan_id)
        if rows:
            console.print(results_table(rows))
        console.print(
            f"Ask Claude in-session to triage scan #{scan_id} "
            f"(see docs/CLAUDE.md)."
        )
