"""SQLite connection handling and data-access helpers."""

from __future__ import annotations

import sqlite3
from importlib import resources
from pathlib import Path

from .models import Dork, Result, Target


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._apply_schema()

    def _apply_schema(self) -> None:
        schema = resources.files("dork_cli.db").joinpath("schema.sql").read_text()
        self.conn.executescript(schema)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- targets -------------------------------------------------------
    def upsert_target(self, t: Target) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO targets (name, domain, source, scope_json, program_url,
                                 security_txt, status, selected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                name=COALESCE(excluded.name, targets.name),
                source=COALESCE(excluded.source, targets.source),
                scope_json=COALESCE(excluded.scope_json, targets.scope_json),
                program_url=COALESCE(excluded.program_url, targets.program_url),
                security_txt=COALESCE(excluded.security_txt, targets.security_txt)
            """,
            (t.name, t.domain, t.source, t.scope_json, t.program_url,
             t.security_txt, t.status, int(t.selected)),
        )
        self.conn.commit()
        if cur.lastrowid:
            row = self.conn.execute(
                "SELECT id FROM targets WHERE domain=?", (t.domain,)
            ).fetchone()
            return row["id"]
        return cur.lastrowid

    def set_selected(self, domain: str, selected: bool) -> int:
        cur = self.conn.execute(
            "UPDATE targets SET selected=? WHERE domain=?",
            (int(selected), domain),
        )
        self.conn.commit()
        return cur.rowcount

    def list_targets(self, selected_only: bool = False) -> list[Target]:
        sql = "SELECT * FROM targets"
        if selected_only:
            sql += " WHERE selected=1"
        sql += " ORDER BY id"
        rows = self.conn.execute(sql).fetchall()
        return [Target.from_row(r) for r in rows]

    # ---- dorks ---------------------------------------------------------
    def add_dork(self, d: Dork) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO dorks (template, category, risk, tags, source, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(template) DO UPDATE SET
                category=excluded.category,
                risk=excluded.risk,
                tags=excluded.tags
            """,
            (d.template, d.category, d.risk, d.tags, d.source, int(d.enabled)),
        )
        self.conn.commit()
        return cur.lastrowid

    def set_dork_enabled(self, dork_id: int, enabled: bool) -> int:
        cur = self.conn.execute(
            "UPDATE dorks SET enabled=? WHERE id=?", (int(enabled), dork_id)
        )
        self.conn.commit()
        return cur.rowcount

    def get_dork(self, dork_id: int) -> Dork | None:
        row = self.conn.execute(
            "SELECT * FROM dorks WHERE id=?", (dork_id,)
        ).fetchone()
        return Dork.from_row(row) if row else None

    def update_dork(self, dork_id: int, *, template: str | None = None,
                    category: str | None = None, risk: str | None = None,
                    tags: str | None = None) -> int:
        """Update fields of an existing dork in place. Only given fields change."""
        sets, params = [], []
        for col, val in (("template", template), ("category", category),
                         ("risk", risk), ("tags", tags)):
            if val is not None:
                sets.append(f"{col}=?")
                params.append(val)
        if not sets:
            return 0
        params.append(dork_id)
        cur = self.conn.execute(
            f"UPDATE dorks SET {', '.join(sets)} WHERE id=?", params
        )
        self.conn.commit()
        return cur.rowcount

    def delete_dork(self, dork_id: int) -> int:
        cur = self.conn.execute("DELETE FROM dorks WHERE id=?", (dork_id,))
        self.conn.commit()
        return cur.rowcount

    def list_dorks(self, enabled_only: bool = False,
                   category: str | None = None) -> list[Dork]:
        sql = "SELECT * FROM dorks"
        clauses, params = [], []
        if enabled_only:
            clauses.append("enabled=1")
        if category:
            clauses.append("category=?")
            params.append(category)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id"
        rows = self.conn.execute(sql, params).fetchall()
        return [Dork.from_row(r) for r in rows]

    # ---- scans & results ----------------------------------------------
    def create_scan(self, provider: str, note: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO scans (provider, note) VALUES (?, ?)", (provider, note)
        )
        self.conn.commit()
        return cur.lastrowid

    def finish_scan(self, scan_id: int, query_count: int,
                    status: str = "done") -> None:
        self.conn.execute(
            "UPDATE scans SET finished_at=datetime('now'), status=?, query_count=? "
            "WHERE id=?",
            (status, query_count, scan_id),
        )
        self.conn.commit()

    def add_result(self, r: Result) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO results (scan_id, target_id, dork_id, query, url, title,
                                 snippet, position, http_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (r.scan_id, r.target_id, r.dork_id, r.query, r.url, r.title,
             r.snippet, r.position, r.http_status),
        )
        self.conn.commit()
        return cur.lastrowid

    def results_for_scan(self, scan_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT r.*, t.domain AS target_domain, d.category AS dork_category
            FROM results r
            JOIN targets t ON t.id = r.target_id
            JOIN dorks d ON d.id = r.dork_id
            WHERE r.scan_id = ?
            ORDER BY r.id
            """,
            (scan_id,),
        ).fetchall()

    def latest_scan_id(self) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM scans ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["id"] if row else None

    # ---- cache ---------------------------------------------------------
    def cache_get(self, key: str, ttl_hours: int) -> str | None:
        row = self.conn.execute(
            """
            SELECT response FROM query_cache
            WHERE cache_key = ?
              AND created_at >= datetime('now', ?)
            """,
            (key, f"-{ttl_hours} hours"),
        ).fetchone()
        return row["response"] if row else None

    def cache_put(self, key: str, provider: str, query: str, response: str) -> None:
        self.conn.execute(
            """
            INSERT INTO query_cache (cache_key, provider, query, response)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                response=excluded.response,
                created_at=datetime('now')
            """,
            (key, provider, query, response),
        )
        self.conn.commit()
