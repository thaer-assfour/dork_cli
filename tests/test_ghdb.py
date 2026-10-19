from dork_cli.sources import ghdb

SAMPLE = {
    "recordsTotal": 3,
    "data": [
        {
            "url_title": '<a href="/ghdb/8000">intitle:"index of" "config.php"</a>',
            "category": {"cat_id": "3", "cat_title": "Sensitive Directories"},
            "date": "2024-01-01",
        },
        {
            "url_title": '\t<a href="/ghdb/8001">site:example.com ext:sql</a>',
            "category": {"cat_id": "9", "cat_title": "Files Containing Passwords"},
            "date": "2024-02-02",
        },
        {
            "url_title": '<a href="/ghdb/8002">inurl:admin login</a>',
            "category": {"cat_id": "12", "cat_title": "Pages Containing Login Portals"},
            "date": "2024-03-03",
        },
    ],
}


def test_extract_dork_strips_anchor():
    assert ghdb.extract_dork('<a href="/ghdb/1">foo bar</a>') == "foo bar"


def test_extract_dork_handles_tabs_and_no_link():
    assert ghdb.extract_dork("\tplain text") == "plain text"


def test_parse_maps_category_and_normalizes():
    dorks = ghdb.parse_ghdb(SAMPLE)
    assert len(dorks) == 3
    # Sensitive Directories -> exposure, template gets site:{target} prefix
    assert dorks[0].category == "exposure"
    assert dorks[0].template.startswith("site:{target} ")
    assert dorks[0].tags == "ghdb:Sensitive Directories"
    # concrete site rewritten to {target}
    assert dorks[1].template == "site:{target} ext:sql"
    assert dorks[1].category == "secrets"
    # login portals -> panels
    assert dorks[2].category == "panels"
    assert all(d.source == "ghdb" for d in dorks)


def test_parse_category_filter():
    dorks = ghdb.parse_ghdb(SAMPLE, category_filter="Files Containing Passwords")
    assert len(dorks) == 1
    assert dorks[0].template == "site:{target} ext:sql"


def test_parse_limit():
    assert len(ghdb.parse_ghdb(SAMPLE, limit=2)) == 2


def test_parse_empty_payload():
    assert ghdb.parse_ghdb({}) == []
    assert ghdb.parse_ghdb({"data": []}) == []
