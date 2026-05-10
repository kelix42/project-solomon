---
name: solomon-onboarding-05-non-negotiables
description: Onboarding Session 05 (Non-Negotiables). Builds the foundation non-negotiables profile via the structured reflective listening loop; runs discovery, a required-fields pass, and a closing checkpoint that includes a hard-rule promotion sub-step; writes captured_items rows and renders foundation/05-non-negotiables.yaml at session close, including the §1 hard-rule schema for any owner-confirmed promotions.
category: onboarding
phase: interview
version: 0.2.0
agent: hermes
trigger: ["/solomon-onboarding-05-non-negotiables", "start session 05", "begin non-negotiables session"]
inputs:
  - active_domain (set to "non-negotiables")
  - probe_library/non-negotiables.yaml (keywords, fallbacks, required_fields, probe_style)
  - db.sessions (open or resume the row for this session)
  - db.coverage (rows where domain="non-negotiables")
  - db.captured_items (existing rows whose source_session matches this run)
  - db.clarification_queue (any rows where session_id matches this run)
  - foundation/05-non-negotiables.yaml (existing rules: block, preserved across renders)
outputs:
  - db.sessions row (status transitions: active to complete or abandoned)
  - db.captured_items rows (written via solomon-extraction)
  - db.vocabulary rows (written via solomon-vocabulary-capture)
  - db.clarification_queue rows (written via solomon-contradiction-check)
  - foundation/05-non-negotiables.yaml (rendered by query F3 at session close, including the §1 rules block with any owner-confirmed promotions appended to the existing rules)
reads_only: false
autonomy_level: L1
depends_on:
  - solomon-redact
  - solomon-interview-engine
  - solomon-extraction
  - solomon-vocabulary-capture
  - solomon-coverage-tracker
  - solomon-contradiction-check
portable: true
---

# solomon-onboarding-05-non-negotiables

Session 05 of the 7-session onboarding flow. Builds the foundation non-negotiables profile (lines around customers, money, employees, partners, vendors, competitors, personal, plus the single line-in-the-sand) into `db.captured_items`. Compiles `foundation/05-non-negotiables.yaml` at session close, INCLUDING the §1 hard-rule schema (`rules:`) for any non-negotiable the owner explicitly promotes during the closing checkpoint.

This skill is a thin wrapper over `solomon-interview-engine` plus the post-turn extraction loop, per §6 of SOLOMON-PLAN.md, with one structural extension to the closing checkpoint and one to the close stage that no other onboarding session has: a per-rule **hard-rule promotion** sub-step. Promoted rules become deterministic Stage 4 hard rules. Skipped rules remain in captured_items only. Promotion is opt-in per rule; the owner must explicitly confirm each one.

## Active domain

`non-negotiables`. The interview-engine reads `probe_library/non-negotiables.yaml`, which holds keywords, fallbacks, the seven required_fields, and the probe_style block.

## Listening style

All discovery probes and required-field follow-ups follow the seven rules in `probe_library/non-negotiables.yaml::probe_style` and `references/eliza-listening.md`. Summary: use the owner's exact words, do not editorialize, build follow-ups on the echoed phrase, drop filler, keep it short, follow emotional content, pivot plainly when the topic shifts.

## Five-stage flow

### Stage A. Setup

1. Compute `session_id`. Format: `onboarding-05-YYYY-MM-DD`. If a row already exists for the date, append `-N` (where N is the next available integer for the day).
2. Read `db.sessions` for any row matching `session_id LIKE 'onboarding-05-%' AND status='active'`. If one exists, resume that `session_id` instead of opening a new row.
3. If no resumable row exists, INSERT into `db.sessions` with `type='onboarding'`, `domain='non-negotiables'`, `status='active'`, `started_at=NOW()`, `last_activity_at=NOW()`, `turns=0`.
4. Set `active_domain = "non-negotiables"`.
5. Run the probe-library version migration check (per `solomon-coverage-tracker`): if `coverage.library_version_seen < probe_library/non-negotiables.yaml::version` for `domain='non-negotiables'`, write a `mentoring_queue` row (`source='probe_library_update'`, `priority=7`).
6. Initialize an empty in-session list `pending_promotions` to collect any hard-rule confirmations from Stage D.

