# Corpus / LLM Wiki — Karpathy attribution + Solomon's Pinecone-extended adaptation

Original gist: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>. Mirrored at `archives/karpathy-llm-wiki.md`.

Karpathy's pattern: 3 layers (raw sources, LLM-maintained wiki, schema config) + 3 operations (ingest, query, lint). Compounding insight: pre-compiled wiki pages mean answers don't get re-derived from scratch on every query the way pure RAG does.

## Solomon's adaptation

| Layer | Folder | Mutability | Pinecone | Lane-1 weight |
|---|---|---|---|---|
| Raw | `corpus/raw/<category>/` | Immutable | namespace `solomon-corpus-raw` | 0.20 |
| Wiki | `corpus/wiki/{entities,concepts,playbooks}/` | LLM-maintained | namespace `solomon-corpus-wiki` | 0.40 |
| Index + log | `corpus/index.md` + `corpus/log.md` | LLM-maintained | n/a | n/a |

## Skills

- `solomon-corpus-ingest` — entry point; routes file, redacts PII, drafts wiki pages, runs **rule-extraction pass** (proposed_rules), embeds.
- `solomon-corpus-lint` — Sleep-Cycle Job 9; surfaces stale, contradictions, orphans, near-duplicates.
- `solomon-corpus-query` — read-only retrieval helper used by Lane 1. v1 does NOT auto-file synthesized answers back as new pages (deferred to v2.1).
- `solomon-corpus-forget` — owner-triggered deletion / GDPR-style revocation; cascades through wiki / raw / Pinecone / captured_items / vocabulary.

## Why Pinecone instead of grep

Karpathy's pattern assumes file-based grep. Solomon scales by replacing grep with semantic search across 4 namespaces (wiki + raw + captured_items + decision_log). Wiki outranks raw at retrieval because wiki pages are already synthesized and cross-referenced.

## Idempotency

SHA256 manifest at `db.ingested_files`. Deterministic Pinecone vector IDs. Wiki section hashes tracked in `db.wiki_vectors` so re-embeds clean up orphans.
