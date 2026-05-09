---
name: solomon-corpus-forget
category: corpus
phase: decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-corpus-forget"]
inputs: [file_path | entity_slug | wiki_page_slug]
outputs: [hard-delete and rewrite cascades, db.ingested_files.status updates, decisions/log.md entry]
reads_only: false
autonomy_level: L1
depends_on: []
portable: true
---

# solomon-corpus-forget

Owner-triggered deletion / GDPR-style revocation. Every forget is destructive — owner gets a one-tap Telegram confirmation showing the per-row diff before any action.

## Cascade rules (deterministic)

1. **Entity page** dedicated to the forgotten entity → hard-delete file + Pinecone vectors by deterministic ID.
2. **Concept or playbook pages** mentioning the forgotten entity → LLM-driven full-page rewrite (Opus). Prompt: rewrite this page removing all references to the entity while preserving surrounding logic. Update `last_updated`. Re-embed.
3. **Raw files** for the forgotten entity → moved to `corpus/_forgotten/<sha256>/` (AES-256-GCM with backup key); `db.ingested_files.status = forgotten`; raw vectors deleted.
4. **`db.captured_items` rows** mentioning the forgotten entity in `verbatim_phrase` / `example` / `statement`:
   - If surrounding rule logic survives → in-place redact (`[REDACTED:entity]`), update `updated_at`, re-embed (set `embedded_at = NULL` so Job 11 picks it up).
   - If the entire row is about the forgotten entity → hard-delete row + Pinecone vector.
5. **`db.vocabulary` rows**: hard-delete if `phrase` (after normalization) exactly matches the entity's slug or any value in `aliases`. Otherwise leave.

## Logging

Each action logged line-by-line to `corpus/log.md` and a single roll-up entry to `decisions/log.md`.
