---
name: solomon-onboarding-status
phase: interview
description: Shows a checklist of Solomon onboarding sessions, which are complete and which still need to be done. Trigger by saying "onboarding status" or "solomon status".
version: 0.1.0
author: Lynx + Sunny---

# Solomon Onboarding Status

Report the status of each onboarding session as a checklist. All 7 sessions (00 through 06) are now DB-backed; the legacy file-existence path has been removed.

## Migrated sessions check (DB-backed)

Applies to Sessions 00, 01, 02, 03, 04, 05, and 06. For each migrated session NN:

A session NN is reported as **complete** only when BOTH conditions hold for the most recent `db.sessions` row whose `session_id LIKE 'onboarding-NN-%'`:

1. `db.sessions.status = 'complete'`, AND
2. Query F1 (defined in the matching `solomon-onboarding-NN-<domain>/SKILL.md`) returns an empty list of unfilled `required_field` ids for that `session_id`.

If a row exists but either condition fails, report **in progress (N remaining)** where N is the length of the F1 result list. Use `(7 remaining)` when no row exists yet.

```sql
-- Pick the most recent attempt for a given session prefix.
-- :prefix is one of 'onboarding-00-%' through 'onboarding-06-%'.
SELECT session_id, status
FROM sessions
WHERE session_id LIKE :prefix
ORDER BY started_at DESC
LIMIT 1;
```

Then run F1 from the matching session skill against `:session_id` to get the unfilled-field count. The required_field id list per session lives in the corresponding probe library YAML's `required_fields` block.

## Output format

Solomon Onboarding (Status)

[ ] / [x] / [in progress (N remaining)] Session 0: Industry & Sector
[ ] / [x] / [in progress (N remaining)] Session 1: Belief System
[ ] / [x] / [in progress (N remaining)] Session 2: Why
[ ] / [x] / [in progress (N remaining)] Session 3: Principles
[ ] / [x] / [in progress (N remaining)] Session 4: Ideal Outcomes
[ ] / [x] / [in progress (N remaining)] Session 5: Non-Negotiables
[ ] / [x] / [in progress (N remaining)] Session 6: Scopes

X/7 complete

If any sessions are incomplete, say: "Say 'start session X' to pick up where you left off."
If all sessions are complete, say: "Onboarding complete. Solomon's foundation is set."
