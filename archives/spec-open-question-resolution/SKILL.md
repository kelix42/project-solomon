---
name: spec-open-question-resolution
description: Walk through and resolve the "Open Questions" section of a technical specification document one question at a time. Use when an owner needs to lock in deferred design decisions on a long-form spec, working through them sequentially and writing each resolution back into the document.
---

# Spec open-question resolution loop

Use this skill when working through a "## Open Questions" or equivalent section of a technical spec with the owner. The job is to convert each open question into a written resolution inside the spec, not just to discuss it.

## When to use

- A spec document on disk has a numbered list of unresolved design decisions.
- The owner wants to work through them and lock decisions into the doc.
- Each resolution requires (a) understanding the tradeoffs, (b) the owner's call, (c) editing the spec.

Concrete example: `/opt/data/cache/documents/solomon-spec.md` Section 13 "Open Questions" — 12 items, resolved one per turn over multiple sessions.

## The loop (per question)

For each open question, follow this order:

1. **Read the relevant spec context.** Don't answer from memory. Use `read_file` or `search_files` to find the section the question affects, plus the question text itself. Skip this only if you just edited the same area in the previous turn.

2. **Present options A/B/C/D.** Always enumerate concrete options first — usually 3 to 4. Include the "defer" option as one of them when defer is genuinely viable. Each option gets one paragraph: what it is, what it costs, what it buys you. Do NOT skip straight to the recommendation; the owner reads the options and uses them as the frame for the decision.

3. **Give the recommendation with reasoning.** Always recommend one option explicitly, even if you'd rather punt. Reasoning should explain *why this option beats the others*, not just why it's good in isolation. Address the strongest counter-argument from the rejected options. Two to four short paragraphs.

4. **Wait for the owner's call.** They may accept, override, ask for more detail, or pick a hybrid. Do not edit the spec until they confirm.

5. **Edit the spec surgically.** Use `patch` (replace mode), not `write_file`. Touch three places:
   - The body section that the resolution affects (add new subsection or update existing prose).
   - Any cross-referenced fields (schema comments, table rows).
   - The Open Questions list itself — replace the original question with `RESOLVED — <one-paragraph summary>. See §X.Y.`

6. **Confirm and report status.** Acknowledge the patch landed, give a status line ("X of N resolved, M remaining"), and tee up the next question with the same options-then-recommendation structure if the owner wants to continue.

## Pitfalls

- **Do not ask "want my take?" before recommending.** Lynx (and most owners working through a spec) wants the recommendation by default. Asking first is friction. Lead with options + recommendation every time.

- **Do not flatten options into prose.** Use a bulleted A/B/C/D list. Owners read the list and pick — burying options in paragraphs forces them to re-extract.

- **Resolutions sometimes answer multiple open questions.** When you resolve question N, scan the rest of the open-questions list for ones that are now answered as a side effect (e.g. "Personal scope hosting" resolved "Should Personal data ever leave the box?"). Mark those RESOLVED too with a back-reference to N.

- **Do not write `write_file` over the spec.** It's long, and a full rewrite risks losing unrelated edits. Always `patch`.

- **Add new subsections rather than overloading existing ones.** If a resolution adds substantial new content (LLM hosting rules, calibration period, retrieval logic), give it its own subsection (§6.2.1, §7.2, §6.2.2, etc.) and reference it from the Open Questions list. Keeps the spec scannable.

- **Schema fields and comments need updating too.** If the resolution changes how a column is interpreted (e.g. `condition` field becomes JSONLogic instead of "machine-checkable predicate"), patch the schema comment AND the field-description table AND add the language section. Three patches, not one.

- **One question per turn unless the owner wants to bundle.** Don't try to resolve three at once — the owner can't react thoughtfully to bundled decisions.

- **Inserting a new top-level section forces renumbering.** If a resolution warrants a new `## N. <Title>` section in the middle of the spec, you must (a) renumber every section after it, (b) renumber their subsections (`### N.1`, `### N.2`, ...), and (c) `search_files` for cross-references like `Section N`, `§N`, `§N.M` and update them. Run a search before editing to know what you're touching. Prefer adding a subsection to an existing section when the content fits — fewer collateral edits.

