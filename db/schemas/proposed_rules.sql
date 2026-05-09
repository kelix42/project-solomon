-- proposed_rules.sql — staging area for owner rules extracted from corpus raw text.
-- The two-phase rule (§0) keeps the interview as the only authoritative writer of captured_items;
-- corpus extraction surfaces candidates here, mentoring confirms each before they cross over.

CREATE TABLE IF NOT EXISTS proposed_rules (
    id                    TEXT PRIMARY KEY,        -- ulid
    domain                TEXT NOT NULL,
    proposed_statement    TEXT NOT NULL,           -- normalized
    verbatim_excerpt      TEXT NOT NULL,           -- the owner's actual sentence from raw
    source_path           TEXT NOT NULL,           -- corpus/raw/<category>/<file>
    source_offset         INTEGER,                 -- character offset in raw
    keywords              TEXT NOT NULL,           -- JSON list, lowercase
    confidence_hint       TEXT CHECK (confidence_hint IN ('stated','repeated','exemplified')),
    proposed_jsonlogic    TEXT,                    -- optional draft if rule looks deterministic
    status                TEXT NOT NULL CHECK (status IN ('queued','confirmed','rejected','edited')),
    created_at            TEXT NOT NULL,
    addressed_at          TEXT,
    addressed_in_session  TEXT,
    captured_item_id      TEXT,                    -- captured_items.id once confirmed
    hard_rule_promoted    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pr_status_domain ON proposed_rules(status, domain);
