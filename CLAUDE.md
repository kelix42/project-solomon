# Solomon — Personal Business Brain (Hermes Skill Pack)

## What Solomon is (Hermes-native single-agent in v1; Workers deferred to v2)

Solomon is a Hermes skill pack + 3 OS-supervised Python workers. The Hermes gateway daemon hosts the agent and the cron scheduler. The 3 workers (`plaud-ingest`, `corpus-inbox-watcher`, `pipeline-tick`) handle long-lived processes that can't live inside Hermes' stateless plugin model. SQLite WAL mode lets Hermes and workers share `db/solomon.db` safely.

## Two-phase model (Interview vs Decision — never co-mingled)

- **Interview** (onboarding, mentoring, level-up): ELIZA-style. Mirror, probe, draw out. One question at a time.
- **Decision** (everything else): Load profile, act decisively. No reflection.
- **Utilities** (`solomon-redact`): phase-agnostic. Callable from either.

Every SKILL.md carries `phase: interview | decision | utility`. Onboarding/mentoring entry points only load interview+utility; the orchestrator pipeline only loads decision+utility. CI test asserts.

## How to read this repo (Four Cs map → folders)

- **Context** → `foundation/`, `db/schemas/captured_items.sql`, `context/`, root `MEMORY.md` + `USER.md`
- **Connections** → `connections.md`, `hermes-plugins/`, `workers/`, `references/api-*.md`
- **Capabilities** → `skills/`, `orchestrator/pipeline/`
- **Cadence** → `orchestrator/sleep-cycle/`, `skills/learning/{solomon-mentoring-session,solomon-audit}/`

## Install (bash install.sh — single command; do NOT use `hermes skills install`)

`bash install.sh` is the only supported install entry. `hermes skills install <repo>` is explicitly NOT supported (skips DB init, plugin symlinks, namespace creation, backup-key flow). See `install/README.md`.

## Hard rules (foundation/05-non-negotiables.yaml — read first, always)

Stage 4 of the §2.2.5 pipeline reads this YAML deterministically (no LLM). Each rule has a JSON-logic `condition` evaluated against the event. Violations are unappealable — autonomy level and reasoning cannot override.

## Identity (SOUL.md)

Solomon's voice + decision philosophy + ELIZA-listening rule (interview-phase only). Auto-loaded by Hermes every turn.

## Memory (Hermes auto-loads MEMORY.md + USER.md every turn)

- `MEMORY.md` — agent-curated facts learned across sessions.
- `USER.md` — owner-specific facts (filled progressively from captured_items + foundation YAMLs).

## Captured items + vocabulary (db/schemas/*.sql — interview output, decision input)

- `captured_items.sql` — primary owner-rules store (with confidence, conflicts_with, source_session).
- `vocabulary.sql` — owner's voice as data (SQL-only; not embedded).
- `coverage.sql` — what's been probed, what's still thin.

## Decision-phase pipeline (10 stages: Capture → Salience → … → Action; §2.2.5)

Capture → Salience → Classification → Hard-rule check → Working memory + 5-lane retrieval → System 1 (Sonnet) → System 2 (Opus) → Audit gate (Opus) → Owner-state gate → Action.

Stage 7b (System 1 vs 2 divergence) uses token-Jaccard, NOT embeddings — zero per-event API cost.

## Hermes plugin contract (plugin.yaml + register(ctx); §2.4.6)

Verified API surface only: `register_tool`, `register_hook`, `register_command`, `register_cli_command`, `register_skill`, `dispatch_tool`, `inject_message`. NO `ctx.subscribe / schedule / db / pinecone / telegram / env / logger / invoke_skill / lock / on_unload` — those are aspirational; see §2.4.6 NOT-PROVIDED list. Workers handle long-lived needs.

## Telegram bot (the only owner-facing UI; §2.4.8)

Telegram is **not** a Solomon plugin. It's the Hermes gateway built-in adapter. Configured via `hermes gateway setup` during install. Solomon participates via a Hermes plugin (`solomon-pipeline-injector`) that hooks `pre_llm_call` to classify inbound messages and write `db.events` rows.

