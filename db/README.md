# Solomon SQLite Schema

`db/solomon.db` is the canonical structured store. WAL mode is required.

## WAL pragmas (every connection)

Every Solomon plugin and worker that opens this DB MUST apply these pragmas on first open AND on every subsequent connection. Hermes does NOT inject them automatically (per §2.4.6 verification). Concurrent writes from multiple workers + the Hermes gateway will hit `database is locked` without WAL.

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
```

## Tables

### Interview-phase (canonical owner-rule store)
- `captured_items.sql` — primary owner-rules store. Embedded by Sleep-Cycle Job 11 (column `embedded_at`).
- `coverage.sql` — what's been probed; tracks `last_probed_version` for probe-library migration.
- `vocabulary.sql` — owner's voice as data. **SQL-only; not embedded** (§1 of SOLOMON-PLAN.md).

### Lifecycle and pipeline
- `events.sql` — every real-time decision event flowing through the §2.2.5 pipeline.
- `working_memory.sql` — hot cache for the pipeline; SQLite-backed LRU, 7-day TTL.
- `scope_autonomy.sql` — current autonomy level per scope (L0–L4); updated by Sleep-Cycle Job 7.
- `mentoring_queue.sql` — cross-session items awaiting batched owner attention.
- `clarification_queue.sql` — in-session contradictions; jumps the queue inside `solomon-interview-engine`.
- `sessions.sql` — onboarding/mentoring resumption flag.

### Corpus
- `ingested_files.sql` — corpus ingest manifest (sha256, status, run_id) for idempotency.
- `wiki_vectors.sql` — tracks live section hashes per wiki page so re-embeds clean up orphans.
- `proposed_rules.sql` — staging area for rules extracted from corpus; mentoring confirms each before they reach `captured_items`.

### Carry-over from Solomon v1
- `decisions.sql` — SQL mirror of `decisions/log.md` (one row per H2 entry); embedded by Job 11.
- `audits.sql`, `biometrics.sql`, `rules_of_thumb.sql`, `mentoring_sessions.sql` — schemas inherited from Solomon v1.

### Per-worker state
- `plaud_state.sql` — last-seen IMAP UID + downloaded-IDs over the last 7 days for the `plaud-ingest` worker. Other ingress workers add their own state tables when their per-source spec is locked (§2.4.5).

## Idempotency

- File ingest: SHA256 of file bytes is the canonical equality test. The `ingested_files.sha256` UNIQUE constraint enforces it.
- Pinecone vector IDs are deterministic: `sha256(file)[:16] + ":" + chunk_index` for raw, `"wiki:" + slug + ":" + section_hash` for wiki, `"captured:" + row.id`, `"decision:" + sha256(entry_body) + ":0"`. Pinecone upserts replace.
- Wiki vector cleanup: `solomon-corpus-ingest` reads `wiki_vectors.section_hashes` before re-embedding; deletes Pinecone vectors for hashes that disappeared from the new page.

## Embed-pending pattern (Sleep-Cycle Job 11)

Tables `captured_items` and `decisions` have an `embedded_at TEXT` column. New rows land with `embedded_at = NULL`. Job 11 picks up null rows nightly, batch-embeds via `text-embedding-3-large`, upserts to Pinecone, sets `embedded_at = NOW()`. Failure mode: row stays null, retried next night. Vocabulary is NOT embedded — SQL frequency queries serve all use cases.

## Concurrent Pinecone writes

`db/.pinecone-write.lock` (file lock) gates all Pinecone writes from `solomon-corpus-ingest`, Job 11, and any other writer. At most one Pinecone write process is in-flight at any moment. Stale lock (PID dead) cleared on Hermes / worker startup.
