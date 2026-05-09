-- sessions.sql — onboarding/mentoring session state for resumption.

CREATE TABLE IF NOT EXISTS sessions (
    session_id        TEXT PRIMARY KEY,
    type              TEXT NOT NULL CHECK (type IN ('onboarding','mentoring')),
    domain            TEXT,                     -- pricing | hiring | … | null for mentoring
    status            TEXT NOT NULL CHECK (status IN ('active','complete','abandoned')),
    started_at        TEXT NOT NULL,
    last_activity_at  TEXT NOT NULL,
    completed_at      TEXT,
    abandoned_reason  TEXT,
    turns             INTEGER NOT NULL DEFAULT 0,
    notes             TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_status_type ON sessions(status, type);
