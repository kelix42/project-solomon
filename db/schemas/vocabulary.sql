-- vocabulary.sql — owner's voice as data (SQL-only; not embedded).
-- Normalization rule for `phrase`: lowercase, strip surrounding punctuation, collapse internal whitespace,
-- strip leading/trailing articles (the/a/an). NO stemming. Hyphens preserved as-is.

CREATE TABLE IF NOT EXISTS vocabulary (
    phrase             TEXT PRIMARY KEY,         -- normalized
    verbatim_examples  TEXT NOT NULL,            -- JSON list of original-cased instances
    type               TEXT NOT NULL CHECK (type IN ('np','vp','idiom','metaphor','stock_expression')),
    frequency          INTEGER NOT NULL DEFAULT 1,
    first_seen         TEXT NOT NULL,            -- captured_items.id
    last_seen          TEXT NOT NULL,
    domains            TEXT,                     -- JSON list of domains where it appeared
    aliases            TEXT                      -- JSON list of equivalent normalized spellings
);
