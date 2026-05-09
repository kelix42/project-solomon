---
name: solomon-contradiction-check
category: interview
phase: interview
version: 0.1.0
agent: hermes
trigger: [post-extraction-insert]
inputs: [newly inserted captured_items.id, db.captured_items WHERE domain = ...]
outputs: [db.captured_items.conflicts_with updates, db.clarification_queue rows]
reads_only: false
autonomy_level: L1
depends_on: [solomon-extraction]
portable: true
---

# solomon-contradiction-check

Real-time conflict detection. Called after every `solomon-extraction` insert.

## Process

1. Query existing `captured_items` for the same `domain`.
2. For each existing row, check if it logically conflicts with the new row (rule vs exception, principle vs counter-example, value vs preference).
3. If conflict found:
   - Write the conflict's id to `conflicts_with` on both rows (JSON list, append).
   - Write a `clarification_queue` row with `session_id = current`, `captured_id_a` and `captured_id_b`, `suggested_probe` like "Earlier you said X; just now Y. Which wins, and why?".
4. The `solomon-interview-engine` reads `clarification_queue` BEFORE every probe — pending clarifications jump the queue and resolve in the same session.

## Why clarification_queue, not mentoring_queue

`mentoring_queue` is for cross-session items batched for later. Real-time same-session contradictions need immediate resolution while the owner's context is fresh; `clarification_queue` accomplishes that.

## LLM prompt outline

Sonnet. Compare two captured_items rows. Output: `{is_conflict: bool, conflict_type: str, suggested_probe: str}`.
