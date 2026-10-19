import pytest

from dork_cli.core.query_builder import ScopeError, build_query


def test_placeholder_substitution():
    q = build_query("example.com", "site:{target} ext:sql")
    assert q == "site:example.com ext:sql"


def test_prepends_site_when_missing():
    q = build_query("example.com", 'intitle:"index of"')
    assert q == 'site:example.com intitle:"index of"'


def test_existing_site_kept_when_matching_host():
    q = build_query("example.com", "site:example.com inurl:admin")
    assert "example.com" in q


def test_host_normalized():
    q = build_query("https://Example.com/path", "ext:env")
    assert q.startswith("site:example.com")


def test_scope_error_when_host_absent():
    with pytest.raises(ScopeError):
        build_query("example.com", "site:other.com secret")
