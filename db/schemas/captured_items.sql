-- captured_items.sql — primary owner-rules store.
-- Embedded by Sleep-Cycle Job 11 (column embedded_at). Vocabulary is in a separate table and is NOT embedded.

CREATE TABLE IF NOT EXISTS captured_items (
    id              TEXT PRIMARY KEY,        -- ulid
    domain          TEXT NOT NULL,           -- pricing | hiring | ops | customer | vendor | finance | …
    type            TEXT NOT NULL CHECK (type IN ('rule','exception','trigger','preference','value','story')),
    statement       TEXT NOT NULL,           -- normalized rule/value
    verbatim_phrase TEXT,                    -- owner's exact wording (preserve casing/punctuation)
    example         TEXT,                    -- a real instance, if given
    reasoning       TEXT,                    -- why the owner does it this way
    conditions      TEXT,                    -- JSON list of clause strings — PROSE ONLY, not evaluated by Stage 4
    conflicts_with  TEXT,                    -- JSON list of captured_items.id this contradicts
    confidence      TEXT NOT NULL CHECK (confidence IN ('stated','repeated','exemplified')),
    source_session  TEXT NOT NULL,           -- onboarding-NN-domain | mentoring-YYYY-MM-DD | corpus-extract-<ulid>
    source_turn     INTEGER NOT NULL,        -- nth question of that session
    keywords        TEXT NOT NULL,           -- JSON list, lowercase, used for retrieval
    embedded_at     TEXT,                    -- ISO 8601; null = pending Sleep-Cycle Job 11
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_captured_domain   ON captured_items(domain);
CREATE INDEX IF NOT EXISTS idx_captured_keywords ON captured_items(keywords);
CREATE INDEX IF NOT EXISTS idx_captured_source   ON captured_items(source_session, source_turn);
CREATE INDEX IF NOT EXISTS idx_captured_pending  ON captured_items(embedded_at) WHERE embedded_at IS NULL;
