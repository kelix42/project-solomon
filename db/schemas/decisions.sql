-- decisions.sql — SQL mirror of decisions/log.md (one row per H2 entry).
-- Embedded by Sleep-Cycle Job 11.

CREATE TABLE IF NOT EXISTS decisions (
    id              TEXT PRIMARY KEY,        -- ulid
    decision_date   TEXT NOT NULL,           -- ISO 8601 from the H2 title (or UNKNOWN-DATE sentinel)
    title           TEXT NOT NULL,           -- H2 title body, max 60 chars
    body            TEXT NOT NULL,           -- canonical four-field rendering
    owner           TEXT NOT NULL,           -- name or initials
    machine_id      TEXT,                    -- recorded per §2.7 multi-device note
    embedded_at     TEXT,                    -- ISO 8601; null = pending Sleep-Cycle Job 11
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decisions_pending ON decisions(embedded_at) WHERE embedded_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_decisions_date    ON decisions(decision_date);