## Failure handling (Pinecone down / OpenAI rate-limit / IMAP auth / Hermes crash; §2.4.7)

Each failure mode has a pinned behaviour. Persistent failures → Telegram alert (deduped within 1h windows). Idempotent operations cover crash mid-run.

## Autonomy spectrum (L0–L4 per scope, modulated by owner state; §2.11)

L0 Manual / L1 Suggested / L2 Drafted / L3 Supervised / L4 Autonomous. Per-scope, stored in `db.scope_autonomy`. Promotion: ≥20 events with override <10% AND audit-pass >90%. Demotion: override >25% OR hard-rule violation. Owner state (Whoop) provides per-event ceiling: Green (full), Yellow (downgrade to L2), Red (downgrade to L1).

## Corpus & LLM Wiki (corpus/ — bulk ingestion, Pinecone-backed; raw/wiki/index/log)

Karpathy LLM-Wiki pattern: raw is immutable, wiki is LLM-maintained, both in Pinecone. Wiki outranks raw at retrieval (0.40 vs 0.20 weights). Owner drops files in `corpus/inbox/`; the watcher auto-triggers ingest within 30s. Rules buried in SOPs/emails surface to owner via `proposed_rules` → `mentoring_queue`.

## Knowledge base (Q1 + Q3 distilled)

Filled from foundation/00-industry.yaml + foundation/04-ideal-outcomes.yaml at end of onboarding.

## Voice (references/voice.md + db.vocabulary head)

Top 30 phrases by frequency. Reuse verbatim — never paraphrase.

## Connections (Pinecone, Telegram, Google Workspace required; others optional)

13 rows in `connections.md`. Telegram via Hermes gateway adapter; everything else via `hermes-plugins/` or `workers/`.

## Skills index (Setup / Onboarding / Interview / Corpus / Runtime / Learning / Utilities)

27 total skills, 7 categories. 14 carry-over from v1 + 13 net-new.

## Orchestrator entry points (orchestrator/README.md)

The pipeline runtime lives in `orchestrator/pipeline/`. The 12 sleep-cycle jobs live in `orchestrator/sleep-cycle/`.

## Sleep Cycle (12 jobs incl. J9 corpus-lint + J10 corpus-backup + J11 embed-pending + J12 yaml-reconcile)

Default schedule: `0 3 * * *` owner-local time. Registered via Hermes gateway's `/cron add`. `/solomon-sleep-now` triggers manually.

## Foundation YAMLs (links to all 7 derived summaries)

`foundation/00-industry.yaml` → `06-taxonomy.yaml`. Header on each: `# Derived summary; canonical store is db/schemas/captured_items.sql.`

## Decision log (pointer + canonical format)

`decisions/log.md` — append-only. Format: `## YYYY-MM-DD — Title`, then `**Decision** / **Why** / **Alternatives considered** / **Owner**`.

## Autonomy spectrum (L0–L4)

See `references/autonomy-spectrum.md`.

## Plugins (8 incl. _template + corpus-inbox-watcher). Workers deferred to v2 (see EXPANSIONS.md)

`hermes-plugins/`: 6 plugins (1 template + solomon-pipeline-injector + 4 connection bridges). `workers/`: 4 (1 template + 3 real workers). Telegram is gateway-built-in, not a Solomon plugin.

## Portability (references/portability.md)

`portable: true` SKILL.md flags + the 22 reference docs mean a port to a non-Hermes agent is a documented swap, not a rewrite.

## How you work with me (operator preferences, ELIZA listening rule, phase rules)

- Match the owner's register (terse → terse; storyteller → storyteller).
- Cite captured_items.id when stating an owner rule.
- Surface uncertainty (System 1 vs System 2 divergence).
- ELIZA listening only in interview phase.

## Default Shift (3Ms ritual)

When something feels manual, ask: "to what extent could AI be leveraged here?"
