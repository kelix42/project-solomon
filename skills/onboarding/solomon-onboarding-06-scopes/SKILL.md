---
name: solomon-onboarding-06-scopes
description: Onboarding Session 06 (Scopes). Builds a starter list of departments, operational scopes (jobs sub-agents may be assigned to), and named customer segments via the structured reflective listening loop. Seeds db.scope_autonomy at L0 on day one (per SOLOMON-PLAN.md §2.11; promotion is performance-driven, not set here). Final onboarding session.
category: onboarding
phase: interview
version: 0.3.0
agent: hermes
trigger: ["/solomon-onboarding-06-scopes", "start session 06", "begin scopes session"]
inputs:
  - active_domain (set to "scopes")
  - probe_library/scopes.yaml (keywords, fallbacks, required_fields, probe_style)
  - db.sessions (open or resume the row for this session)
  - db.coverage (rows where domain="scopes")
  - db.captured_items (existing rows whose source_session matches this run)
  - db.clarification_queue (any rows where session_id matches this run)
outputs:
  - db.sessions row (status transitions: active to complete or abandoned)
  - db.captured_items rows (written via solomon-extraction)
  - db.vocabulary rows (written via solomon-vocabulary-capture)
  - db.clarification_queue rows (written via solomon-contradiction-check)
  - db.scope_autonomy rows (one per captured operational_scopes entry, INSERT OR IGNORE with level=0; existing rows are not overwritten)
  - foundation/06-scopes.yaml (rendered by query F3 at session close)
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

# solomon-onboarding-06-scopes

Final session of the 7-session onboarding flow. Builds a starter list of three things into `db.captured_items`:

1. **departments**: the business areas the owner runs (e.g., Sales, Support, Ops).
2. **operational_scopes**: the specific jobs sub-agents may eventually be assigned to. Each scope row's `statement` field stores a JSON object `{"name": "...", "department": "..."}`. `department` defaults to null if unspecified.
3. **customer_segments_named**: the named groups of customers the business serves.

The captured scopes seed `db.scope_autonomy` at level=0 per SOLOMON-PLAN.md §2.11 (every scope starts at L0; promotion is performance-driven via Sleep-Cycle Job 7). Owner autonomy preferences per scope are NOT collected here; they are learned later through the mentoring queue and Job 7 once the owner has real usage context.

This session intentionally drops the five other taxonomy categories from the prior 0.2.0 design (decision types, product buckets, vendor groups, revenue streams, internal jargon). Those are captured passively by `solomon-vocabulary-capture`, the listening agent, and corpus entity allowlisting; they no longer earn a required-field slot in foundation onboarding.

This skill is a thin wrapper over `solomon-interview-engine` plus the post-turn extraction loop, per §6 of SOLOMON-PLAN.md. It adds two structural elements on top of the spec's discovery saturation: a required-fields pass and a closing checkpoint. Same pattern as Session 0.

## Active domain

`scopes`. The interview-engine reads `probe_library/scopes.yaml`, which holds keywords, fallbacks, the three required_fields, and the probe_style block.

## Listening style

All discovery probes and required-field follow-ups follow the seven rules in `probe_library/scopes.yaml::probe_style` and `references/eliza-listening.md`. Summary: use the owner's exact words, do not editorialize, build follow-ups on the echoed phrase, drop filler, keep it short, follow emotional content, pivot plainly when the topic shifts.

## Required fields

Three fields, asked in this order:

| field_id | prompt summary | shape of expected answer |
|---|---|---|
| `departments` | "What are the main areas of the business you run?" | List of department names. |
| `operational_scopes` | "For each area, what jobs would you want a sub-agent to handle?" | List of scope items, each captured row's `statement` is a JSON object `{name, department}`. |
| `customer_segments_named` | "Who are your customers? Are there named groups you treat differently?" | List of segment names with brief descriptions. |

The `operational_scopes` prompt depends on `departments` already being filled. If the owner skips departments, the scope prompt drops the per-department framing and asks for a flat list, with `department=null` on each captured row.

## Five-stage flow

### Stage A. Setup

