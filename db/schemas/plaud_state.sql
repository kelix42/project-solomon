-- plaud_state.sql — persistent state for the plaud-ingest worker (§2.4.5).
-- last_seen_uid: highest IMAP UID seen so search can skip already-known.
-- recent_email_ids: ring-buffered 7-day list for crash-recovery dedup.

CREATE TABLE IF NOT EXISTS plaud_state (
    id                INTEGER PRIMARY KEY CHECK (id = 1),  -- singleton row
    last_seen_uid     INTEGER NOT NULL DEFAULT 0,
    recent_email_ids  TEXT NOT NULL DEFAULT '[]',          -- JSON list
    last_idle_at      TEXT,
    last_poll_at      TEXT,
    consecutive_fails INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO plaud_state (id) VALUES (1);
