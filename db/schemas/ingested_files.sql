-- ingested_files.sql — corpus ingest manifest. SHA256 dedup is canonical.

CREATE TABLE IF NOT EXISTS ingested_files (
    id                    TEXT PRIMARY KEY,        -- ulid
    sha256                TEXT NOT NULL UNIQUE,
    inbox_path_at_ingest  TEXT NOT NULL,
    raw_path              TEXT,                    -- final location after move
    size_bytes            INTEGER NOT NULL,
    mime_type             TEXT,
    category              TEXT NOT NULL CHECK (category IN ('sops','emails','messages','docs','data')),
    ingest_run_id         TEXT NOT NULL,
    status                TEXT NOT NULL CHECK (status IN ('pending','in_progress','success','partial','failed','forgotten')),
    wiki_pages_touched    TEXT,                    -- JSON list
    pinecone_vectors      INTEGER,
    error_message         TEXT,
    ingested_at           TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ingested_status ON ingested_files(status);
