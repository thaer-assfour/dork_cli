from pathlib import Path

from dork_cli.db.database import Database
from dork_cli.db.models import Dork, Result, Target


def make_db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test.db")


def test_target_upsert_and_select(tmp_path):
    with make_db(tmp_path) as db:
        tid = db.upsert_target(Target(domain="example.com", name="Example",
                                      source="manual", scope=["*.example.com"]))
        assert tid
        db.set_selected("example.com", True)
        selected = db.list_targets(selected_only=True)
        assert len(selected) == 1
        assert selected[0].scope == ["*.example.com"]


def test_dork_add_and_filter(tmp_path):
    with make_db(tmp_path) as db:
        db.add_dork(Dork(template="site:{target} ext:env", category="secrets"))
        db.add_dork(Dork(template="site:{target} inurl:admin", category="panels",
                         enabled=False))
        enabled = db.list_dorks(enabled_only=True)
        assert len(enabled) == 1
        assert db.list_dorks(category="panels")[0].enabled is False


def test_dork_edit_and_delete(tmp_path):
    with make_db(tmp_path) as db:
        did = db.add_dork(Dork(template="site:{target} ext:env", category="secrets"))
        assert db.update_dork(did, risk="critical", category="config") == 1
        d = db.get_dork(did)
        assert d.risk == "critical" and d.category == "config"
        # no-op update changes nothing
        assert db.update_dork(did) == 0
        assert db.delete_dork(did) == 1
        assert db.get_dork(did) is None


def test_scan_results_and_cache(tmp_path):
    with make_db(tmp_path) as db:
        tid = db.upsert_target(Target(domain="example.com"))
        did = db.add_dork(Dork(template="site:{target} ext:env"))
        sid = db.create_scan("duckduckgo")
        db.add_result(Result(scan_id=sid, target_id=tid, dork_id=did,
                             query="site:example.com ext:env",
                             url="https://example.com/.env", title="env"))
        db.finish_scan(sid, query_count=1)
        rows = db.results_for_scan(sid)
        assert len(rows) == 1
        assert rows[0]["target_domain"] == "example.com"

        db.cache_put("k1", "duckduckgo", "q", '[{"x": 1}]')
        assert db.cache_get("k1", 72) == '[{"x": 1}]'
        assert db.cache_get("missing", 72) is None
