# Corpus

Solomon's bulk knowledge layer, adapted from Karpathy's LLM Wiki pattern. See `archives/karpathy-llm-wiki.md` for the original idea and `references/corpus-llm-wiki.md` for Solomon's Pinecone-extended adaptation.

## How files get processed

- Drop files in `inbox/`. They will be processed automatically within ~30 seconds.
- If Hermes is not running, files will be processed the next time the `corpus-inbox-watcher` worker starts.
- To trigger manually, run `/solomon-corpus-ingest <path>` in any Hermes session.

## Folder layout

- `inbox/` — drop zone. Subfolder names act as routing hints (`sops/`, `emails/`, `messages/`, `docs/`, `data/`).
- `raw/` — immutable cleaned copies. The LLM reads these but never edits.
- `wiki/` — LLM-maintained synthesized pages: `entities/`, `concepts/`, `playbooks/`.
- `index.md` — auto-maintained catalog of every wiki page.
- `log.md` — append-only chronicle of ingest/query/lint events.
- `schema.md` — configuration: routing, limits, redaction allowlist, transcription/OCR backends.

## What gets indexed in Pinecone

- Wiki pages → namespace `solomon-corpus-wiki` (Lane 1 retrieval weight 0.40 — highest).
- Raw chunks (sliding-window, 800 tokens / 100 overlap) → namespace `solomon-corpus-raw` (weight 0.20).
- captured_items rows → namespace `solomon-captured-items` (weight 0.30; embedded by Sleep-Cycle Job 11).
- Decision-log entries → namespace `solomon-decision-log` (weight 0.10; embedded by Job 11).

## Owner rules buried in raw text

When `solomon-corpus-ingest` finds a first-person rule in your SOPs/emails (e.g., "I never quote below cost+15%"), it doesn't write to `captured_items` directly. It queues the proposal to `db.proposed_rules` and surfaces it in the next mentoring session for confirmation. See §2.7 of SOLOMON-PLAN.md.

## Forgetting

`/solomon-corpus-forget <path | entity_slug | wiki_page_slug>` triggers a one-tap-confirmed cascade: hard-deletes the entity page, LLM-rewrites mentioning concept/playbook pages, quarantines raw files to `_forgotten/`, redacts or deletes captured_items rows, and removes Pinecone vectors by deterministic ID.
