-- coverage.sql — what's been probed, what's still thin.
-- Drives session-complete heuristics and probe-library version migration.

CREATE TABLE IF NOT EXISTS coverage (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    domain                   TEXT NOT NULL,
    sub_topic                TEXT NOT NULL,
    probe_count              INTEGER NOT NULL DEFAULT 0,
    items_captured           INTEGER NOT NULL DEFAULT 0,
    gap_score                REAL NOT NULL DEFAULT 1.0,    -- 1.0 = untouched, 0.0 = saturated
    last_probed              TEXT,                          -- ISO 8601, null if never
    last_probed_version      TEXT,                          -- semver of probe library at last probe
    library_version_seen     TEXT,                          -- highest probe-library version observed
    turns_since_last_capture INTEGER NOT NULL DEFAULT 0,
    notes                    TEXT,
    UNIQUE (domain, sub_topic)
);
