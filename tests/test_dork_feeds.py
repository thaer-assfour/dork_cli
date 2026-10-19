from dork_cli.sources import dork_feeds as f


def test_normalize_adds_site_prefix():
    assert f.normalize_template('intitle:"index of"') == 'site:{target} intitle:"index of"'


def test_normalize_replaces_concrete_site():
    assert f.normalize_template("site:example.com ext:sql") == "site:{target} ext:sql"


def test_normalize_keeps_existing_target_placeholder():
    assert f.normalize_template("site:{target} inurl:admin") == "site:{target} inurl:admin"


def test_categorize_secrets():
    assert f.categorize("site:{target} ext:env") == "secrets"


def test_categorize_panels():
    assert f.categorize("site:{target} inurl:admin") == "panels"


def test_categorize_fallback_misc():
    assert f.categorize("site:{target} intext:hello") == "misc"


def test_parse_json_list_of_strings():
    entries = f.parse_feed('["site:example.com ext:sql", "inurl:admin"]')
    assert len(entries) == 2
    assert entries[0]["raw"] == "site:example.com ext:sql"


def test_parse_json_list_of_objects_with_wrapper():
    text = '{"data": [{"query": "ext:env", "category": "secrets", "risk": "critical"}]}'
    entries = f.parse_feed(text)
    assert entries[0]["category"] == "secrets"
    assert entries[0]["risk"] == "critical"


def test_parse_csv():
    text = "dork,category\nsite:x.com ext:sql,files\ninurl:login,panels\n"
    entries = f.parse_feed(text)
    assert len(entries) == 2
    assert entries[1]["category"] == "panels"


def test_parse_lines_skips_comments():
    text = "# header\nsite:{target} ext:env\n\ninurl:admin\n"
    entries = f.parse_feed(text)
    assert len(entries) == 2


def test_feed_to_dorks_autocategorizes():
    entries = f.parse_feed('["ext:env", "inurl:dashboard"]')
    dorks = f.feed_to_dorks(entries, source_label="ghdb")
    assert dorks[0].category == "secrets"
    assert dorks[0].template.startswith("site:{target}")
    assert dorks[0].source == "ghdb"