1. Compute `session_id`. Format: `onboarding-06-YYYY-MM-DD`. If a row already exists for the date, append `-N` (next available integer for the day).
2. Read `db.sessions` for any row matching `session_id LIKE 'onboarding-06-%' AND status='active'`. If one exists, resume that `session_id` instead of opening a new row.
3. If no resumable row exists, INSERT into `db.sessions` with `type='onboarding'`, `domain='scopes'`, `status='active'`, `started_at=NOW()`, `last_activity_at=NOW()`, `turns=0`.
4. Set `active_domain = "scopes"`.
5. Run the probe-library version migration check (per `solomon-coverage-tracker`): if `coverage.library_version_seen < probe_library/scopes.yaml::version` for `domain='scopes'`, write a `mentoring_queue` row (`source='probe_library_update'`, `priority=7`).

### Stage B. Discovery

Delegate per-turn probe selection to `solomon-interview-engine`. After every owner answer:

1. Run `solomon-redact` on the answer text.
2. In parallel, dispatch `solomon-extraction` and `solomon-vocabulary-capture`. Extraction writes 0 or more `captured_items` rows with `embedded_at=NULL` and updates `coverage`. Each row carries the matched keyword in its `keywords` JSON array.
3. Trigger `solomon-contradiction-check` per inserted `captured_items` row. Same-session conflicts go to `clarification_queue`.
4. Increment `db.sessions.turns`; update `last_activity_at`.
5. Ask `solomon-coverage-tracker` for the next sub-topic with `gap_score > 0.4` (lowest gap-score wins). If the tracker returns a session-complete signal (saturation or diminishing returns per SOLOMON-PLAN.md §2.1), exit Stage B and proceed to Stage C.

Discovery is intentionally light here. Most of the value comes from Stage C.

### Stage C. Required-fields pass

1. Run query F1 to get the ordered list of unfilled `required_field` ids for this `session_id`.
2. For each unfilled `field_id` in declaration order:
   a. Ask the field's `prompt` verbatim from `scopes.yaml::required_fields`.
   b. Receive the owner's answer. Run `solomon-redact`, `solomon-extraction`, `solomon-vocabulary-capture` as in Stage B.
   c. The extraction call MUST tag the new `captured_items` row's `keywords` JSON array with `field:<field_id>` so query F1 sees the field as filled and query F4 can count turns.
   d. For `operational_scopes` specifically, each captured scope row's `statement` field stores a JSON object with keys `name` and `department`. `department` defaults to null if the owner did not group scopes by area in their answer.
   e. If the answer is "I don't know", "not applicable", or "decline to answer" (case-insensitive substring or LLM intent classifier), write a `captured_items` row directly: `type='preference'`, `statement=<answer>`, `verbatim_phrase=<answer>`, `keywords=['field:<field_id>']`. Close the field; do not fire a follow-up.
   f. Otherwise, run query F4 to get `turns_on_field`. If `turns_on_field < 2` AND the answer matches one of the field's `follow_up_keywords`, fire ONE follow-up probe from the matched keyword cluster (highest priority unused template, lowest priority number wins). The follow-up's captured rows also carry `field:<field_id>` in keywords.
   g. Hard cap: never spend more than 2 turns on any single `required_field`, regardless of how many keywords match.
3. Re-run F1. Loop until F1 returns an empty list.

### Stage D. Closing checkpoint

1. Run query F2 to pull every `captured_items` row for this `session_id`, ordered by `source_turn` then `id`. Group rows by `required_field_tag` (rows with `field:*` in keywords) versus discovery captures.
2. Present the structured summary in plain markdown. Required-fields block on top (departments, then a scopes table grouped by department, then customer segments), then any discovery captures grouped by sub-topic. End with: "This is the starter list. The agent will use it as the workflow backlog. Anything to confirm, correct, add, or keep talking about?"
3. Map the owner's reply to one of five paths:

