-- mentoring_sessions.sql — log of mentoring sessions themselves (distinct from mentoring_queue).

CREATE TABLE IF NOT EXISTS mentoring_sessions (
    session_id    TEXT PRIMARY KEY,            -- mentoring-YYYY-MM-DD-<n>
    started_at    TEXT NOT NULL,
    completed_at  TEXT,
    topics_count  INTEGER NOT NULL DEFAULT 0,
    new_captured  INTEGER NOT NULL DEFAULT 0,
    summary       TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
