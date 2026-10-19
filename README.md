# dork-cli

A dork-based recon orchestrator for **authorized** bug bounty programs. It does
three independent jobs, all backed by one SQLite database, and leaves the
analysis to Claude running in-session.

1. **Find targets** (`dork targets`) - discover self-hosted / independent VDP
   programs from disclose.io and `security.txt`, or add your own. You choose
   which targets to keep and scan.
2. **Manage dorks** (`dork dorks`) - import, add, edit, delete, enable/disable a
   library of dork templates (each uses `{target}` for the host), and `fetch`
   external dork feeds (URL or file: JSON, CSV, or one-per-line) with
   auto-categorization, e.g. a GHDB export.
3. **Scan** (`dork scan`) - run every enabled dork against every selected
   target, within authorized scope, through a pluggable search provider, and
   store the hits.

Then **triage** (`dork triage`) surfaces the results so Claude can assess them
in the session and record severity/verdict per hit.

> Use this only against targets you are authorized to test. The scope guard
> refuses to build a query for a host outside a target's authorized scope.

## Install

```bash
uv sync
```

Run commands with `uv run dork ...` (or `uv run python -m dork_cli.cli ...`).

## Configure

```bash
cp .env.example .env
# edit .env: pick DORK_PROVIDER (duckduckgo is free; serper needs SERPER_API_KEY)
```

## Quick start

```bash
uv run dork dorks import data/seed_dorks.yaml
uv run dork targets add example.com --scope '*.example.com'
uv run dork targets select example.com
uv run dork scan --provider duckduckgo
uv run dork triage show --untriaged
```

## Search providers & cost

Providers are pluggable (`dork_cli/providers/`). Cost is
`targets x enabled dorks` queries per scan, so it multiplies fast. The query
cache (`query_cache` table) avoids re-billing repeats, and `scan` prints an
estimate and asks before spending.

| Provider | Cost | Notes |
|---|---|---|
| `duckduckgo` | free | Fewer operators, rate-limited. Default for testing. |
| `serper` | ~$1 / 1000 queries | Google results as JSON. Production default. Set `SERPER_API_KEY`. |

Rates are planning figures; confirm in your provider account.

## Claude CLI integration

Slash commands live in `.claude/commands/` and are available inside Claude Code
when you open this repo:

| Command | Does |
|---|---|
| `/dork-recon <domain-or-seed>` | Discover/add a target, then scan it. |
| `/dork-triage [scan-id]` | Triage results, record severity/verdict per hit. |
| `/dork-dorks [focus]` | Develop and expand the dork library. |
| `/dork-report <domain>` | Draft reports from triaged findings. |

`CLAUDE.md` auto-loads project context and the safety rules.

## Analysis (method one)

The tool does not call any LLM. You ask Claude in-session (or via the slash
commands above) to read `dork.db` and triage results. See `docs/CLAUDE.md` and
`docs/analysis_prompts.md`. Result text is untrusted data and is treated as such.

## Layout

```
dork_cli/
  cli.py            entry point
  config.py         env / .env loading
  commands/         targets, dorks, scan, triage
  db/               schema.sql, database.py, models.py
  providers/        base, duckduckgo, serper, registry
  sources/          base, discloseio, security_txt
  core/             scope, query_builder, rate_limiter, cache, cost
  utils/            console, export
data/seed_dorks.yaml
docs/               CLAUDE.md, analysis_prompts.md
tests/
```