## Recommended option-table format

When a resolution introduces per-scope or per-band variation, use a markdown table in the spec:

```
| Scope/Band | Threshold/Value | Notes |
|------------|-----------------|-------|
| Admin      | 15              | High-volume, low-stakes. |
| Business   | 20              | Default. |
```

Tables age better than bulleted prose because future edits can add a row without reflowing paragraphs.

## Status tracking

After each resolution, include a one-line status update in the chat reply:
`Status: X of N resolved (#1, #2, ...). M remaining.`

This keeps the owner oriented across sessions when the work spans many turns.

## Post-resolution: the consistency sweep (do not skip this)

After the last open question is resolved, the spec is NOT done. Piecemeal
patching across many sessions reliably introduces seam damage that is
invisible while editing one question at a time. Always offer (and recommend)
a delegated end-to-end consistency review before declaring a v1.0 baseline.

In one real run (Solomon spec, 12 open questions resolved across multiple
sessions) the post-resolution sweep found 18 issues — 8 critical (broken
implementation), 10 minor — including:

- A new table FK pointing at a phantom table name (`rules` instead of the
  actual `rules_of_thumb`). The author confused the conceptual name with
  the schema name when writing the new DDL.
- A `NOT NULL` enum column that the new section started writing a value
  ('unavailable') the enum didn't list. The schema would reject the value.
- Older prose in another section still describing a feature the resolution
  replaced (e.g. "Hard Gate evaluates a Python expression" left over from
  before the JSONLogic resolution).
- A scope/concept renamed in some places but not others ("Business" used
  in 8 sites across the spec, but the §5 taxonomy had it as "Operational").
- Schema columns referenced in newly-added queries that didn't exist on
  the table (`counterparty`, `created_at` when the column is `ts`).
- Two sections specifying contradictory behavior for the same operation
  (§11.3 said `solomon-setup` runs migrations; §12.6 said it must NOT).
- New tables defined inline in a late section (§9.4, §12.6) but never
  added to the canonical §3.1 schema sketch and never created by the
  setup skill — fresh installs would crash on first use.
- New mentoring/event triggers added without expanding the corresponding
  enum column comment in the schema.
- v0.1/v0.2 scope rows in the MVP section saying "feature X deferred to
  v0.2" while a separate section already wired up X.

How to run the sweep:

1. Use `delegate_task` with toolsets `["file", "terminal"]` and a single
   subagent (do NOT batch this — the reviewer needs unified context). Give
   it the spec path and a list of recently-added subsections/tables so it
   knows where the seam damage is most likely. Tell it explicitly NOT to
   modify the file — output a report only.

2. Ask the report to be structured as: CRITICAL ISSUES / MINOR ISSUES /
   SUGGESTED CLEANUPS / CLEAN AREAS, with line numbers and one-line fix
   suggestions per item. The CRITICAL/MINOR/CLEANUP triage is what lets
   you decide what to fix now versus defer.

3. Specifically instruct the reviewer to check:
   - Every cross-reference (`§N.M`, `Section N`, `See §...`) — does the
     target exist with the right title?
   - Every `CREATE TABLE` block — are FKs valid? Are columns referenced
     in prose actually in the schema? Are enums in column comments
     consistent with values written elsewhere?
   - Direct prose contradictions between the new sections and older
     sections about the same operation (setup vs migrate, hosting vs
     local-only, retrieval vs flat windows, etc.).
   - Renamed concepts: search for both old and new names; the rename is
     never complete on the first pass.
   - Renumbering artifacts (gaps in §N.1, §N.2, §N.4 sequences, missing
     TOC entries, stale "Section N" references after an insertion).
   - MVP/scope tables vs. the body of the spec: does the in-scope/out-of-
     scope row for each feature match what the body actually specifies?

4. Apply fixes in batches grouped by section, not by issue number. Each
   batch is one or two `patch` calls; verify after each batch with
   `search_files` against the original problem patterns to confirm
   nothing slipped.

5. After all critical fixes, re-run `search_files` for the original
   problem regexes (broken FK names, stale enum values, removed scope
   names, renamed concepts) to verify the fixes really took. Some
   matches will be legitimate (e.g. an enum that genuinely doesn't
   include the new value because it never sees that state) — read each
   hit before assuming it's a regression.

