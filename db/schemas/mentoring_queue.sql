-- mentoring_queue.sql — cross-session items awaiting batched owner attention.
--
-- Priority assignments (lower = more urgent):
--   1: corpus-lint contradiction, both items confidence=exemplified
--   2: real-time contradiction-check (escalated after retries) — though most go to clarification_queue
--   3: Sleep-cycle Job 5 conflict-detection, OR corpus-lint contradiction with mixed confidence
--   4: Sleep-cycle Job 3 surprise-replay, OR corpus_rule_proposal
--   5: coverage-tracker gap, OR yaml_hand_edit reconciliation
--   6: legacy_decision_undated (ported v1 decision missing date), OR corpus-lint stale page
--   7: probe_library_update, OR corpus-lint near-duplicate, OR _oversized/_unsupported parking folders
--   8: corpus-lint orphan page

CREATE TABLE IF NOT EXISTS mentoring_queue (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    source                TEXT NOT NULL CHECK (source IN (
                              'lint','contradiction','surprise','coverage_gap',
                              'probe_library_update','yaml_hand_edit','legacy_decision_undated',
                              'corpus_rule_proposal'
                          )),
    surfaced_at           TEXT NOT NULL,
    status                TEXT NOT NULL CHECK (status IN ('queued','addressed','dismissed')),
    priority              INTEGER NOT NULL DEFAULT 5,
    payload               TEXT NOT NULL,           -- JSON
    addressed_at          TEXT,
    addressed_in_session  TEXT,                    -- mentoring-YYYY-MM-DD slug
    notes                 TEXT
);
CREATE INDEX IF NOT EXISTS idx_mq_status_priority ON mentoring_queue(status, priority);
