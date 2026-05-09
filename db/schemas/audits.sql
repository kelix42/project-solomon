-- audits.sql — audit verdicts and rationale per pipeline event. Carry-over from Solomon v1.

CREATE TABLE IF NOT EXISTS audits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      TEXT NOT NULL,
    verdict       TEXT NOT NULL CHECK (verdict IN ('APPROVE','DOWNGRADE','REJECT','REQUEST_RETHINK')),
    rationale     TEXT,
    audited_at    TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);
CREATE INDEX IF NOT EXISTS idx_audits_event ON audits(event_id);
