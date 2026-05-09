---
name: solomon-extraction
category: interview
phase: interview
version: 0.1.0
agent: hermes
trigger: [post-owner-turn-hook]
inputs: [owner_answer_text, current_session_id, current_turn]
outputs: [db.captured_items rows (with embedded_at = NULL), db.coverage updates]
reads_only: false
autonomy_level: L1
depends_on: [solomon-redact]
portable: true
---

# solomon-extraction

Parses each owner answer into `db.captured_items` rows. Called after every owner turn, in parallel with `solomon-vocabulary-capture`. Always preceded by `solomon-redact` (PII pass).

## Process

1. Receive the owner's answer text.
2. Identify each distinct claim: `domain` / `type` / `statement` / `verbatim_phrase` / `example` / `reasoning` / `conditions` (prose) / `keywords` / `confidence`.
3. Write ≥0 rows to `captured_items` with `embedded_at = NULL` (Sleep-Cycle Job 11 will batch-embed).
4. Update `coverage.items_captured`, `coverage.gap_score` (decreases by 1/(probe_count+1) per new item), `coverage.turns_since_last_capture` (reset to 0).
5. Trigger `solomon-contradiction-check` per inserted row.

## Confidence scoring rule

- `stated`: first appearance, no example.
- `repeated`: second+ appearance of an equivalent claim.
- `exemplified`: claim accompanied by a concrete instance in the `example` field.

## LLM prompt outline

Sonnet. Output is structured JSON validating against `db/schemas/captured_items.sql`. System prompt: "Extract first-person owner rules / preferences / values from this text. Format each as JSON matching the captured_items schema. Multiple rows per answer when the owner makes multiple distinct claims."