### Stage B. Discovery

Delegate per-turn probe selection to `solomon-interview-engine`. After every owner answer:

1. Run `solomon-redact` on the answer text.
2. In parallel, dispatch `solomon-extraction` and `solomon-vocabulary-capture`. Extraction writes 0 or more `captured_items` rows with `embedded_at=NULL` and updates `coverage`. Each row carries the matched keyword in its `keywords` JSON array.
3. Trigger `solomon-contradiction-check` per inserted `captured_items` row. Same-session conflicts go to `clarification_queue`.
4. Increment `db.sessions.turns`; update `last_activity_at`.
5. Ask `solomon-coverage-tracker` for the next sub-topic with `gap_score > 0.4` (lowest gap-score wins). If the tracker returns a session-complete signal (saturation or diminishing returns per SOLOMON-PLAN.md §2.1), exit Stage B and proceed to Stage C.

### Stage C. Required-fields pass

1. Run query F1 to get the ordered list of unfilled `required_field` ids for this `session_id`.
2. For each unfilled `field_id` in declaration order:
   a. Ask the field's `prompt` verbatim from `non-negotiables.yaml::required_fields`.
   b. Receive the owner's answer. Run `solomon-redact`, `solomon-extraction`, `solomon-vocabulary-capture` as in Stage B.
   c. The extraction call MUST tag the new `captured_items` row's `keywords` JSON array with `field:<field_id>` so query F1 sees the field as filled and query F4 can count turns.
   d. If the answer is "I don't know", "not applicable", or "decline to answer" (case-insensitive substring or LLM intent classifier), write a `captured_items` row directly: `type='preference'`, `statement=<answer>`, `verbatim_phrase=<answer>`, `keywords=['field:<field_id>']`. Close the field; do not fire a follow-up; do not offer hard-rule promotion in Stage D for declined fields.
   e. Otherwise, run query F4 to get `turns_on_field`. If `turns_on_field < 2` AND the answer matches one of the field's `follow_up_keywords`, fire ONE follow-up probe from the matched keyword cluster (highest priority unused template, lowest priority number wins). The follow-up's captured rows also carry `field:<field_id>` in keywords.
   f. Hard cap: never spend more than 2 turns on any single `required_field`, regardless of how many keywords match.
3. Re-run F1. Loop until F1 returns an empty list.

### Stage D. Closing checkpoint

The standard closing checkpoint runs first (same as every other migrated onboarding session), then a Session-05-only **hard-rule promotion sub-step** runs against the captured non-negotiables.

#### D.1. Standard summary review

1. Run query F2 to pull every `captured_items` row for this `session_id`, ordered by `source_turn` then `id`. Group rows by `required_field_tag` (rows with `field:*` in keywords) versus discovery captures.
2. Present the structured summary in plain markdown. Required-fields block on top, then discovery captures grouped by sub-topic. End with: "Anything to confirm, correct, add, or keep talking about?"
3. Map the owner's reply to one of five paths:

