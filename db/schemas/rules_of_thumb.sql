-- rules_of_thumb.sql — fast-look-up condensed rules (a denormalized view derived from captured_items).
-- Carry-over from Solomon v1.

CREATE TABLE IF NOT EXISTS rules_of_thumb (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain          TEXT NOT NULL,
    short_form      TEXT NOT NULL,                -- ≤120 chars, owner's verbatim ideal
    captured_id     TEXT NOT NULL,                -- backlink to captured_items
    use_count_30d   INTEGER NOT NULL DEFAULT 0,
    last_used       TEXT,
    FOREIGN KEY (captured_id) REFERENCES captured_items(id)
);
CREATE INDEX IF NOT EXISTS idx_rot_domain ON rules_of_thumb(domain);
