-- events.sql — every real-time decision event flowing through the §2.2.5 pipeline.
-- Canonical record for crash recovery and audit. Read by the pipeline-tick worker.

CREATE TABLE IF NOT EXISTS events (
    event_id           TEXT PRIMARY KEY,        -- ulid
    source             TEXT NOT NULL,           -- telegram | plaud_live | whoop | gmail_live | calendar | webhook | file_dropped
    payload            TEXT NOT NULL,           -- JSON
    received_at        TEXT NOT NULL,
    processed_at       TEXT,
    salience_score     REAL,
    classification     TEXT,                    -- JSON {scope, domain, decision_type}
    hard_rule_blocked  TEXT,                    -- captured_items.id of the violated rule, or NULL
    system1_output     TEXT,
    system2_output     TEXT,
    divergence_score   REAL,                    -- token-Jaccard 0.0–1.0 (NOT cosine — see §2.2.5 Stage 7b)
    audit_verdict      TEXT,                    -- APPROVE | DOWNGRADE | REJECT | REQUEST_RETHINK
    owner_state        TEXT,                    -- green | yellow | red | unknown
    action_taken       TEXT,
    status             TEXT NOT NULL CHECK (status IN (
                           'pending','in_progress','complete','skipped','failed','blocked_by_hard_rule'
                       )),
    stage_timings_ms   TEXT                     -- JSON {capture, salience, classification, …, action}
);
CREATE INDEX IF NOT EXISTS idx_events_status   ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_source   ON events(source, received_at);