| Owner intent | Detection | DB writes | Next |
|---|---|---|---|
| Confirm | LLM intent classifier returns "confirm" (or owner says yes/looks right/approve) | Update `sessions.last_activity_at` | Proceed to Stage E. |
| Correct an item | Owner names a row id, sub-topic, or quotes a statement and provides a revised version | New `captured_items` row via `solomon-extraction` with the same field tag (if any) and a fresh `source_turn`; new row's `conflicts_with` JSON list contains the prior row's id; the prior row stays for history | Loop to step 1 of Stage D (re-run F2). |
| Add a new item | Owner introduces new content not in the summary | Standard `solomon-extraction` insert with appropriate keywords (including a field tag if it falls under a required field) | Loop to step 1 of Stage D. |
| Keep talking on a sub-topic | Owner says "more on X" or asks a follow-up question on a sub-topic | Re-enter Stage B for that sub-topic with a bounded loop (max 3 probes), then return | Loop to step 1 of Stage D. |
| Decline or abandon | Owner says "stop" or signals abandonment | Set `sessions.status='abandoned'`, `abandoned_reason=<reason>`. Auto-mark all `clarification_queue` rows for this `session_id` to `status='dismissed'` with `notes='session abandoned'`. `captured_items` rows are kept | Exit. Do not run F3 and do not write to `db.scope_autonomy`. |

After every correction, re-run F1. If a correction has accidentally left a required field unfilled, re-enter Stage C for that field only.

### Stage E. Close

1. Set `db.sessions.status='complete'`, `completed_at=NOW()`, `last_activity_at=NOW()`.
2. Run query F3 to render `foundation/06-scopes.yaml`. Format follows the standard header convention: a leading comment block, `last_updated`, then a `required_fields` map (one entry per field id with `statement` and `verbatim_phrase`; for `operational_scopes`, the value is a list of `{name, department}` objects parsed from each captured row's JSON statement), then a `discovery` map keyed by sub-topic, then a `voice_samples` list (top vocabulary phrases from this session). DB stays canonical per SOLOMON-PLAN.md §1; the YAML is a derived summary.
3. Write the captured operational_scopes into `db.scope_autonomy`. For each captured scope (parse the JSON statement to get `name`):

   ```sql
   INSERT OR IGNORE INTO scope_autonomy
     (scope, level, since, last_reeval_at, notes)
   VALUES
     (:scope_name, 0, :now_iso, :now_iso, 'source_session: ' || :session_id);
   ```

   `INSERT OR IGNORE` preserves any existing scope rows whose level may already have been promoted by Sleep-Cycle Job 7. Department metadata is NOT written to `scope_autonomy` (the schema does not carry that column); it lives in `captured_items.statement` JSON only. This is the only onboarding session that writes to `db.scope_autonomy`; later changes flow through the mentoring queue and Sleep-Cycle Job 7 per SOLOMON-PLAN.md §2.11.
4. Print: "Session 06 is complete. All 7 onboarding sessions are done. The starter scope list is in `db.scope_autonomy` at L0; promotion is performance-driven from here. Solomon's foundation is set."

## SQL queries

All four use SQLite JSON1. Identical pattern to Session 0; only `:session_id` values and field ids differ. The scope_autonomy write in Stage E.3 is documented inline above.

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

### F3. Render foundation/06-scopes.yaml at session close

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

- **Resume**: if Stage A finds an active row, all subsequent stages operate on that `session_id`. F1, F2, F4 all naturally respect this.
- **Abandon**: triggered by `/solomon-onboarding-abandon` or 30-day inactivity. See Stage D table. Per SOLOMON-PLAN.md §2.7, captured rows are kept; pending clarifications are dismissed; coverage rows are kept. `db.scope_autonomy` is NOT written on abandon.
- **Probe-library version migration**: handled in Stage A.5 (one-time per session start). Does not auto-mass-re-probe.
- **Empty discovery**: if Stage B exits with zero captures, Stage C still runs against required_fields. Each declined field becomes a `type='preference'` row with the literal answer, satisfying F1.
- **No departments given**: `operational_scopes` prompt drops the per-department framing and stores `department=null` on each scope. The owner can group scopes later via the mentoring queue.
- **Existing scope_autonomy row**: `INSERT OR IGNORE` skips any scope already present in `db.scope_autonomy` (whose level may have been promoted to L1 to L4 by Sleep-Cycle Job 7). The captured_items row still records the owner's mention.
- **Final session signaling**: the close print is the explicit "all 7 sessions done" cue for the parent `solomon-onboarding` orchestrator (and for `solomon-profile-loader`, which can fill `SOUL.md` placeholders once this session lands).

## Phase enforcement

`phase: interview` per SOLOMON-PLAN.md §2.11. The orchestrator pipeline (decision phase) cannot load this skill. CI test asserts.
