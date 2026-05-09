-- scope_autonomy.sql — current autonomy level per scope (L0–L4); updated by Sleep-Cycle Job 7.

CREATE TABLE IF NOT EXISTS scope_autonomy (
    scope                  TEXT PRIMARY KEY,
    level                  INTEGER NOT NULL CHECK (level BETWEEN 0 AND 4),
    since                  TEXT NOT NULL,
    last_reeval_at         TEXT NOT NULL,
    override_rate_30d      REAL,
    audit_pass_rate_30d    REAL,
    notes                  TEXT
);