| Owner intent | Detection | DB writes | Next |
|---|---|---|---|
| Confirm | LLM intent classifier returns "confirm" (or owner says yes/looks right/approve) | Update `sessions.last_activity_at` | Proceed to Stage D.2 (hard-rule promotion). |
| Correct an item | Owner names a row id, sub-topic, or quotes a statement and provides a revised version | New `captured_items` row via `solomon-extraction` with the same field tag (if any) and a fresh `source_turn`; new row's `conflicts_with` JSON list contains the prior row's id; the prior row stays for history | Loop to step 1 of Stage D.1 (re-run F2). |
| Add a new item | Owner introduces new content not in the summary | Standard `solomon-extraction` insert with appropriate keywords (including a field tag if it falls under a required field) | Loop to step 1 of Stage D.1. |
| Keep talking on a sub-topic | Owner says "more on X" or asks a follow-up question on a sub-topic | Re-enter Stage B for that sub-topic with a bounded loop (max 3 probes), then return | Loop to step 1 of Stage D.1. |
| Decline or abandon | Owner says "stop" or signals abandonment | Set `sessions.status='abandoned'`, `abandoned_reason=<reason>`. Auto-mark all `clarification_queue` rows for this `session_id` to `status='dismissed'` with `notes='session abandoned'`. `captured_items` rows are kept (the owner's words remain valid) | Exit. Do not run F3 and do not run D.2. |

After every correction, re-run F1. If a correction has accidentally left a required field unfilled, re-enter Stage C for that field only.

#### D.2. Hard-rule promotion (Session 05 only)

For each captured non-negotiable in this session (rows whose `keywords` JSON array contains `field:never_do_*` or `field:line_in_the_sand`, plus any discovery-captured rule with type='rule' and domain='non-negotiables'):

1. Present the rule prose to the owner: "You said: '<verbatim_phrase>'. Want me to enforce this as a hard rule that blocks me automatically?"
2. If owner says no or skip: do nothing. The rule stays in `captured_items` only. Move to next.
3. If owner says yes:
   a. Solomon drafts a JSON-logic `condition` and a matching `on_violate` block via Sonnet. The drafter is given the captured row's `statement`, `verbatim_phrase`, and `domain` and produces:
      ```yaml
      condition:
        and:
          - { "==": [{ var: "event.classification.scope" }, "<scope>"] }
          - { ...predicate that captures the rule's intent... }
      on_violate:
        action: REJECT
        explanation: "<plain English why this would block, including a pointer to captured_items.id>"
      ```
   b. Show the draft to the owner. Owner choices: confirm / edit / skip.
   c. On confirm: append `{id: <captured_items.id>, statement, domain: 'non-negotiables', condition, on_violate}` to the in-session `pending_promotions` list. Mark the captured row by appending `hard_rule_promoted` to its `keywords` JSON array (so future re-renders know this row is promoted).
   d. On edit: owner provides revised JSON-logic; same flow.
   e. On skip: do nothing.
4. After all candidates are walked, present a brief "Promoted N rules" summary and ask "Ready to close?"

The drafter's accuracy is not statically testable. Validation is empirical against the next pipeline events; bad drafts will surface as override-rate spikes per SOLOMON-PLAN.md §2.11 autonomy demotion thresholds.

### Stage E. Close

1. Set `db.sessions.status='complete'`, `completed_at=NOW()`, `last_activity_at=NOW()`.
2. Run query F3 to render `foundation/05-non-negotiables.yaml`. The render is a special two-part operation:
   a. Read the existing `foundation/05-non-negotiables.yaml` (if it exists). Parse YAML. Preserve the existing `rules:` block (rules from prior sessions, mentoring promotions, or hand-edits). Per SOLOMON-PLAN.md §1, hand-edits trigger a `mentoring_queue` row with `source='yaml_hand_edit'`, `priority=5`; that reconciliation is handled by Sleep-Cycle Job 12, not by this skill.
   b. Replace the prose blocks (`last_updated`, `required_fields`, `discovery`, `voice_samples`) using the standard F3 sets.
   c. Append every entry in `pending_promotions` to the `rules:` block. Each entry uses the §1 schema: `id`, `statement`, `domain`, `condition`, `on_violate`.
   d. Write the merged file back to `foundation/05-non-negotiables.yaml` with the standard header comment block preserved.
3. Print: "Session 05 is complete. Ready to start Session 06?"

## SQL queries

All four use SQLite JSON1 (already a baseline dependency for the keywords arrays). F1, F2, F4 are identical to Session 0; only `:session_id` values differ. F3 is extended for Session 05 (see Stage E above).

### F1. Unfilled required_field ids for a session

```sql
SELECT COUNT(*) AS filled
FROM captured_items, json_each(captured_items.keywords) AS k
WHERE captured_items.source_session = :session_id
  AND k.value = 'field:' || :field_id;
```

### F2. Closing checkpoint summary

```sql
SELECT
  ci.id, ci.domain, ci.type, ci.statement, ci.verbatim_phrase, ci.example,
  ci.confidence, ci.source_turn, ci.keywords,
  (
    SELECT k.value FROM json_each(ci.keywords) AS k
    WHERE k.value LIKE 'field:%' LIMIT 1
  ) AS required_field_tag
FROM captured_items AS ci
WHERE ci.source_session = :session_id
ORDER BY ci.source_turn ASC, ci.id ASC;
```

### F3. Render foundation/05-non-negotiables.yaml at session close (Session 05 special case)

The standard three sets feed the prose blocks. The `rules:` block is preserved from the existing file and extended with `pending_promotions` (Python composes the merge):

```sql
-- Set 1: required-field captures (latest turn wins per field).
SELECT k.value AS field_tag, ci.statement, ci.verbatim_phrase, ci.confidence, ci.source_turn
FROM captured_items AS ci, json_each(ci.keywords) AS k
WHERE ci.source_session = :session_id AND k.value LIKE 'field:%'
ORDER BY ci.source_turn DESC;

-- Set 2: discovery captures (no field tag).
SELECT ci.statement, ci.verbatim_phrase, ci.example, ci.reasoning, ci.confidence, ci.keywords, ci.source_turn
FROM captured_items AS ci
WHERE ci.source_session = :session_id
  AND NOT EXISTS (SELECT 1 FROM json_each(ci.keywords) AS k WHERE k.value LIKE 'field:%')
ORDER BY ci.source_turn ASC;

-- Set 3: vocabulary samples linked to this session.
SELECT v.phrase, v.frequency, v.type
FROM vocabulary AS v
WHERE v.first_seen IN (SELECT id FROM captured_items WHERE source_session = :session_id)
ORDER BY v.frequency DESC, v.last_seen DESC LIMIT 30;

-- Set 4 (Session 05 only): captured non-negotiables that have been promoted in this session.
-- These are the rows whose keywords array contains 'hard_rule_promoted' (added in Stage D.2.c).
SELECT ci.id, ci.statement, ci.verbatim_phrase, ci.domain
FROM captured_items AS ci, json_each(ci.keywords) AS k
WHERE ci.source_session = :session_id
  AND k.value = 'hard_rule_promoted';
```

### F4. Turns spent on a specific required field within a session

```sql
SELECT COUNT(DISTINCT ci.source_turn) AS turns_on_field
FROM captured_items AS ci, json_each(ci.keywords) AS k
WHERE ci.source_session = :session_id
  AND k.value = 'field:' || :field_id;
```

Returns 0, 1, or 2. The skill enforces the hard cap by checking this value before firing any follow-up.

## Edge cases

- **Resume**: if Stage A finds an active row, all subsequent stages operate on that `session_id`. F1, F2, F4 all naturally respect this. The in-session `pending_promotions` list is rebuilt on resume by querying for rows with `hard_rule_promoted` in their keywords array AND source_session matching.
- **Abandon**: triggered by `/solomon-onboarding-abandon` or 30-day inactivity. See Stage D.1 table. Per SOLOMON-PLAN.md §2.7, captured rows are kept; pending clarifications are dismissed; coverage rows are kept. `pending_promotions` is discarded; nothing is written to `foundation/05-non-negotiables.yaml`.
- **Probe-library version migration**: handled in Stage A.5 (one-time per session start). Does not auto-mass-re-probe.
- **Empty discovery**: if Stage B exits with zero captures (owner declines every probe), Stage C still runs against required_fields. Each field that the owner declines becomes a `type='preference'` row with the literal answer, satisfying F1. Declined required fields are not offered for hard-rule promotion in Stage D.2.
- **Existing hand-edited rules**: the F3 render preserves any `rules:` entries already in `foundation/05-non-negotiables.yaml`. Reconciliation between hand-edits and DB is handled by Sleep-Cycle Job 12 (`yaml-reconcile`) per SOLOMON-PLAN.md §1.
- **Promotion on later mentoring**: rules captured in this session that the owner does NOT promote here can still be promoted later via `solomon-mentoring-session` when a `corpus_rule_proposal` queue item references them.

## Phase enforcement

`phase: interview` per SOLOMON-PLAN.md §2.11. The orchestrator pipeline (decision phase) cannot load this skill. CI test asserts.
