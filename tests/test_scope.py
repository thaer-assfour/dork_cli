from dork_cli.core.scope import default_scope, effective_scope, is_in_scope, normalize_host


def test_normalize_strips_scheme_and_path():
    assert normalize_host("https://Example.com/foo") == "example.com"


def test_default_scope_includes_wildcard():
    assert default_scope("example.com") == ["example.com", "*.example.com"]


def test_in_scope_exact():
    assert is_in_scope("example.com", ["example.com"])


def test_in_scope_wildcard():
    assert is_in_scope("api.example.com", ["*.example.com"])


def test_out_of_scope():
    assert not is_in_scope("evil.com", ["example.com", "*.example.com"])


def test_empty_scope_is_never_in_scope():
    assert not is_in_scope("example.com", [])


def test_effective_scope_falls_back_to_self():
    assert effective_scope("example.com", []) == ["example.com", "*.example.com"]
