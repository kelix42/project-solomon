-- clarification_queue.sql — in-session contradictions, resolved while context is fresh.
-- solomon-interview-engine reads this BEFORE every probe selection; pending clarifications jump the queue.
-- solomon-contradiction-check writes here for SAME-SESSION conflicts.
-- mentoring_queue is reserved for cross-session items.

CREATE TABLE IF NOT EXISTS clarification_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    captured_id_a   TEXT NOT NULL,
    captured_id_b   TEXT NOT NULL,
    suggested_probe TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('queued','asked','resolved','dismissed')),
    created_at      TEXT NOT NULL,
    resolved_at     TEXT,
    resolution_id   TEXT                         -- captured_items.id of the resolving rule
);
CREATE INDEX IF NOT EXISTS idx_cq_session_status ON clarification_queue(session_id, status);
