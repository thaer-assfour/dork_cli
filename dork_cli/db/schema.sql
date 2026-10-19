-- dork-cli schema. Applied idempotently on every run.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Discovered / imported targets. "selected" marks the ones you chose to work on.
CREATE TABLE IF NOT EXISTS targets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,
    domain       TEXT NOT NULL UNIQUE,
    source       TEXT,                      -- discloseio | security_txt | manual | ...
    scope_json   TEXT,                      -- JSON array of in-scope host patterns
    program_url  TEXT,                      -- policy / program page
    security_txt TEXT,                      -- raw security.txt contents if fetched
    status       TEXT DEFAULT 'new',        -- new | active | archived
    selected     INTEGER DEFAULT 0,         -- 0/1, you pick which targets to scan
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Dork library. "template" uses {target} where the host goes, e.g.
--   site:{target} intitle:"index of" "backup"
CREATE TABLE IF NOT EXISTS dorks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    template   TEXT NOT NULL UNIQUE,
    category   TEXT,                         -- exposure | panels | secrets | errors | ...
    risk       TEXT DEFAULT 'medium',        -- low | medium | high
    tags       TEXT,                         -- free-form comma list
    source     TEXT,                         -- seed | manual | generated
    enabled    INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- One row per "scan" invocation.
CREATE TABLE IF NOT EXISTS scans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT DEFAULT (datetime('now')),
    finished_at TEXT,
    provider    TEXT,
    status      TEXT DEFAULT 'running',      -- running | done | aborted
    query_count INTEGER DEFAULT 0,
    note        TEXT
);

-- Each hit returned for a (target, dork) query. This is the
-- "table of targets that were searched" the design calls for.
CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id     INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    target_id   INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    dork_id     INTEGER NOT NULL REFERENCES dorks(id) ON DELETE CASCADE,
    query       TEXT NOT NULL,
    url         TEXT,
    title       TEXT,
    snippet     TEXT,
    position    INTEGER,
    http_status INTEGER,
    found_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_results_scan ON results(scan_id);
CREATE INDEX IF NOT EXISTS idx_results_target ON results(target_id);

-- Triage lives in its own table so a single result can carry several
-- assessments over time. Claude fills these in-session after reading results.
CREATE TABLE IF NOT EXISTS triage (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id  INTEGER NOT NULL REFERENCES results(id) ON DELETE CASCADE,
    severity   TEXT,                          -- info | low | medium | high | critical
    verdict    TEXT,                          -- confirmed | likely | noise
    note       TEXT,
    next_step  TEXT,
    reviewer   TEXT DEFAULT 'claude',         -- claude | human
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_triage_result ON triage(result_id);

-- Query-response cache, so re-running a scan does not re-bill the provider.
CREATE TABLE IF NOT EXISTS query_cache (
    cache_key  TEXT PRIMARY KEY,             -- hash(provider + query + num)
    provider   TEXT,
    query      TEXT,
    response   TEXT,                          -- JSON-serialized list of results
    created_at TEXT DEFAULT (datetime('now'))
);
