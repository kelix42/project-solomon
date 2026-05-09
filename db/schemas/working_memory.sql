-- working_memory.sql — hot cache for the §2.2.5 pipeline; SQLite-backed LRU with 7-day TTL.
-- No Redis dependency in v1.

CREATE TABLE IF NOT EXISTS working_memory (
    key              TEXT PRIMARY KEY,        -- e.g., "scope:pricing:active_thread:deal-acme-1234"
    value            TEXT NOT NULL,           -- JSON
    expires_at       TEXT NOT NULL,
    last_accessed    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wm_expires ON working_memory(expires_at);
