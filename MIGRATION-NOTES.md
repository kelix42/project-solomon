# Migration notes

## 2026-05-10. Session 0 (Industry) migration, Style A to Style B

This file records out-of-scope inconsistencies surfaced during the Session 0 migration. Each entry is a separate slice of future work, not part of this PR.

### Files changed in this slice

| Path | Change |
|---|---|
| `skills/interview/solomon-interview-engine/probe_library/industry.yaml` | New file. First foundation-topic probe library. Includes `probe_style` block (the seven listening rules) and `required_fields` block (seven entries). |
| `skills/onboarding/solomon-onboarding-00-industry/SKILL.md` | Full rewrite. Style B frontmatter, five-stage flow (setup, discovery, required-fields pass, closing checkpoint, close). Removes every `/opt/data/` reference. |
| `skills/onboarding/solomon-onboarding-status/SKILL.md` | Surgical edit. Session 0 row uses DB-backed check; Sessions 1 to 6 unchanged with explicit comment. Pre-existing em dash in frontmatter description fixed (file was touched, global rule applies). |
| `tests/test_session_0_migration.py` | New file. 12 test cases. All pass. |
| `references/eliza-listening.md` | Extended with the seven MIRRORING STYLE rules and three-way examples. The canonical copy lives in `industry.yaml::probe_style`; this is the human-readable reference. Pre-existing em dash on line 9 fixed. |

### Out-of-scope items (recorded for future slices)

1. **Style A onboarding skills still pointing at `/opt/data/`**. The same migration must be applied to:
   - `skills/onboarding/solomon-onboarding/SKILL.md` (parent meta-orchestrator)
   - `skills/onboarding/solomon-onboarding-01-belief-system/SKILL.md`
   - `skills/onboarding/solomon-onboarding-02-why/SKILL.md`
   - `skills/onboarding/solomon-onboarding-03-principles/SKILL.md`
   - `skills/onboarding/solomon-onboarding-04-ideal-outcomes/SKILL.md`
   - `skills/onboarding/solomon-onboarding-05-non-negotiables/SKILL.md`
   - `skills/onboarding/solomon-onboarding-06-taxonomy/SKILL.md`
   - Each needs Style B frontmatter, the five-stage flow, and a matching probe library YAML (`belief-system.yaml`, `why.yaml`, `principles.yaml`, `ideal-outcomes.yaml`, `non-negotiables.yaml`, `scopes.yaml`) carrying its own `required_fields` and `probe_style` blocks.
   - Once Sessions 1 to 6 migrate, the legacy file-existence path in `solomon-onboarding-status` should be removed entirely.

2. **`solomon-mentoring-session` (Style A)** writes to `/opt/data/solomon/mentoring/` and uses static question lists. Needs migration to delegate to `solomon-interview-engine`, write to `db.captured_items`, and read the mentoring queue ordered by priority per SOLOMON-PLAN.md §2.7.

3. **`solomon-listening-agent` (Style A)** uses ad-hoc memory tags (`[solomon-learning]`) instead of going through the redact-extraction-vocabulary pipeline. Needs reshape so transcripts feed the same write surface as the rest of the interview side.

4. **`SOUL.md`** still has unresolved placeholders: `{{owner_name}}`, `{{business_name}}`, `{{principle_1..5}}`, `{{top_vocabulary_30}}`, `{{voice_samples}}`. Filled by `solomon-profile-loader` at end-of-onboarding (per SOLOMON-PLAN.md §1). The brief listening rule in SOUL.md should also be updated to point to `references/eliza-listening.md` for the full seven rules.

5. **`USER.md`** is template-only. Will populate via Sleep-Cycle Job 12 (`yaml-reconcile`) after the first onboarding pass.

6. **`references/voice.md`** is template-only with empty fenced blocks. Will populate from Q0 of `intake.md` or from the first vocabulary captures.

7. **`intake.md` instruction is wrong**. Line 96 tells the owner to run `hermes -s solomon-onboarding -q "ingest intake.md"`. The current `solomon-onboarding` parent skill is Style A and has no extraction logic. After the parent migrates, this instruction needs to actually trigger the redact + extract + vocabulary + contradiction-check pipeline per Q section.

8. **`probe_library/README.md` schema docs** do not yet describe the new top-level keys `probe_style` and `required_fields`. The keys are forward-compatible (existing readers ignore unknown keys), but the README should be updated when the next foundation-topic probe library lands. The `industry.yaml` header comment documents both keys inline as an interim measure.

9. **Existing operational probe libraries** (`pricing.yaml`, `hiring.yaml`, `customer.yaml`, `ops.yaml`, `vendor.yaml`, `finance.yaml`) contain em dashes in template strings and one `"You said"` opener (in `pricing.yaml`). These pre-date the no-em-dash rule and the chatbot-pattern lint. Plan: when each operational domain gets a follow-up touch, normalize the templates and add a `probe_style` block. Out of scope for this slice (the migration prompt explicitly forbids modifying anything under `skills/interview/`).

