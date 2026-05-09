---
name: solomon-corpus-ingest
category: corpus
phase: decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-corpus-ingest", "ingest corpus file"]
inputs: [file_paths or globs, current corpus state, corpus/schema.md]
outputs: [corpus/raw/<category>/files, corpus/wiki/ pages, db.ingested_files row, db.proposed_rules rows, db.wiki_vectors update, Pinecone upserts, corpus/log.md, corpus/index.md]
reads_only: false
autonomy_level: L2
depends_on: [solomon-redact]
portable: true
---

# solomon-corpus-ingest

The corpus entry point. Triggered automatically by the `corpus-inbox-watcher` worker when files appear in `corpus/inbox/`; manually via `/solomon-corpus-ingest <file>`.

## Process per file

1. **Manifest check**: SHA256 the file. If `db.ingested_files.sha256` shows `status = success`, skip and log "already-ingested." Otherwise create/update the row with `status = pending`.
2. **Routing** (per §2.5): subfolder hint → extension map → LLM classifier fallback. Land in `corpus/raw/<category>/<normalized-slug>`.
3. **Redaction**: call `solomon-redact` on the file content. Original bytes go to `corpus/raw/_pre-redaction/<sha256>.bin` (encrypted).
4. **LLM passes** (Sonnet):
   a. Summarize. b. Extract entities (PERSON/ORG/LOC/GPE + business-specific). c. Draft/update entity/concept/playbook wiki pages. d. **Rule-extraction pass** — extract any first-person owner rules; write to `db.proposed_rules` with `status = queued`; write a `mentoring_queue` row (`source = corpus_rule_proposal`, priority 4) per proposal.
5. **Wiki vector cleanup**: read `db.wiki_vectors.section_hashes` for each touched page. Compute new hashes. Delete Pinecone vectors for hashes that disappeared. Upsert new vectors. Update the row.
6. **Embed raw**: chunk via sliding window (800 tokens, 100 overlap). Upsert to Pinecone namespace `solomon-corpus-raw` with deterministic IDs.
7. **Append `corpus/log.md`** with the slug, action, and counts.
8. **Update `corpus/index.md`** with new pages.
9. **Set `ingested_files.status = success`** and `pinecone_vectors` count.

## Concurrent Pinecone writes

Acquires `db/.pinecone-write.lock` for the duration of step 5/6. Job 11 also acquires this; one Pinecone write at a time, ever.

## Failure handling

Per §2.4.7: file-stable mid-write → wait. Pinecone 5xx → status = partial, retry next ingest. OpenAI rate-limit → exponential backoff (1s, 2s, 4s, 8s, 16s, give up; resume next sleep cycle).
