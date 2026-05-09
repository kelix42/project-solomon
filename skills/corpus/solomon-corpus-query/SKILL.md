---
name: solomon-corpus-query
category: corpus
phase: decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-corpus-query", "search the corpus"]
inputs: [query string, optional namespace_weights, optional top_k]
outputs: [ranked list of chunks with citation paths]
reads_only: true
autonomy_level: L1
depends_on: []
portable: true
---

# solomon-corpus-query

Retrieval helper used by Lane 1 of the 5-lane retrieval (§2.8). Not typically owner-invoked, though the slash command works for ad-hoc lookups.

## v1 is read-only

Hits all four Pinecone namespaces (`solomon-corpus-wiki`, `solomon-captured-items`, `solomon-corpus-raw`, `solomon-decision-log`) with the configured weights from `memory/pinecone-index.md`. Deduplicates. Returns ranked chunks with citation paths back to `corpus/raw/` and `corpus/wiki/` (for wiki) or `db.captured_items` (for captured) or `db.decisions` (for decision_log).

## v2.1 deferred

Karpathy's "auto-file synthesized answers back as new concept pages" pattern requires a precise durability rule. Proposed criteria (not implemented in v1): same query asked ≥3 times across ≥2 sessions AND answer stable across runs.