6. Triage the cleanups bucket explicitly with the owner. Most cleanups
   (TOC, naming consistency, casing) are stylistic, not behavioral, and
   can ship in v1.1 without blocking implementation. Lock the baseline
   on critical+minor; defer cleanups to a polish pass.

## Common seam-damage patterns to watch for proactively

Even before the consistency sweep, when adding a new resolution:

- New table → add DDL to §3.1 (canonical schema), not just inline in the
  resolution section. Then reference §3.1 from the resolution. Keeps the
  schema sketch the single source of truth.
- New enum value → grep the spec for the enum's column comment and update
  it everywhere (column DDL, related audit/log tables, prose descriptions).
- New trigger/event type → check whether any existing column stores that
  type as an enum, and update its comment.
- Renamed concept → run `search_files` for the old name AFTER patching
  the resolution; do not trust that the rename was complete.
- New section that references a column → verify the column exists on
  the table you think it's on, not just in the conceptual model.

## Related skills

When the last open question is resolved, do NOT immediately declare the spec
v1.0. Resolutions added across many turns silently introduce seam damage —
each resolution is internally fine, but the new prose references things that
contradict or don't exist in older sections. Always run a consistency pass
before treating the spec as a baseline.

Use `delegate_task` with `toolsets=["file", "terminal"]` to run a read-only
review subagent. Tell it the spec path, list the recently added subsections
explicitly (so it knows the seam locations), and have it produce a structured
report: CRITICAL ISSUES / MINOR ISSUES / SUGGESTED CLEANUPS / CLEAN AREAS.
Tell it not to edit, just report.

Specific things to instruct the subagent to check for — these are the
failure modes that recur:

1. **Phantom-table FKs.** New subsections that introduce a CREATE TABLE may
   write `REFERENCES rules(id)` when the actual table is `rules_of_thumb`.
   Have the subagent enumerate every `CREATE TABLE` and verify every FK
   target exists.

2. **Invented column references.** New prose may say "ORDER BY created_at"
   or "filter on counterparty" when the schema column is actually `ts`
   and `counterparty` doesn't exist. Have the subagent check every column
   reference in new sections against the §3.1-style schema sketch.

3. **Enum drift.** A NOT NULL column with a documented enum
   (`'pass'|'block'|'flag'`) may get new values added in prose
   (`'unavailable'`) without the schema comment being updated. Same for
   `triggered_by` style columns that grow new trigger sources over time.

4. **Undefined scope/taxonomy names.** New sections may use a top-level
   name (`Business`) that isn't in the taxonomy section (which has
   `Operational`). This compounds because Open Questions back-references
   pick up the wrong name too. Diff every scope/taxonomy reference
   against the canonical list.

5. **Direct prose contradictions.** A new resolution may explicitly
   override an older paragraph (e.g. §12.6 says "schema migrations use
   solomon-migrate, not solomon-setup" while §11.3 still says
   "solomon-setup applies migrations"). Have the subagent search for
   pairs of sections that talk about the same operation.

6. **DDL added in a non-canonical section.** New tables (`rule_conflicts`,
   `meta`) may be defined inline in §9.4 or §12.6 but never added to the
   §3.1 master schema or to §11.2 `solomon-setup` steps. The fresh-install
   path will be missing those tables.

7. **MVP scope drift.** A "deferred to v0.2" line in the MVP section may
   contradict newly-added v0.1 machinery that depends on the deferred
   feature.

After the report comes back, fix critical issues first in batched patches
grouped by section. Re-run a focused `search_files` for each fixed pattern
to verify nothing slipped — e.g. after renaming `Business` to `Operational`,
search for `\bBusiness\b` (word-boundary) to confirm zero stray references
remain. Some legitimate uses of the same word ("business owner" as English
prose) may match — manually exclude those.

Do not run the consistency review on every resolution turn. Once at the end
is correct; per-turn reviews waste tokens and miss cross-resolution drift.

## Related skills

- `solomon-guide` — context for what Solomon is, when the spec questions are about Solomon specifically.
- `writing-plans` — for converting a resolved spec into an implementation plan.
