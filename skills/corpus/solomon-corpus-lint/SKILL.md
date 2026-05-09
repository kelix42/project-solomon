---
name: solomon-corpus-lint
category: corpus
phase: decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-corpus-lint", "Sleep-Cycle Job 9"]
inputs: [corpus/wiki/, corpus/raw/, db.captured_items, db.ingested_files, db.wiki_vectors, Pinecone solomon-corpus-raw]
outputs: [mentoring_queue rows, corpus/log.md lint report]
reads_only: false
autonomy_level: L2
depends_on: []
portable: true
---

# solomon-corpus-lint

Sleep-Cycle Job 9. Also callable on demand.

## What it scans

- **Contradictions**: wiki claims that disagree with each other or with captured_items.
- **Stale pages** (corrected rule per §2.7): a wiki page is stale if there exist `ingested_files` rows with `category` matching the page's domain (or referencing the page's primary entity) whose `ingested_at > wiki_page.last_updated` AND whose content has not yet been merged into the page's source-citations. Top 20 stalest → mentoring_queue priority 6.
- **Orphan pages**: wiki pages with no inbound cross-references → mentoring_queue priority 8.
- **Missing cross-refs**: entity pages mentioned in raw text without backlinks → flag at priority 7.
- **Near-duplicates**: cosine similarity > 0.95 in `solomon-corpus-raw` → mentoring_queue priority 7.
- **Parking folder check**: files in `corpus/inbox/_oversized/` or `_unsupported/` → mentoring_queue priority 7.

## Output

Lint report appended to `corpus/log.md`. Mentoring_queue rows for owner attention.
