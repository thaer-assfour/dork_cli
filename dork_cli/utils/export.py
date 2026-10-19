"""Export scan results to CSV / JSON / Markdown for downstream tooling."""

from __future__ import annotations

import csv
import json
from pathlib import Path

_FIELDS = ["id", "target_domain", "dork_category", "query", "title", "url",
           "snippet", "position"]


def _row_to_dict(row) -> dict:
    return {k: row[k] for k in _FIELDS}


def to_csv(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(_row_to_dict(row))


def to_json(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([_row_to_dict(r) for r in rows], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def to_markdown(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["| Target | Category | Title | URL |", "|---|---|---|---|"]
    for r in rows:
        title = (r["title"] or "").replace("|", "\\|")
        lines.append(f"| {r['target_domain']} | {r['dork_category'] or ''} "
                     f"| {title} | {r['url'] or ''} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export(rows, path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        to_csv(rows, path)
    elif suffix == ".json":
        to_json(rows, path)
    elif suffix in (".md", ".markdown"):
        to_markdown(rows, path)
    else:
        raise ValueError(f"Unsupported export format: {suffix}")
