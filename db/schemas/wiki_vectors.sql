-- wiki_vectors.sql — tracks live section hashes per wiki page so re-embeds clean up orphans.

CREATE TABLE IF NOT EXISTS wiki_vectors (
    page_path        TEXT PRIMARY KEY,        -- e.g., corpus/wiki/entities/customer-acme-corp.md
    section_hashes   TEXT NOT NULL,           -- JSON list of currently-active section_hash values
    last_updated     TEXT NOT NULL
);
