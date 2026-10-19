---
description: Run the full dork recon pipeline for a target or seed (discover/add, scan, show results).
argument-hint: <domain-or-seed> [--scope '*.example.com'] [--provider duckduckgo|serper]
allowed-tools: Bash(uv run dork *), Bash(sqlite3 -readonly *)
---

You are driving the `dork` CLI in this repository for an **authorized** bug
bounty recon run. The argument is: `$ARGUMENTS`.

Do the following, confirming scope before any network call:

1. Decide whether the argument is a concrete domain or a keyword seed.
   - Domain: `uv run dork targets add <domain> --scope <scope-if-given>` then
     `uv run dork targets select <domain>`.
   - Keyword: `uv run dork targets discover "<seed>" --save`, show the table,
     and ask me which domains to `select`. Do not select on my behalf.
2. Make sure the dork library is populated. If `uv run dork dorks list --enabled`
   is empty, run `uv run dork dorks import data/seed_dorks.yaml`.
3. Show the plan and run the scan: `uv run dork scan` with any `--provider`
   given. The command prints a cost estimate and asks before spending; relay it
   and wait for my confirmation rather than passing `--yes` unless I said so.
4. After the scan, run `uv run dork triage show --untriaged` and summarize how
   many hits came back per target and category.

Never add a target or widen scope beyond what I authorize. Stop and ask if the
scope for a discovered target is unclear.