10. **GitHub repo description** (set during initial push earlier today) contains em dashes. Cosmetic. Update via `gh repo edit kelix42/project-solomon --description "..."` next time the repo is touched.

11. **`description:` field in Style B frontmatter**. The §6 template in SOLOMON-PLAN.md does not include `description:`. Existing Style B skills (`solomon-extraction`, `solomon-vocabulary-capture`, `solomon-coverage-tracker`, `solomon-contradiction-check`, `solomon-interview-engine`, `solomon-profile-loader`, `solomon-level-up`, `solomon-redact`) lack it. The Session 0 migrated skill adds it because IDE linting flagged the omission and the field is additive (Hermes ignores unknown frontmatter). Recommend backfilling `description:` to all Style B skills as a one-line touch in the next slice.

12. **VS Code agent linter warnings**. The IDE (`vscode-anthropic-claude` extension) lints SKILL.md frontmatter against its own agent schema (`argument-hint`, `compatibility`, `context`, `description`, etc.). Hermes skills use a different schema (`name`, `category`, `phase`, `version`, `agent`, `trigger`, `inputs`, `outputs`, `reads_only`, `autonomy_level`, `depends_on`, `portable`). The warnings are advisory; both schemas tolerate unknown fields. No action needed unless a future direction merges the two formats.

### Note on SOLOMON-PLAN.md

The spec landed at the repo root (`SOLOMON-PLAN.md`, 1350 lines) during this migration. Section numbers cited throughout the migration prompt (§0, §1, §2.1, §2.6, §2.7, §6, §2.11) map cleanly to that file. The file is currently untracked by git; it will be committed alongside this migration.

### Listening style propagation

Per the user's directive to reflect the modern reflective listening recommendations wherever necessary, the seven MIRRORING STYLE rules now live in:

- `skills/interview/solomon-interview-engine/probe_library/industry.yaml::probe_style` (canonical copy, ships with each future probe library file)
- `references/eliza-listening.md` (human-readable reference with three-way examples and required-field guidance)
- `skills/onboarding/solomon-onboarding-00-industry/SKILL.md` (skill body has a "Listening style" section pointing to both)

Future migration slices should add the same `probe_style` block to every new probe library YAML and update the corresponding wrapper SKILL.md to point at `references/eliza-listening.md`.

## 2026-05-10. Session 06 refactor: Taxonomy to Scopes

Reframed the final onboarding session from a 7-required-field taxonomy elicitation to a 3-required-field scopes elicitation. The five dropped fields (decision_type_taxonomy, product_or_service_categories, vendor_or_supplier_categories, revenue_streams_named, internal_jargon_terms) are captured passively by `solomon-vocabulary-capture`, the listening agent, and corpus entity allowlisting.

What survives:

| field | shape | downstream consumer |
|---|---|---|
| `departments` | list of department names | `captured_items` only (no scope_autonomy column for department) |
| `operational_scopes` | each captured row's `statement` is JSON `{name, department}` | `captured_items` plus `db.scope_autonomy` (one INSERT OR IGNORE row per scope at level=0) |
| `customer_segments_named` | list of named segments | `captured_items` plus retrieval Lane 3 entity anchors |

Files renamed:

- `skills/onboarding/solomon-onboarding-06-taxonomy/` to `skills/onboarding/solomon-onboarding-06-scopes/`
- `skills/interview/solomon-interview-engine/probe_library/taxonomy.yaml` to `scopes.yaml` (full content rewrite, not a simple rename)
- `foundation/06-taxonomy.yaml` to `foundation/06-scopes.yaml` (header retitled)

Stage E.3 is a structural addition: Session 06 is the only onboarding session that writes to `db.scope_autonomy`. The write is `INSERT OR IGNORE INTO scope_autonomy (scope, level, since, last_reeval_at, notes) VALUES (?, 0, ?, ?, 'source_session: <sid>')` per captured scope. Existing rows whose `level` has already been promoted by Sleep-Cycle Job 7 are preserved. Per SOLOMON-PLAN.md §2.11, every scope starts at L0; promotion is performance-driven, not chosen at onboarding. Owner autonomy preferences per scope are deliberately deferred to mentoring and Job 7.

Tests updated:

- `SESSION_CONFIGS["06"]` rewritten (domain, foundation_path, skill_dir, yaml_name, required_field_ids).
- `test_session_cannot_complete_without_required_fields` and `test_status_skill_reports_in_progress` generalized from hard-coded counts to `len(fids) - 1` so they handle any session with at least 2 required_fields.
- New non-parametrized `test_session_06_writes_scope_autonomy` validates the four properties of Stage E.3: new scopes at level=0, department-null scopes still written, existing rows preserved by INSERT OR IGNORE, idempotent re-runs.
