# Solomon Spec v2 — Hermes-Native Personal Business Brain

## Context

Solomon is a personal business brain that learns its owner well enough to make routine decisions for them. The repo we are about to build at `/Users/kekeliefu/Documents/Project Solomon/solomon/` consolidates four pre-existing sources of design under [Project Solomon/Support Information/](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/):

1. **Solomon's own foundation** — vision doc [Solomon — A personal business brain.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Solomon%20—%20A%20personal%20business%20brain.md), centerpiece [orchestrator-design-original.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/orchestrator-design-original.md) (~205KB runtime), frozen [solomon-spec-v1.0.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/solomon-spec-v1.0.md), [12-DECISIONS-RESOLVED.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/12-DECISIONS-RESOLVED.md), [MEMORY-ENTRIES.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/MEMORY-ENTRIES.md), and 16 existing skills under [solomon-skills/](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/solomon-skills/).
2. **Hermes agent reference** — [Hermes-Agent/](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Hermes-Agent/). Defines Hermes' primitives: identity in `SOUL.md`, agent-curated memory in `MEMORY.md` + `USER.md` (auto-injected every turn), single-file markdown skills, Python plugins (`plugin.yaml` + `__init__.py`), MCP bridges, `.env` at `~/.hermes/.env`. Pinecone is an installable Hermes skill.
3. **Nate Herkai's AIS-OS** — [Nate Support/AIS-OS/](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/). Provides organizational discipline (flat naming, root [CLAUDE.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/CLAUDE.md), `context/` + `references/` + `decisions/log.md` + `archives/` + skills folder, [aios-intake.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/aios-intake.md), [connections.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/connections.md)) plus the **Three Ms** (Mindset → Method → Machine) and **Four Cs** (Context → Connections → Capabilities → Cadence) frameworks.
4. **ELIZA reference** — [ELIZA.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/ELIZA/ELIZA.md) Wikipedia clipping plus [MAD-SLIP_transcription.txt](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/ELIZA/MAD-SLIP_transcription.txt) (the original 1966 source code). Solomon is not a chatbot; ELIZA's *interview technique* — keyword-triggered probing, exact-word echoing, decomposition, and ranked fallbacks — is borrowed for the structured **interview engine** that captures the owner's decision-making patterns during onboarding and mentoring.
5. **Karpathy's LLM Wiki idea** — gist at <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>. A 3-layer pattern: **raw sources** (immutable docs the LLM reads but never edits), **wiki** (LLM-generated markdown entity/concept pages with cross-references and a maintained `index.md` + append-only `log.md`), and **schema** (a config file describing conventions). Three operations: ingest, query, lint. The compounding insight: pre-compiled wiki pages mean answers don't get re-derived from scratch on every query the way pure RAG does. Solomon adapts this for **Pinecone-backed bulk ingestion** (§2.3).

**Goal**: produce a single GitHub-publishable repo that runs as a Hermes skill pack, ships with a structured ELIZA-derived interview engine, drops the owner straight into Session 0 after a one-command install, uses Pinecone as canonical vector memory, and treats Google Workspace (Gmail + Calendar + Drive) as first-class. Solomon v1 runs as the Hermes gateway daemon plus three OS-supervised Python workers (§2.4.6.5: `plaud-ingest`, `corpus-inbox-watcher`, `pipeline-tick`); Hermes **sub-agents** spawned via `delegate_task` are deferred to v2 (see EXPANSIONS.md). The Solomon "workers" of v1 are not Hermes sub-agents — they are separate long-lived Python services sharing SQLite with Hermes.

**User-confirmed scope** (locked):
- **Location**: new sibling folder at `/Users/kekeliefu/Documents/Project Solomon/solomon/`. Existing `Support Information/` stays as the archive.
- **Build depth**: full scaffold *plus* authored content for every doc.
- **Canonical agent runtime**: **Hermes**.
- **Distribution**: GitHub repo + `bash install.sh` (single command). Auto-launches Session 0.
- **Vector memory**: Pinecone, with OpenAI `text-embedding-3-large` (3072 dims) as the v1 embedding model.
- **Integrations**: Telegram (via Hermes' built-in gateway adapter, not a Solomon plugin), Google Workspace (Gmail + Calendar + Drive/Docs/Sheets via MCP — Hermes plugin), Pinecone (Hermes plugin), Whoop (Hermes plugin), Plaud (Solomon worker, IMAP), workflow orchestrator (n8n or make.com — Hermes plugin), plus `_template-hermes-plugin/` and `_template-worker/` scaffolds for any other tool.
- **Interview architecture**: ELIZA-derived. Two-phase split — interview phase (extraction, used in onboarding + mentoring only) vs decision phase (act on owner's behalf, no probing).
- **Bulk corpus ingestion**: Karpathy LLM-Wiki adapted for Pinecone. Owner drops files into `corpus/inbox/`; a watchdog plugin auto-triggers ingest within ~30s; ingest writes raw + wiki, embeds, logs.

---

## §0. Two-Phase Architecture (Interview vs Decision)

The most consequential design decision in this spec. Two phases, cleanly separated, never co-mingled.

| Phase | When | Skills loaded | Reads from | Writes to |
|---|---|---|---|---|
| **Interview** | Onboarding (Sessions 0–6) + scheduled mentoring + `/solomon-level-up` | `solomon-interview-engine` (orchestrator) + `solomon-extraction` + `solomon-vocabulary-capture` + `solomon-coverage-tracker` + `solomon-contradiction-check` (+ `solomon-redact` from utilities) | `probe_library/`, `db.coverage`, `db.captured_items`, `db.clarification_queue`, `db.vocabulary`, `db.sessions`, `corpus/schema.md` (entity_allowlist) | `db.captured_items`, `db.coverage`, `db.vocabulary`, `db.clarification_queue`, `db.sessions`, `foundation/NN-*.yaml` (derived summaries) |
| **Decision** | Real-time owner-on-behalf actions, listening to Plaud, daily ops, corpus maintenance, audit | `solomon-profile-loader` (entry) + listening-agent + corpus skills + audit + decision-log | `db.captured_items`, `db.vocabulary`, `db.ingested_files`, `db.wiki_vectors`, `db.sessions`, `db.events`, `db.working_memory`, `db.scope_autonomy`, `db.biometrics`, `foundation/NN-*.yaml`, `corpus/wiki/`, hot memory | `decisions/log.md`, `MEMORY.md`, `USER.md`, `corpus/raw/`, `corpus/wiki/`, `db.ingested_files`, `db.wiki_vectors`, `db.events`, `db.working_memory`, `db.scope_autonomy`, action outputs |

**Rule**: ELIZA-style reflection, probing, and exact-word echoing happen *only* in the interview phase. Decision-phase skills load the populated profile and act decisively — they do not reflect, do not probe. The two skill sets share no code paths; they share only the data store.

**Utilities are phase-agnostic.** Skills with `phase: utility` may be invoked from either phase. Currently only `solomon-redact` is a utility. Utilities never probe, never reflect, and never write to interview/decision-only stores beyond their declared output. They exist so cross-cutting concerns (PII redaction, in this case) can be tested and audited as one skill rather than duplicated.

Enforced at the skill level: every SKILL.md carries `phase: interview`, `phase: decision`, or `phase: utility`. Onboarding/mentoring entry points only load `phase: interview` and `phase: utility` skills; the orchestrator pipeline only loads `phase: decision` and `phase: utility` skills. Utilities never load other utilities. CI tests assert no skill loads under the wrong phase.

---

## §1. Storage — SQLite Schemas and Foundation YAMLs

SQLite is Solomon's canonical structured store; the 7 foundation YAMLs are derived summaries rendered from `captured_items` at session close. YAML alone cannot support contradiction-link queries, vocabulary-frequency joins, or coverage tracking. SQL store has confidence scoring, source tracking, and timestamps the YAMLs cannot.

### Interview-phase tables (this section)

**`captured_items.sql`** — primary owner-rules store
```
id                  TEXT PRIMARY KEY        -- ulid
domain              TEXT NOT NULL           -- pricing | hiring | ops | customer | vendor | finance | …
type                TEXT NOT NULL           -- rule | exception | trigger | preference | value | story
statement           TEXT NOT NULL           -- normalized rule/value
verbatim_phrase     TEXT                    -- owner's exact wording (preserve casing/punctuation)
example             TEXT                    -- a real instance, if given
reasoning           TEXT                    -- why the owner does it this way
conditions          TEXT                    -- when this applies (JSON list of clause strings)
conflicts_with      TEXT                    -- JSON list of captured_items.id this contradicts
confidence          TEXT NOT NULL           -- stated | repeated | exemplified
source_session      TEXT NOT NULL           -- onboarding-NN-domain | mentoring-YYYY-MM-DD
source_turn         INTEGER NOT NULL        -- nth question of that session
keywords            TEXT NOT NULL           -- JSON list, lowercase, used for retrieval
embedded_at         TEXT                    -- ISO 8601; null = pending Sleep-Cycle Job 11
created_at          TEXT NOT NULL
updated_at          TEXT NOT NULL
INDEX idx_domain   (domain)
INDEX idx_keywords (keywords)
INDEX idx_source   (source_session, source_turn)
INDEX idx_embedded (embedded_at) WHERE embedded_at IS NULL
```

**`coverage.sql`** — what's been probed, what's still thin
```
id                       INTEGER PRIMARY KEY AUTOINCREMENT
domain                   TEXT NOT NULL
sub_topic                TEXT NOT NULL           -- e.g., domain=pricing, sub_topic=after-hours
probe_count              INTEGER NOT NULL DEFAULT 0
items_captured           INTEGER NOT NULL DEFAULT 0
gap_score                REAL NOT NULL DEFAULT 1.0    -- 1.0 = untouched, 0.0 = saturated
last_probed              TEXT                          -- ISO 8601, null if never
last_probed_version      TEXT                          -- semver of probe library at last probe
library_version_seen     TEXT                          -- highest probe-library version observed
turns_since_last_capture INTEGER NOT NULL DEFAULT 0    -- for session-complete heuristic
notes                    TEXT
UNIQUE (domain, sub_topic)
```

**`vocabulary.sql`** — owner's voice as data (SQL-only; not embedded)
```
-- Normalization key for `phrase`: lowercase, strip surrounding punctuation, collapse internal whitespace,
-- strip leading/trailing articles (the/a/an). NO stemming. Hyphens preserved as-is.
-- Vocabulary is queried via SQL frequency/recency lookups and used for verbatim probe-template filling.
-- It is NOT embedded into Pinecone — there is no semantic-search use case for individual phrases.
phrase              TEXT PRIMARY KEY
verbatim_examples   TEXT NOT NULL           -- JSON list of original-cased instances
type                TEXT NOT NULL           -- np | vp | idiom | metaphor | stock_expression
frequency           INTEGER NOT NULL DEFAULT 1
first_seen          TEXT NOT NULL           -- captured_items.id
last_seen           TEXT NOT NULL
domains             TEXT                    -- JSON list of domains where it appeared
aliases             TEXT                    -- JSON list of equivalent normalized spellings
```

### Probe library (read-only at runtime, ships with skill)

Lives at `skills/interview/solomon-interview-engine/probe_library/`. One YAML per domain. Each domain file holds ranked follow-up templates per keyword, plus fallbacks. **Lower priority number wins** (priority 1 fires before priority 9). Slot `{phrase}` for verbatim insertion.

```yaml
# probe_library/pricing.yaml
domain: pricing
version: 0.1.0
priority: 9   # 1–10, higher = more critical for cloning judgment
keywords:
  discount:
    - priority: 1
      template: "You said {phrase}. When was the last time you actually gave a discount?"
    - priority: 2
      template: "{phrase} — what would have to be true for you to break that?"
fallbacks:
  - "Tell me about the last time pricing came up in a conversation with a customer."
```

Each probe library file declares a semver `version` at the top level. Bumps follow standard semver: patch for new templates under existing keywords, minor for new keywords, major for breaking schema changes. `coverage.library_version_seen` is compared against this `version` on launch (§2.1 probe-library version migration). The schema and semver convention are documented in `skills/interview/solomon-interview-engine/probe_library/README.md`.

### Foundation YAMLs (derived summaries)

`foundation/NN-*.yaml` (00 through 06: industry, belief-system, why, principles, ideal-outcomes, non-negotiables, taxonomy). Header comment on each: `# Derived summary; canonical store is db/schemas/captured_items.sql.`

Each `solomon-onboarding-NN-*` wrapper compiles its session's `captured_items` rows into the matching YAML at session close. **YAML hand-edit reconciliation rule (DB always wins)**: when a YAML differs from its underlying rows on next re-render, the diff is logged to `mentoring_queue` (priority 5, source = `yaml_hand_edit`); owner accepts (creates a new captured_items row marking the prior superseded) or discards (YAML re-rendered to match DB).

**Hard-rule schema (`foundation/05-non-negotiables.yaml`)** — the deterministic check at Pipeline Stage 4 reads this format. Each rule is a list entry:

```yaml
# foundation/05-non-negotiables.yaml — derived summary; canonical store is db/schemas/captured_items.sql.
rules:
  - id: <captured_items.id>          # ulid linking back to the row that produced this rule
    statement: "Never quote below cost+15% on commercial jobs."
    domain: pricing
    condition:                        # JSON-logic expression evaluated by the Stage-4 deterministic checker
      and:
        - { ">=": [{ var: "event.classification.scope" }, "pricing"] }
        - { "<":  [{ var: "event.payload.margin_pct" }, 15] }
    on_violate:
      action: REJECT
      explanation: "Below 15% margin on commercial work — see captured_items.id <id>."
```

Stage 4 evaluates `condition` with the `json-logic-py` library (declared in `requires_python:` of the orchestrator). No LLM is involved at this stage — violations are deterministic and unappealable. Hand-edits to this file go through the same DB-wins reconciliation as any other foundation YAML.

### SOUL.md template

`SOUL.md` is loaded by Hermes into the system prompt every turn. Solomon's `SOUL.md` has five pinned sections, filled at end-of-onboarding from `captured_items` + `vocabulary`:

```markdown
# Solomon — <Owner Name>'s Personal Business Brain

## Identity
You are Solomon, a personal business brain for <Owner Name> at <Business Name>. You learn how the owner makes decisions and execute the routine 80% on their behalf, escalating the rest. You speak in the owner's voice (see Voice register).

## Decision philosophy
<3–5 bullet points distilled from foundation/02-why.yaml and foundation/03-principles.yaml at end-of-onboarding.>

## Voice register
<Top 30 vocabulary phrases by frequency, plus 2–3 verbatim sample sentences pulled from references/voice.md.>

## ELIZA listening rule (interview phase only)
When in an interview-phase session (`phase: interview` skill is loaded), you mirror, probe, and draw the owner out. One question at a time. Reuse the owner's verbatim phrases. Never paraphrase. Never stack questions. In decision phase, this rule does not apply — you load the populated profile and act.

## Hard rules pointer
Before any action, the orchestrator (Stage 4) checks `foundation/05-non-negotiables.yaml`. Hard rules cannot be overridden by reasoning, autonomy level, or owner state. If a hard rule blocks an action, explain the rule in plain English and stop.
```

### Existing tables (carry-over from Solomon v1)

**`decisions.sql`** — SQL mirror of `decisions/log.md` (one row per H2 entry; the markdown file is the human-readable face, the SQL row is the embeddable canonical record):

```
id              TEXT PRIMARY KEY        -- ulid
decision_date   TEXT NOT NULL           -- ISO 8601 from the H2 title (or UNKNOWN-DATE sentinel)
title           TEXT NOT NULL           -- H2 title body, max 60 chars
body            TEXT NOT NULL           -- canonical four-field rendering (Decision/Why/Alternatives/Owner)
owner           TEXT NOT NULL           -- name or initials
machine_id      TEXT                    -- recorded per §2.7 multi-device note
embedded_at     TEXT                    -- ISO 8601; null = pending Sleep-Cycle Job 11
created_at      TEXT NOT NULL
INDEX idx_embedded (embedded_at) WHERE embedded_at IS NULL
INDEX idx_date    (decision_date)
```

`audits.sql`, `biometrics.sql`, `rules_of_thumb.sql`, `mentoring_sessions.sql` — schemas inherited from Solomon v1 spec; documented in `db/README.md`. None require new columns for v2.

---

## §2. Skills, Plugins, and Subsystems

### §2.1. Interview-phase skills (5)

All carry `phase: interview` in front-matter. Listed in invocation order during a session.

**`solomon-interview-engine`** *(orchestrator during training)*
- **Triggered by** every onboarding session wrapper (`solomon-onboarding-00-industry` … `06-taxonomy`) and `solomon-mentoring-session`.
- **What it does**: reads `db.clarification_queue WHERE session_id = ? AND status = 'queued'` first — pending clarifications jump the queue. Otherwise detects keywords in the owner's last answer; selects the highest-priority unused probe from `probe_library/` for the active domain (lowest priority number wins); renders with verbatim phrase substitution; asks one question; on dry keyword falls back to a related keyword or a generic forward prompt; never stacks questions.
- **Inputs**: active domain, last answer, `probe_library/<domain>.yaml`, `db.coverage`, `db.vocabulary`, `db.clarification_queue`.
- **Outputs**: next question; `db.coverage.probe_count++`; `db.coverage.last_probed`, `last_probed_version`.
- **Subfolder**: `probe_library/` ships inside the skill. Read-only at runtime. Updates ship as new versions of the skill.

**`solomon-extraction`** *(parses each owner answer)*
- Called after every owner turn. Calls `solomon-redact` first.
- **What it does**: identifies `domain`, `type`, `statement`, `verbatim_phrase`, `example`, `reasoning`, `conditions`, `confidence`, `keywords`; writes ≥0 rows to `captured_items`. Multiple rows per answer when the owner makes multiple distinct claims.
- **Confidence scoring**: `stated` (first appearance, no example), `repeated` (second+ appearance of equivalent claim), `exemplified` (claim + concrete instance).
- **Outputs**: new captured_items rows with `embedded_at = NULL` (Sleep-Cycle Job 11 will embed); updates `coverage.items_captured`, `coverage.gap_score`, `coverage.turns_since_last_capture`.

**`solomon-vocabulary-capture`** *(owner's voice as data)*
- Called after every owner turn, in parallel with extraction. Calls `solomon-redact` on names that match entity patterns.
- **Two-pass extractor**:
  1. spaCy `en_core_web_sm` POS tagging → noun phrases, verb phrases (deterministic, free).
  2. LLM extraction (Sonnet, ~200 tokens out) → idioms, metaphors, stock expressions only (the things spaCy misses).
- **Outputs**: rows in `vocabulary` (SQL-only, not embedded — see §1); `type` field marks which extractor produced the row.

**`solomon-coverage-tracker`** *(when is a session done?)*
- Called by `interview-engine` before selecting the next probe.
- **What it does**: returns the lowest-coverage sub-topic with `gap_score > 0.4`; checks session-complete thresholds.
- **Session-complete rule**: complete when **either**:
  - **Saturation**: every sub-topic for the active domain has `gap_score < 0.4` AND `probe_count >= 5`.
  - **Diminishing returns**: total session `probe_count >= 8` AND `turns_since_last_capture >= 4`.
- **Probe-library version migration**: detects `coverage.library_version_seen < probe_library/<domain>.yaml::version` on launch and writes a `mentoring_queue` row (source = `probe_library_update`, priority 7). No automatic mass re-probe.

**`solomon-contradiction-check`** *(real-time conflict detection)*
- Called after every `extraction` insert.
- **What it does**: queries existing `captured_items` for the same domain; surfaces logical conflicts; writes the conflict id to `conflicts_with` on both rows; writes a row to `db.clarification_queue` (NOT `mentoring_queue`) so `interview-engine` resolves it in the **same session** while context is fresh.

### §2.2. Decision-phase skills (entry points)

**`solomon-profile-loader`** *(decision-phase entry)*
- Loaded at the start of any decision session — Plaud transcript processing, real-time orchestrator runs, daily reports.
- Loads compiled profile (from `captured_items` + `foundation/*.yaml`) and `vocabulary` into hot memory. Applies the owner's verbatim phrasing when generating outputs.
- **Replaces** the v1 `solomon-profile` skill; SKILL.md trigger list includes both `/solomon-profile-loader` and `/solomon-profile`.

**`solomon-listening-agent`** *(carry-over from v1)*
- Plaud transcript processor. Unchanged in this restructure except for adoption of the uniform front-matter and the `phase: decision` flag.

### §2.2.5. Decision-phase orchestrator pipeline (the runtime stack)

Real-time owner-on-behalf decisions flow through a deterministic ten-stage pipeline. Each external event becomes a `RawEvent` row in `db.events` (§2.7) and is processed in order. Failure of any stage stops the pipeline for that event; the event row records `status = failed` for diagnosis.

```
Capture → Salience → Classification → Hard-rule check → Working memory + 5-lane retrieval
       → System 1 (Sonnet) → System 2 (Opus) → Audit gate (Opus) → Owner-state gate → Action
```

**Real-time vs bulk** — the corpus path (§2.3 / §2.4.5) feeds bulk historical knowledge into `corpus/inbox/`. The orchestrator pipeline below handles **real-time decision events** that need an action now (an incoming Telegram message, a fresh Plaud transcript from the last 10 minutes, a Whoop state change, a new Gmail thread, a Calendar meeting start, a webhook). The two paths share Pinecone (read-only by the pipeline) but have separate write surfaces. An ingress plugin can feed both paths if its `plugin.yaml` declares `listens: [solomon.events]` in addition to writing to `corpus/inbox/`.

**Stage 1 — Capture**. Real-time-flagged ingress plugins push to `solomon.events` and write a row to `db.events`. The corpus path is not involved.

**Stage 2 — Salience scorer**. LLM call (Haiku, ~50 tokens output). Returns 0.0–1.0 across four dimensions: stakes, novelty, emotion, owner-involvement. Score < 0.3 → `events.status = skipped`, pipeline exits. Threshold lives in `corpus/schema.md` `salience_min:`.

**Stage 3 — Classification**. LLM call (Sonnet). Returns `{scope, domain, decision_type}`. Used to load scope-specific rules and route to the action surface.

**Stage 4 — Hard-rule check**. **Deterministic Python evaluation, no LLM.** Iterates over `foundation/05-non-negotiables.yaml` rules ONLY (the deterministic source of truth). Each rule has a `condition` clause evaluated as a JSON-logic expression against the event payload + classification. `db.captured_items.conditions` is human-readable prose for display in mentoring sessions and is **not evaluated** at this stage — promoting a captured_items rule to deterministic enforcement requires the owner to confirm a JSON-logic translation into `foundation/05-non-negotiables.yaml` (mentoring-session prompt: "want me to enforce this as a hard rule? Here's the JSON-logic. [Confirm / Edit]"). If any YAML rule violates → `events.status = blocked_by_hard_rule`, an explanation goes to Telegram, and the pipeline exits. Hard rules cannot be overridden by downstream stages or by autonomy level.

**Stage 5 — Working memory + 5-lane retrieval**. Working memory is read from `db.working_memory` (SQLite-backed LRU, 7-day TTL — no Redis dependency in v1). Retrieval runs the 5 lanes from §2.8 in parallel and merges by namespace weights.

**Stage 6 — System 1 predictor**. Sonnet. Loaded with hot identity (`SOUL.md` + `MEMORY.md` + `USER.md`), active-scope rules, retrieved context, owner-state row. Prompt: "Apply the owner's stated rules. Return the rule-based answer in 1–2 sentences. No reasoning, no exploration." Fast first take.

**Stage 7 — System 2 reasoner**. Opus. Same context as System 1 but allowed chain-of-thought. Returns full reasoning + answer.

**Stage 7b — System 1 vs 2 divergence check**. **No embedding call on the hot path.** Compute token-set Jaccard similarity (lowercased, punctuation-stripped, stopwords removed) plus length-ratio between System 1 and System 2 outputs. Combined score `0.6 × jaccard + 0.4 × length_ratio`. Below 0.7 → priority-4 `mentoring_queue` row (source = `surprise`) with both outputs in the payload so the owner can teach Solomon why the rule and the reasoning disagree. Token-Jaccard is local, deterministic, takes microseconds, and adds zero per-event API cost. Embedding-based comparison is deferred to a v2.1 enhancement if Jaccard proves too coarse — a v1 metric collected in `db.events.divergence_score` lets us evaluate Jaccard's calibration before paying for embeddings.

**Stage 8 — Audit gate**. Separate Opus call (independent of System 2). Inputs: `(proposed_action, hard_rules, scope, owner_state, system1_output, system2_output)`. Returns one of `APPROVE` / `DOWNGRADE` / `REJECT` / `REQUEST_RETHINK`. `REQUEST_RETHINK` loops back to Stage 7 once (max 1 retry), then escalates if still rejected.

**Stage 9 — Owner-state gate**. Reads latest `db.biometrics` row (Whoop signal). Modulates the per-scope autonomy ceiling for this event:
- **Green** (recovery > 60% AND sleep > 7h): full scope autonomy.
- **Yellow** (recovery 33–60% OR sleep 5–7h): downgrade to L2 ceiling regardless of scope.
- **Red** (recovery < 33% OR explicit stress flag): downgrade to L1 ceiling (suggestions only).
- **Whoop missing** (plugin disabled or stale > 24h): default to Green; log a one-time warning to `corpus/log.md`.

**Stage 10 — Action**. Routes per the combined `(effective_autonomy, audit_verdict)` level:
- L4 + APPROVE → ship silently; daily digest mention.
- L3 + APPROVE → ship for routine; one-tap for novel.
- L2 / L3 + DOWNGRADE → one-tap to Telegram (approve / edit / discuss).
- L1 + APPROVE / L0 → suggestion only, queued for next digest.
- REJECT / REQUEST_RETHINK after retry → escalate to `mentoring_queue` priority 2.

Every run logs `db.events.processed_at` plus per-stage timing.

### §2.3. Corpus subsystem — Karpathy LLM-Wiki, Pinecone-backed (4 skills)

The corpus absorbs bulk material the owner accumulates — SOPs, training docs, vendor contracts, customer emails, internal Slack/text threads, Plaud transcripts, presentations, exports. The interview engine alone won't surface every rule already encoded in those documents.

**Three-layer corpus model**:

| Layer | Folder | Mutability | Indexed? | Lane-1 retrieval weight |
|---|---|---|---|---|
| Raw sources | `corpus/raw/<category>/` | Immutable (LLM reads, never edits) | Pinecone namespace `solomon-corpus-raw` | 0.20 |
| Wiki pages | `corpus/wiki/{entities,concepts,playbooks}/` | LLM-maintained | Pinecone namespace `solomon-corpus-wiki` | 0.40 (highest) |
| Index + log | `corpus/index.md` + `corpus/log.md` | LLM-maintained | Read directly (no Pinecone) | n/a |

Page conventions (the schema, in `corpus/schema.md`):
- **Entity page** (`wiki/entities/customer-acme-corp.md`): YAML front-matter (`type: entity`, `subtype: customer`, `aliases: [...]`, `last_updated`); body sections: Identity, Relationship history, Key rules (with backlinks to `captured_items.id` and `corpus/raw/...`), Open threads, Cross-refs.
- **Concept page** (`wiki/concepts/refund-policy.md`): front-matter (`type: concept`, `domain`, `aliases`, `last_updated`); body: Definition, Owner's stated rule, Exceptions, Source citations, Cross-refs.
- **Playbook page** (`wiki/playbooks/close-of-month.md`): front-matter (`type: playbook`, `cadence`, `owner`, `last_run`); body: Trigger, Steps, Inputs/outputs, Failure modes, Cross-refs.
- Every page ends with a `## Sources` section listing `corpus/raw/...` paths and `captured_items.id` values used to compile it.

**Four corpus skills** (all `phase: decision`):

**`solomon-corpus-ingest`** *(entry point)*
- **Trigger**: automatic via `corpus-inbox-watcher` worker (§2.4 + §2.4.6.5) when files appear in `corpus/inbox/`; manual via `/solomon-corpus-ingest <file_or_glob>`.
- **What it does**: routes a file (rules in §2.5) → calls `solomon-redact` (§2.6) → writes to `corpus/raw/<category>/` with normalized slug → LLM pass to summarize, extract entities, draft/update entity/concept/playbook pages → **rule-extraction pass** (§2.7 `proposed_rules`) drafts owner-rule candidates and queues them for mentoring confirmation → appends `corpus/log.md` and updates `corpus/index.md` → embeds changed wiki pages and new raw chunks. Single ingest may touch 10–15 wiki pages and produce 0–N proposed_rules rows.
- **Wiki vector cleanup**: before re-embedding a wiki page, reads `wiki_vectors.section_hashes` for the page; computes the new hash list; deletes Pinecone vectors for any hashes in the old list but not the new; upserts new vectors; writes the new hash list back. Prevents orphaned `wiki:<slug>:<section_hash>` vectors lingering after page rewrites.
- **Idempotency**: SHA256-keyed manifest (`db.ingested_files`, §2.7); deterministic Pinecone vector IDs; diff-based wiki page edits. Rule-extraction is also idempotent — re-ingesting the same file produces no duplicate `proposed_rules` rows (dedup by `verbatim_excerpt` SHA256 + source_path).

**`solomon-corpus-lint`** *(Sleep-Cycle Job 9, also on-demand)*
- Scans `corpus/wiki/` for: contradictions, **stale pages**, orphan pages, missing cross-refs, near-duplicates.
- **Stale rule**: a wiki page is stale if there exist `ingested_files` rows with `category` matching the page's domain (or referencing the page's primary entity) whose `ingested_at > wiki_page.last_updated` AND whose content has not yet been merged into the page's source-citations. Top 20 stalest pages surface to `mentoring_queue` per run.
- **Near-duplicate**: cosine similarity > 0.95 in `solomon-corpus-raw` namespace → mentoring_queue priority 7.

**`solomon-corpus-query`** *(retrieval helper, used by Lane 1)*
- Hits all four Pinecone namespaces with configurable weights, deduplicates, returns ranked list with citation paths back to `corpus/raw/` and `corpus/wiki/`.
- v1 is read-only. Karpathy's "auto-file synthesized answers back as new concept pages" pattern is deferred to v2.1 pending a precise durability rule.

**`solomon-corpus-forget`** *(GDPR-style deletion / owner mistake-drop)*
- **Trigger**: `/solomon-corpus-forget <file_path | entity_slug | wiki_page_slug>` or owner request via Telegram.
- **Confirmation**: every forget is destructive — owner gets a one-tap Telegram confirmation showing the per-row diff before any action.
- **Cascade** (one block, no exceptions):
  - **Entity page** dedicated to the forgotten entity → hard-delete; Pinecone vectors for that page deleted by ID.
  - **Concept or playbook pages** mentioning the forgotten entity → LLM-driven full-page rewrite (remove all references, preserve surrounding logic, update `last_updated`, re-embed).
  - **Raw files** for the forgotten entity → moved to `corpus/_forgotten/<sha256>/` (encrypted with the backup key from §2.10); `ingested_files.status = forgotten`; raw vectors deleted.
  - **`captured_items` rows** mentioning the forgotten entity in `verbatim_phrase`/`example`/`statement` → if surrounding rule logic survives, redact entity name in place (`[REDACTED:entity]`), update `updated_at`, re-embed (next Job 11). If the entire row is about the forgotten entity, hard-delete the row + Pinecone vector.
  - **`vocabulary` rows**: hard-delete if `vocabulary.phrase` (after normalization per §2.11) exactly matches the forgotten entity's slug or any value in its `aliases` list. Otherwise leave. Vocabulary captures phrasings, not entities; only direct slug matches qualify for deletion.
- Each action logged line-by-line to `corpus/log.md` and a single roll-up entry to `decisions/log.md`.

### §2.4. Inbox watcher plugin — `corpus-inbox-watcher`

A `watchdog`-based Hermes plugin (modeled exactly on `plaud-ingest`) that auto-triggers `solomon-corpus-ingest` when files land in `corpus/inbox/`. The watcher is purely the trigger; it never touches file contents or moves them — that's the ingest skill's job.

**Behaviour contract**:

| # | Requirement | Detail |
|---|---|---|
| 1 | Recursive watch | Watch `corpus/inbox/` recursively via Python `watchdog`. |
| 2 | Catch-up on startup | Scan `corpus/inbox/**/*` once on plugin start; queue pre-existing files for ingest before live event watching. |
| 3 | Debounce | 30s after last file event before triggering. Reset timer on every new event. **Cap**: 5 resets OR 5 minutes from the first event in the window, whichever comes first — then fire regardless of new arrivals (livelock prevention). |
| 4 | File-stable check | File size unchanged for 3 consecutive seconds before triggering ingest. |
| 5 | Trigger ingest | Invoke `solomon-corpus-ingest` with the list of stable file paths. Same skill-invocation mechanism as `plaud-ingest`. |
| 6 | No file mutation | Watcher does not move, copy, rename, or read file contents. |
| 7 | Failure handling | If ingest raises: log to `corpus/log.md` with file path + error; leave file in `inbox/`; no automatic retry. |
| 8 | Resource-light | Idle CPU ~0%, RAM under 50 MB. OS-level events only — no polling loops. |
| 9 | Lifecycle | Starts when Hermes starts; stops cleanly when Hermes stops. No separate daemon. |
| 10 | Logging | Log start, stop, file detection, debounce trigger, ingest invocation, errors. |

**Canonical `plugin.yaml`**:

```yaml
name: corpus-inbox-watcher
version: 0.1.0
description: Auto-triggers solomon-corpus-ingest when files land in corpus/inbox/
requires_env: []
requires_python: [watchdog]
default_enabled: true
watch_paths:
  - corpus/inbox
debounce_seconds: 30
debounce_max_resets: 5
debounce_max_total_seconds: 300
file_stable_seconds: 3
```

**Known behaviour**: if Hermes is killed mid-debounce, the in-memory timer is lost. On restart, the catch-up scan re-detects the file; the manifest's SHA256 lookup prevents double-ingest. Documented in `plugins/corpus-inbox-watcher/README.md`.

**Acceptance tests**:
1. Single `.txt` drop appears in `raw/<category>/` within 30–40s, one ingest log entry.
2. 10 files dropped in burst → one batched ingest run.
3. Hermes-down catch-up: stop, drop file, start; file processed on startup.
4. 50+ MB PDF mid-write: watcher waits for 3s file-stable check.

### §2.4.5. External data ingress — how the outside world reaches `corpus/inbox/`

The `corpus-inbox-watcher` only handles the last hop (filesystem → ingest). Each external source has its own ingress plugin that drops files into `corpus/inbox/<category>/`. **The canonical pattern**: external source → ingress plugin (IMAP / API poller / webhook receiver / OAuth pull) → write to `corpus/inbox/<category>/<ISO-timestamped-slug>` → `corpus-inbox-watcher` picks up → `solomon-corpus-ingest` routes / redacts / writes raw + wiki / embeds / logs.

Each ingress plugin must:
1. Use an idempotency token (provider-side message ID, ETag, IMAP UID, etc.) recorded so the same external item is never downloaded twice across restarts. Per-plugin state lives in `db/schemas/<plugin>_state.sql` (one table per plugin, owned by that plugin).
2. ISO-timestamp every filename written into `corpus/inbox/`. Format: `YYYY-MM-DDTHH-MM-SS--<source>--<provider-id>.<ext>`.
3. Write to the right `corpus/inbox/<category>/` subfolder so the watcher's routing-by-subfolder rule (§2.5) applies.
4. Mark the external source-side item as read/processed so subsequent polls skip it.
5. Hold an in-memory dedup set during the running session so concurrent threads in the same plugin can't double-download.
6. Log every successful download, every failure, and every dedup-skip to `corpus/log.md` with the ingress plugin name as the prefix.

**Plaud** *(authoritative — locked v1 spec)*

Plaud sends transcripts as emails with `.txt` attachments to the owner's configured email address from `no-reply@plaud.ai` via Plaud's AutoFlow feature. The `plaud-ingest` plugin runs two background threads watching that inbox over IMAP:

- An **IDLE listener** that grabs new mail the instant it arrives.
- A **backup poller** that checks every 60 seconds in case IDLE missed one.

Both threads search with the UNSEEN flag — `mail.search(None, f'(UNSEEN FROM "{PLAUD_SENDER}")')` — so Gmail only returns unread mail; old emails read before the plugin started will never match. After downloading an attachment, the plugin marks the email read via `mail.store(eid, "+FLAGS", "\\Seen")` so the next search skips it. An in-memory `_downloaded_email_ids` set holds IDs already grabbed during the current run so the IDLE thread and the 60-second poller cannot download the same email twice if they fire simultaneously.

Each downloaded `.txt` attachment is renamed with an ISO timestamp prefix to avoid collisions and saved to `corpus/inbox/messages/`. From there `corpus-inbox-watcher` picks it up via its standard 30-second debounce and 3-second file-stable check, then invokes `solomon-corpus-ingest`, which routes the file to `corpus/raw/messages/`, redacts PII, generates wiki entries, embeds into Pinecone, and logs.

**Required env vars** (`.env.example`): `PLAUD_IMAP_HOST`, `PLAUD_IMAP_USER`, `PLAUD_IMAP_PASS`, `PLAUD_SENDER=no-reply@plaud.ai`. Persistent state lives in `db/schemas/plaud_state.sql` (last-seen UID, downloaded-IDs over the last 7 days for crash-recovery dedup).

**Authentication note**: Gmail (and most modern providers) blocks IMAP basic-auth unless the account has 2FA + an app-password. `install.sh`, when configuring Plaud, surfaces a one-line check: "Your `PLAUD_IMAP_PASS` must be an app-password if `PLAUD_IMAP_HOST` is `imap.gmail.com` (Gmail rejects regular passwords on IMAP). Generate one at <https://myaccount.google.com/apppasswords>." If the user provides the regular password Gmail will silently reject the IMAP login; the plugin logs `auth_failed` to `corpus/log.md` and emits a Telegram message asking the owner to fix the credential.

**Other v1 integrations** *(spec TBD — see Open Questions for v2.1; v1 install-menu options are gated on the owner providing the per-source spec)*:

| Source | Expected ingress pattern | Lands in | Status |
|---|---|---|---|
| Telegram (owner-pushed files / voice notes) | Bot push → handler writes to `corpus/inbox/messages/` | `corpus/inbox/messages/` | Spec TBD |
| Google Workspace — Gmail | Gmail API watch + 60s backup poller (Plaud-pattern, OAuth instead of IMAP basic auth) | `corpus/inbox/emails/` | Spec TBD |
| Google Workspace — Drive | Drive `changes.watch` API + 5-min backup poller; downloads new files in watched folders | `corpus/inbox/docs/` or `data/` per MIME | Spec TBD |
| Google Workspace — Calendar | Calendar events API push + 60s backup poller; events serialized as `.json` per occurrence | `corpus/inbox/data/` | Spec TBD |
| Whoop | OAuth + 5-min REST poller for daily metrics; serialized as `.json` per day | Direct write to `db.biometrics` (skips `corpus/inbox/`) | Spec TBD |
| n8n / make.com | Webhook receiver — workflow POSTs to `http://localhost:<port>/solomon/webhook/<scenario>` with payload + filename | `corpus/inbox/<scenario-routed-category>/` | Spec TBD |

The Plaud spec is the template. Any v1 install that enables one of the "Spec TBD" integrations must complete its spec at the same depth before the integration is treated as locked. The skeleton plugin scaffolds in `plugins/<name>/` ship with `plugin.yaml` + `__init__.py` + `README.md` and a `_TODO_SPEC.md` placeholder noting the missing detail.

### §2.4.6. Hermes plugin contract (verified against Hermes docs)

Hermes plugins are stateless event handlers attached to Hermes' agent invocations — they fire on tool calls and LLM calls, not as long-lived workers. Anything that needs to run continuously (IMAP listener, file watcher, decision-pipeline tick) lives in a **worker** instead (§2.4.6.5), not a plugin.

`solomon/hermes-plugins/<name>/` — every Hermes plugin is a Python package matching this contract.

**`plugin.yaml`** — declarative metadata (verified against Hermes wiki):

```yaml
name: <slug>                          # matches folder name
version: <semver>
description: <one line>
requires_env: [ENV_VAR_1, ...]        # plugin refuses to load if any are unset
requires_python: [pkg1, pkg2]         # pip deps; install.sh step 4 installs them
default_enabled: true|false
hooks: [pre_tool_call, post_tool_call, pre_llm_call, post_llm_call, on_session_start, on_session_end, on_session_finalize, on_session_reset, subagent_stop, pre_gateway_dispatch]
```

**`__init__.py`** — exports `register(ctx)`. Hermes calls this on plugin load. The verified `ctx` API:

```python
def register(ctx):
    ctx.register_tool(name, schema, handler, toolset=None, check_fn=None)    # exposes tool to LLM
    ctx.register_command(name, handler, description="")                       # slash command in CLI/gateway
    ctx.register_cli_command(name, help, setup_fn, handler_fn)                # terminal subcommand
    ctx.register_skill(name, path)                                            # registers a skill folder
    ctx.register_hook(hook_name, callback)                                    # lifecycle hook (see hooks list)
    ctx.dispatch_tool(name, arguments)                                        # call other tools w/ parent context
    ctx.inject_message(content, role="user")                                  # CLI only
```

**`ctx` does NOT provide** (verified absent from Hermes docs; Solomon plugins must implement these themselves):
- ❌ `ctx.subscribe()` / pubsub — Hermes has no pubsub bus
- ❌ `ctx.schedule()` — cron is gateway-level (§2.9), not plugin-level
- ❌ `ctx.db()` — plugins open their own SQLite connection (with WAL pragmas per §10 step 7)
- ❌ `ctx.pinecone()` — plugins import `pinecone` directly, read `PINECONE_API_KEY` from `os.getenv()`
- ❌ `ctx.telegram()` — Telegram is the gateway adapter (§2.4.8), not a plugin client
- ❌ `ctx.env()` — plugins use `os.getenv()`; `requires_env` only gates loading
- ❌ `ctx.logger()` — plugins use stdlib `logging` and append to `corpus/log.md` themselves
- ❌ `ctx.invoke_skill()` — skills are markdown documents the LLM reads; programmatic skill invocation is via `ctx.dispatch_tool()` to a tool the skill exposes, not a function call
- ❌ `ctx.lock()` — plugins implement file locks themselves (e.g., `fcntl` on Linux/macOS, `db/.<name>.lock` path convention from §2.5 still applies but plugins manage it)
- ❌ `ctx.on_unload()` — plugins are stateless; teardown isn't part of the lifecycle (workers handle that, not plugins)

**Plugin loading sequence** (verified):
1. Hermes startup → discover plugins in `~/.hermes/plugins/`, `.hermes/plugins/`, pip entry points, bundled `<repo>/plugins/`.
2. Read each `plugin.yaml`. Skip if listed in `plugins.disabled`.
3. Check `requires_env`; skip if any variable is unset.
4. Import `__init__.py`; call `register(ctx)` exactly once.
5. If `register` raises, plugin is disabled with a log line; Hermes continues with the rest.

**Skill-from-plugin invocation pattern** (corrected): a plugin cannot call `ctx.invoke_skill("solomon-corpus-ingest")`. To trigger work that requires a skill's instructions, the plugin either:
(a) Registers a tool (e.g., `ingest_corpus_file`) whose handler does the work directly. The skill's job is to teach the LLM when/how to call the tool. The Python work happens in the tool handler.
(b) Writes a row to `db.events` with `source = file_dropped` and the file path. A worker tick (§2.4.6.5) picks it up and starts a Hermes agent session via the CLI: `subprocess.run(["hermes", "-s", "solomon-corpus-ingest", "-q", f"process {path}"])`.

Pattern (a) is preferred when the work is mechanical (move file, call Pinecone, write SQL). Pattern (b) is preferred when the work needs LLM reasoning (entity extraction, wiki page drafting). `solomon-corpus-ingest` uses pattern (b) because it needs LLM reasoning per file.

### §2.4.6.5. Workers — long-lived processes outside Hermes

Solomon's IMAP listener, file watcher, and real-time decision-pipeline tick cannot be Hermes plugins (plugins are stateless event handlers, per §2.4.6 verification). They run as **workers**: separate Python processes alongside the Hermes gateway, supervised by launchd/systemd (§2.4.9), sharing `db/solomon.db` with Hermes via WAL.

`solomon/workers/<name>/` — each worker is a Python package with:

```
workers/<name>/
├── worker.yaml            # name, version, description, requires_env, requires_python, supervisor (launchd|systemd|both)
├── __main__.py            # `python -m solomon.workers.<name>` entrypoint; runs forever
├── README.md
└── (optional) state.py    # opens db/solomon.db with WAL pragmas
```

v1 workers:
- **`workers/plaud-ingest/`** — IMAP IDLE + 60s poller; writes `.txt` attachments to `corpus/inbox/messages/`; persists state in `db.plaud_state`. (§2.4.5)
- **`workers/corpus-inbox-watcher/`** — `watchdog`-based recursive file watcher on `corpus/inbox/`; writes `db.events` rows with `source = file_dropped`; the file path becomes the `payload`. (§2.4)
- **`workers/pipeline-tick/`** — every 60s, scans `db.events WHERE status = 'pending'`, spawns a Hermes agent session per pending event (`hermes -s solomon-orchestrator -q "process event <id>"` or equivalent). The orchestrator skill loads §2.2.5's stage handlers. Concurrency: at most 5 in-flight pipelines (config in `corpus/schema.md`).

Each worker has its own launchd `.plist` or systemd `.service` unit installed by `install.sh`. Workers communicate with Hermes plugins **only through the shared SQLite database** — no in-process pubsub. SQLite's WAL mode and the `db/.pinecone-write.lock` file lock from §2.5 handle concurrency.

**Why this works without Hermes-internal pubsub**: SQLite-as-queue is a well-known pattern. Workers `INSERT INTO events ...`; the pipeline-tick worker polls `WHERE status = 'pending'`; the lock and atomic UPDATE prevent double-processing. No Redis required for v1; v2.1 may swap to Redis if event volume justifies it.

### §2.4.7. Failure handling and resilience

External services fail. The plan pins a behaviour for each known failure mode so `install.sh`, plugins, and the §2.2.5 pipeline don't have undefined behaviour under stress.

| Failure | Detection | Behaviour |
|---|---|---|
| Pinecone unreachable (network / 5xx) | Any `pinecone()` call raises | Pipeline Stage 5 (retrieval) returns empty; logged; pipeline continues with non-retrieval context. Job 11 marks rows as `embedded_at_attempted` and retries next night. Three consecutive nights of failure → Telegram alert. |
| Pinecone embedding-dim mismatch | Index metadata differs from `EMBEDDING_DIM` | `install.sh` refuses to proceed; ingest skips the file with `status = failed`, logs explanation. |
| OpenAI rate-limit (429) | HTTP status / SDK exception | Exponential backoff with jitter (1s, 2s, 4s, 8s, 16s, give up). Job 11 batches in groups of 100, leaves the rest for next run on persistent rate-limit. |
| OpenAI down (5xx) | HTTP status | Same backoff. Embedding work defers to next sleep cycle. Decision-pipeline LLM calls fall back to OpenRouter alternative if `OPENROUTER_API_KEY` is set; otherwise the event lands in `events.status = failed` with a Telegram alert. |
| Anthropic / OpenRouter LLM down | HTTP status | Pipeline stages (Salience, Classification, System1/2, Audit) fall back per `SOLOMON_MODEL_FALLBACK_<stage>` env vars (default to OpenRouter if direct Anthropic fails). If both are down, the event row stores `status = failed` and the owner gets a Telegram alert summarizing skipped events. |
| Telegram unreachable | Webhook timeout / 5xx | Bot retries 3× over 30s. Persistent failure → write the message to `corpus/inbox/_telegram-undelivered/` for human review; the bot retries every 5 min. |
| Plaud IMAP auth-failed | IDLE/poll exception | Plugin sleeps 5 min, then retries. After 3 failures, surfaces a Telegram alert ("check `PLAUD_IMAP_PASS` — Gmail may need an app-password"). Plugin keeps retrying. |
| SQLite locked / corrupted | sqlite3 exception | Refuse to proceed; the operation fails fast. Daily backup (Job 10) restores from yesterday's tarball if `db/solomon.db` is unreadable. Owner gets a Telegram alert. |
| Hermes crash mid-pipeline | Process killed | On restart, watcher's catch-up scan handles `corpus/inbox/`. The pipeline reads `events.status IN (in_progress, pending)` and resumes from the highest-completed stage per row (idempotent stages re-run safely). |
| `corpus-inbox-watcher` debounce timer lost mid-window | Hermes killed | Catch-up scan re-detects files; SHA256 manifest prevents double-ingest (§2.5). |
| Disk full | Filesystem error | Refuse new ingest; old backups rotate first. Owner gets a Telegram alert. |
| Plugin install missing dependency | `import` error at register | Plugin marked `disabled` in registry; install.sh re-prompts for `pip install` on next run. Other plugins continue. |

Every failure goes to `corpus/log.md` with the plugin slug, severity, and the next-action plan. Failures with severity ≥ ERROR also get one-line Telegram alerts (deduped within 1h windows).

### §2.4.8. Telegram bot — Hermes' built-in gateway adapter

Telegram is **not** a Solomon plugin. It's one of the 20 platform adapters that ship with Hermes' built-in gateway (verified). Solomon configures it via `hermes gateway setup` during install; no Python bot code lives in this repo.

**Setup at install time** (driven by `install.sh` step 5 optional integrations menu):
1. `install.sh` runs `hermes gateway setup` and selects the Telegram adapter.
2. Owner provides `TELEGRAM_BOT_TOKEN` (from BotFather) and confirms `TELEGRAM_CHAT_ID` (the owner's user/chat ID — Hermes' setup wizard discovers it from `/start`).
3. Hermes writes the gateway config; the gateway service (§2.4.9) handles long-polling continuously.

**How Solomon participates**:
- **Inbound**: Hermes' gateway routes incoming messages to the configured agent. A Solomon Hermes-plugin (`hermes-plugins/solomon-pipeline-injector/`) registers a `pre_llm_call` hook that reads the user message + classifies it. Text → writes a `db.events` row with `source = telegram`, payload = the text; the pipeline-tick worker (§2.4.6.5) processes it. Voice note → transcribed via the §2.5 transcription backend, then the same event flow. Document/image → saved to `corpus/inbox/<routed-category>/` per §2.5 routing.
- **Outbound**: Solomon plugins/skills send via Hermes' built-in `send_message` tool (registered by the gateway). One-tap approval cards use Hermes' `send_inline_keyboard` tool with buttons `[Approve] [Edit] [Discuss] [Reject]`. Mentoring questions use plain `send_message`. Daily digests scheduled by Sleep-Cycle Job 8 + an additional `0 8 * * *` cron.

**Rate limiting**: Telegram-imposed (one outbound message per 5s per chat). The gateway handles backpressure; Solomon doesn't reimplement.

**Auth**: Hermes' gateway already enforces `TELEGRAM_CHAT_ID` allowlist (only configured chats reach the agent). No separate Solomon check required. v2.1 may add multi-chat allowlist for delegating to assistants.

**Inline-button callbacks**: Hermes' gateway converts callback queries to user messages with a structured payload; the Solomon plugin's `pre_llm_call` hook routes them to the right handler (one-tap → action; mentoring answer → captured_items insert + clarification_queue update).

### §2.4.9. Process supervisor — Hermes gateway + Solomon workers

Two long-lived process families run continuously:

1. **Hermes gateway** — `hermes gateway start` (verified Hermes command). One process, hosts every Hermes platform adapter (Telegram per §2.4.8) and every loaded Hermes plugin's `register(ctx)` hooks. Also runs Hermes' built-in cron scheduler (ticks every 60s, executes scheduled jobs in fresh agent sessions).
2. **Solomon workers** — separate Python processes per worker (§2.4.6.5): `plaud-ingest`, `corpus-inbox-watcher`, `pipeline-tick`. Each is its own process so a crash in one doesn't take down the others.

Both families are supervised at the OS level by `install.sh`:

- **macOS** — one `.plist` per service in `~/Library/LaunchAgents/`:
  - `io.solomon.hermes-gateway.plist` → runs `hermes gateway start`. KeepAlive=true, RunAtLoad=true.
  - `io.solomon.worker.plaud-ingest.plist` → runs `python -m solomon.workers.plaud_ingest`.
  - `io.solomon.worker.corpus-inbox-watcher.plist` → runs `python -m solomon.workers.corpus_inbox_watcher`.
  - `io.solomon.worker.pipeline-tick.plist` → runs `python -m solomon.workers.pipeline_tick`.
  - `install.sh` writes each plist and runs `launchctl load`.
- **Linux** — one `.service` per service in `~/.config/systemd/user/`:
  - `solomon-hermes-gateway.service`, `solomon-worker-plaud-ingest.service`, `solomon-worker-corpus-inbox-watcher.service`, `solomon-worker-pipeline-tick.service`. All `Restart=always`, `WantedBy=default.target`.
  - `install.sh` runs `systemctl --user daemon-reload && systemctl --user enable --now <each>`.
- **Windows** — out of v1 scope; flagged in `EXPANSIONS.md`.

Per-session conversations are NOT attached to the gateway via a custom socket — Hermes' gateway already routes per-platform messages (Telegram, etc.) to the agent. Manual CLI conversations (`hermes -s solomon-onboarding -q "begin"`) start their own short-lived agent process; the gateway is unaffected.

`install.sh` step 12 (auto-launch onboarding) is just `hermes -s solomon-onboarding -q "begin"` — a one-shot conversation that doesn't need the gateway. The gateway starts automatically at install time and is independently responsible for routing real-time external messages while the owner is doing the onboarding interview.

The 5-min Whoop poller, 60s Plaud poller, file watcher, and pipeline-tick loop all run inside their respective worker processes — separate from Hermes gateway. Sleep-cycle cron jobs (§2.9) run inside Hermes gateway via its built-in scheduler. Telegram inbound runs inside Hermes gateway (gateway adapter).

**Health check**: `solomon-setup` skill on first run inspects `launchctl list | grep io.solomon` (macOS) or `systemctl --user list-units 'solomon-*'` (Linux). Any missing service triggers a re-install of the unit and a Telegram alert.

### §2.5. Ingest operational contracts

**Routing** — three-tier resolution, first match wins:

1. **Subfolder hint** — if the inbox path starts with `sops/`, `emails/`, `messages/`, `docs/`, or `data/`, that's the category.
2. **Extension map** (in `corpus/schema.md`):
   - `.eml, .mbox` → `emails`
   - `.csv, .tsv, .parquet, .json` → `data`
   - `.wav, .mp3, .m4a, .flac, .opus, .ogg` → `messages` (post-transcription)
   - `.txt, .md, .rtf` → LLM classifier
   - `.pdf, .docx, .doc, .pptx, .xlsx, .html, .heic, .png, .jpg` → `docs`
3. **LLM classifier fallback** — reads first 500 tokens, picks one of the 5 categories. Logged so the owner can correct it (corrections add a rule to `corpus/schema.md`).

Re-ingesting the same content always lands in the same category (deterministic given filename + first 500 tokens).

**Subfolder behaviour** — the watcher recurses for both nested drops (folder of 200 emails → one ingest run) and pre-existing structure (`inbox/sops/2026-h1/` honored as routing hint). Empty dirs ignored. Symlinks not followed.

**Idempotency manifest** — `db/schemas/ingested_files.sql`:

```
id                    TEXT PRIMARY KEY        -- ulid
sha256                TEXT NOT NULL UNIQUE    -- canonical equality test
inbox_path_at_ingest  TEXT NOT NULL
raw_path              TEXT                    -- final location
size_bytes            INTEGER NOT NULL
mime_type             TEXT
category              TEXT NOT NULL           -- sops | emails | messages | docs | data
ingest_run_id         TEXT NOT NULL
status                TEXT NOT NULL           -- pending | in_progress | success | partial | failed | forgotten
wiki_pages_touched    TEXT                    -- JSON list of corpus/wiki/... paths
pinecone_vectors      INTEGER
error_message         TEXT
ingested_at           TEXT NOT NULL
INDEX idx_sha256      (sha256)
INDEX idx_status      (status)
```

The watcher consults this table before invoking ingest. SHA256 lookup: if `status = success`, skip; if `pending|in_progress|partial|failed`, retry from scratch.

**Duplicate detection** — SHA256 of file bytes is canonical equality. Filenames don't matter. Near-duplicates (different bytes, similar embeddings) detected at lint time (cosine > 0.95) and surfaced to `mentoring_queue`.

**Restart / crash recovery** — three idempotent guarantees:
- Wiki page edits are diff-based.
- Pinecone vector IDs are deterministic: `vector_id = sha256(file)[:16] + ":" + chunk_index` for raw chunks, `"wiki:" + slug + ":" + section_hash` for wiki page sections, `"captured:" + row.id` for captured_items, and `"decision:" + sha256(entry_body) + ":0"` for decision-log entries. Pinecone upserts replace.
- Manifest `status` field is the checkpoint. On startup, watcher scans `WHERE status IN (pending, in_progress, partial)` and re-runs ingest on those paths. Same `ingest_run_id` is reused.

**Concurrent Pinecone writes** — at most one in-flight, ever. File lock at `db/.pinecone-write.lock` (PID + start_time + ingest_run_id or job name). Both `solomon-corpus-ingest` and Sleep-Cycle Job 11 (embed-pending) acquire this lock before any Pinecone write. If held: ingest skips and reschedules per debounce; Job 11 defers to next nightly run. New file events keep arriving during a held lock and reset the debounce; on next debounce expiry the watcher retries the lock. Stale lock (PID dead) cleared on Hermes startup. At most one Pinecone write process is in-flight at any moment — covers ingest-vs-ingest, ingest-vs-Job-11, and Job-11-vs-Job-11.

**File size and type limits** (in `corpus/schema.md`, owner-editable):
- Max size per file: 100 MB. Larger → `corpus/inbox/_oversized/` + log entry.
- Allowed extensions: routing extension map above. Anything else → `corpus/inbox/_unsupported/` + log entry.
- Empty files: skipped, logged.
- Both `_oversized/` and `_unsupported/` parking folders surface in the weekly Telegram digest from `solomon-audit` and as mentoring_queue priority 7 entries from `solomon-corpus-lint` so files don't sit forgotten.

**Audio transcription and image OCR** — backends declared in `corpus/schema.md`:
- **Transcription**: default `whisper.cpp` local. Optional OpenAI Whisper API (`OPENAI_API_KEY`). If `plaud-ingest` is installed, its existing pipeline is reused. Documented in `references/api-transcription.md`.
- **OCR**: default `pytesseract` local. Optional Google Vision API (uses Google Workspace OAuth). PDFs with text layer skip OCR. Documented in `references/api-ocr.md`.

Default is local-only; nothing leaves the machine for transcription/OCR unless the owner opts in.

### §2.6. PII redaction — `solomon-redact`

PII redaction is needed for corpus ingest **and** for interview-derived `captured_items` and `vocabulary` rows (customer names, employee names, phone numbers in stories the owner tells). One global utility skill, called from three places.

- **Lives at**: `skills/utilities/solomon-redact/`. `phase: utility` (callable from any context).
- **Called by**: `solomon-corpus-ingest` (decision phase), `solomon-extraction` and `solomon-vocabulary-capture` (interview phase). Also callable as `/solomon-redact <file_path | text>` for owner-initiated audits.
- **Pattern detection**:
  - **Named entities** (PERSON, ORG, LOC, GPE) — detected via spaCy `en_core_web_sm` NER; tokenized as `[REDACTED:entity]`. spaCy is already a `solomon-vocabulary-capture` dependency, so no new install. Owner allowlist via `corpus/schema.md` `entity_allowlist:` (e.g., the owner's own company name should not be redacted in their own SOPs).
  - SSN, US/EU phone with name-context, credit card (Luhn), API keys (high-entropy 20+ char strings prefixed by `key=`, `token=`, `Bearer `), AWS access keys (`AKIA…`), private SSH keys (PEM markers), passwords in obvious labeled contexts.
- **Replacement**: in-place `[REDACTED:ssn]`, `[REDACTED:cc]`, `[REDACTED:key]`, `[REDACTED:entity]` tokens. Original bytes (for files) quarantined to `corpus/raw/_pre-redaction/<sha256>.bin`, AES-256-GCM with the backup key from §2.10.
- **Allowlist**: paths matching globs in `corpus/schema.md`'s `redaction_skip:` list bypass redaction (e.g., owner's own SOPs that intentionally include test API keys).
- **Audit**: every redaction logged to `corpus/log.md` with file path, type, and offset (not the value).
- **Test fixtures**: `skills/utilities/solomon-redact/fixtures/` holds known-PII test files used in CI; the skill is verified against them on every release.

Defense-in-depth, not a guarantee. The owner is still expected not to drop payroll CSVs into `inbox/` unless they accept the risk.

### §2.7. Lifecycle tables and flows

**`mentoring_queue.sql`** — cross-session items awaiting batched owner attention:

```
id                    INTEGER PRIMARY KEY AUTOINCREMENT
source                TEXT NOT NULL          -- lint | contradiction | surprise | coverage_gap |
                                             -- probe_library_update | yaml_hand_edit | legacy_decision_undated |
                                             -- corpus_rule_proposal
surfaced_at           TEXT NOT NULL
status                TEXT NOT NULL          -- queued | addressed | dismissed
priority              INTEGER NOT NULL DEFAULT 5    -- lower number = higher priority (1 = urgent)
payload               TEXT NOT NULL          -- JSON: refs to captured_items.id, wiki paths, raw paths
addressed_at          TEXT
addressed_in_session  TEXT                   -- mentoring-YYYY-MM-DD slug
notes                 TEXT
INDEX idx_status_priority (status, priority)
```

**Priority assignments** (header comment in the SQL file):

| Source | Priority |
|---|---|
| `corpus-lint` contradiction, both items `confidence=exemplified` | 1 |
| Sleep-cycle Job 5 (conflict-detection across heuristics) | 3 |
| `corpus-lint` contradiction, mixed confidence | 3 |
| Sleep-cycle Job 3 (surprise-replay) | 4 |
| `corpus_rule_proposal` (corpus-ingest extracted a rule) | 4 |
| `coverage-tracker` gap | 5 |
| `yaml_hand_edit` reconciliation | 5 |
| `legacy_decision_undated` (ported v1 decision missing date) | 6 |
| `corpus-lint` stale page | 6 |
| `probe_library_update` | 7 |
| `corpus-lint` near-duplicate | 7 |
| Files parked in `_oversized/` or `_unsupported/` | 7 |
| `corpus-lint` orphan page | 8 |

`solomon-mentoring-session` reads `WHERE status = 'queued' ORDER BY priority` to populate each session's topic list.

**`clarification_queue.sql`** — in-session contradictions, resolved while context is fresh:

```
id              INTEGER PRIMARY KEY AUTOINCREMENT
session_id      TEXT NOT NULL          -- which interview session is active
captured_id_a   TEXT NOT NULL          -- captured_items.id of one side
captured_id_b   TEXT NOT NULL          -- captured_items.id of the other side
suggested_probe TEXT NOT NULL          -- "Earlier you said X; just now Y. Which wins, and why?"
status          TEXT NOT NULL          -- queued | asked | resolved | dismissed
created_at      TEXT NOT NULL
resolved_at     TEXT
resolution_id   TEXT                   -- captured_items.id of the resolving rule
INDEX idx_session_status (session_id, status)
```

`solomon-interview-engine` reads `WHERE session_id = ? AND status = 'queued'` before every probe selection — pending clarifications jump the queue. `solomon-contradiction-check` writes here for **same-session** conflicts. `mentoring_queue` is reserved for cross-session items surfaced by `corpus-lint`.

**`events.sql`** — every real-time decision event flowing through the §2.2.5 pipeline; canonical record for crash recovery and audit:

```sql
-- db/schemas/events.sql
event_id           TEXT PRIMARY KEY        -- ulid
source             TEXT NOT NULL           -- telegram | plaud_live | whoop | gmail_live | calendar | webhook
payload            TEXT NOT NULL           -- JSON
received_at        TEXT NOT NULL
processed_at       TEXT
salience_score     REAL                    -- 0.0–1.0
classification     TEXT                    -- JSON {scope, domain, decision_type}
hard_rule_blocked  TEXT                    -- captured_items.id of the violated rule, or NULL
system1_output     TEXT
system2_output     TEXT
divergence_score   REAL                    -- cosine similarity of system1 vs system2 (0.0–1.0)
audit_verdict      TEXT                    -- APPROVE | DOWNGRADE | REJECT | REQUEST_RETHINK
owner_state        TEXT                    -- green | yellow | red | unknown
action_taken       TEXT
status             TEXT NOT NULL           -- pending | in_progress | complete | skipped | failed | blocked_by_hard_rule
stage_timings_ms   TEXT                    -- JSON {capture, salience, classification, …, action}
INDEX idx_status   (status)
INDEX idx_source   (source, received_at)
```

**`working_memory.sql`** — hot cache for the §2.2.5 pipeline; SQLite-backed LRU with 7-day TTL (no Redis dependency in v1):

```sql
-- db/schemas/working_memory.sql
key              TEXT PRIMARY KEY        -- e.g., "scope:pricing:active_thread:deal-acme-1234"
value            TEXT NOT NULL           -- JSON
expires_at       TEXT NOT NULL
last_accessed    TEXT NOT NULL
INDEX idx_expires (expires_at)
```

**`proposed_rules.sql`** — staging area for owner rules that the corpus ingest extracts from raw text but cannot directly write to `captured_items` (the two-phase rule from §0 keeps the interview as the only authoritative writer). Mentoring confirms or rejects each proposal:

```sql
-- db/schemas/proposed_rules.sql
id                    TEXT PRIMARY KEY        -- ulid
domain                TEXT NOT NULL           -- pricing | hiring | ops | …
proposed_statement    TEXT NOT NULL           -- normalized rule the LLM extracted
verbatim_excerpt      TEXT NOT NULL           -- the owner's actual sentence from raw
source_path           TEXT NOT NULL           -- corpus/raw/<category>/<file>
source_offset         INTEGER                 -- character offset in raw file (for navigation)
keywords              TEXT NOT NULL           -- JSON list, lowercase
confidence_hint       TEXT                    -- stated | repeated | exemplified — best guess from extraction
proposed_jsonlogic    TEXT                    -- optional draft JSON-logic if the rule looks deterministic
status                TEXT NOT NULL           -- queued | confirmed | rejected | edited
created_at            TEXT NOT NULL
addressed_at          TEXT
addressed_in_session  TEXT                    -- mentoring-YYYY-MM-DD slug
captured_item_id      TEXT                    -- captured_items.id once confirmed
hard_rule_promoted    INTEGER NOT NULL DEFAULT 0  -- 1 if also written to foundation/05-non-negotiables.yaml
INDEX idx_status_domain (status, domain)
```

**Promotion workflow** (cross-references §2.3 corpus-ingest and §2.7 mentoring queue):
1. `solomon-corpus-ingest` runs an additional **rule-extraction pass** after entity extraction. The pass uses Claude Sonnet with a prompt: "Extract any first-person rules the owner states or implies in this text. Format as JSON: `[{statement, verbatim, domain, confidence_hint, jsonlogic_if_deterministic}]`."
2. Each extracted rule writes a `proposed_rules` row with `status = queued`.
3. `corpus-ingest` writes a `mentoring_queue` row (`source = corpus_rule_proposal`, priority 4, payload references the proposed_rules.id).
4. Next mentoring session reads the queue and prompts the owner via Telegram: *"In `[corpus/raw/sops/2026-pricing-policy.docx]` you wrote: 'I never quote below cost+15%.' Confirm as a captured rule? `[Confirm] [Edit] [Reject] [Make this a hard rule]`"*.
5. **Confirm** → writes a `captured_items` row (with `confidence = stated`, `source_session = corpus-extract-<ulid>`), sets `proposed_rules.status = confirmed`, links `captured_item_id`.
6. **Edit** → owner provides revised statement; same flow.
7. **Reject** → sets `proposed_rules.status = rejected` with the reason in payload.
8. **Make this a hard rule** → in addition to the captured_items insert, prompts owner to confirm the JSON-logic translation (which the corpus-ingest extraction already drafted in `proposed_jsonlogic`), then writes a YAML entry to `foundation/05-non-negotiables.yaml`. Sets `hard_rule_promoted = 1`. Stage 4 of the pipeline (§2.2.5) will enforce it on the next event.

**This closes the bulk-corpus-rule gap**: rules buried in SOPs, emails, and Plaud transcripts surface to the owner for confirmation rather than silently never reaching `captured_items`. The two-phase rule is preserved (interview phase confirms; corpus only proposes).

`mentoring_queue.source` enum gains a new value: `corpus_rule_proposal` (priority 4).

**`scope_autonomy.sql`** — current autonomy level per scope, updated by Sleep-Cycle Job 7:

```sql
-- db/schemas/scope_autonomy.sql
scope                  TEXT PRIMARY KEY
level                  INTEGER NOT NULL CHECK (level BETWEEN 0 AND 4)
since                  TEXT NOT NULL
last_reeval_at         TEXT NOT NULL
override_rate_30d      REAL
audit_pass_rate_30d    REAL
notes                  TEXT
```

**`wiki_vectors.sql`** — tracks live section hashes per wiki page so re-embeds can clean up orphans:

```sql
-- db/schemas/wiki_vectors.sql
page_path        TEXT PRIMARY KEY        -- e.g., corpus/wiki/entities/customer-acme-corp.md
section_hashes   TEXT NOT NULL           -- JSON list of currently-active section_hash values
last_updated     TEXT NOT NULL
```

**`sessions.sql`** — onboarding/mentoring resumption flag:

```
session_id        TEXT PRIMARY KEY        -- e.g., "onboarding-03-2026-05-09" or "mentoring-2026-05-09"
type              TEXT NOT NULL           -- onboarding | mentoring
domain            TEXT                    -- pricing | hiring | … | null for mentoring
status            TEXT NOT NULL           -- active | complete | abandoned
started_at        TEXT NOT NULL
last_activity_at  TEXT NOT NULL
completed_at      TEXT
abandoned_reason  TEXT
turns             INTEGER NOT NULL DEFAULT 0
notes             TEXT
INDEX idx_status_type (status, type)
```

**Onboarding session resumption rule** — `solomon-onboarding` (the meta orchestrator) reads `sessions` + `coverage` + `captured_items` on launch:
- No items for active session → start from question 1.
- Partial items, session not marked complete → resume from the lowest-coverage sub-topic.
- Status complete → advance to the next session, or report "all 7 sessions complete."
- Owner override: `/solomon-onboarding-restart 03` resets coverage for that session and starts fresh.

Status flow: `active → complete` (saturation/diminishing-returns from §2.1) or `active → abandoned` (explicit `/solomon-onboarding-abandon` or 30-day inactivity).

**Abandoned-session disposition**: `captured_items` rows from abandoned sessions are kept (the owner's words remain valid even if the session was incomplete). Pending `clarification_queue` rows for the abandoned session are auto-marked `status = dismissed` with `notes = 'session abandoned'`. `coverage` rows are kept and inform future sessions on the same domain. The session itself is preserved in `sessions` with `status = abandoned` and the reason in `abandoned_reason`.

**Contradiction resolution flow**:
- Real-time, same session → `contradiction-check` → `clarification_queue` → `interview-engine` jumps it onto next probe.
- Cross-session, batched → `corpus-lint` → `mentoring_queue` → `mentoring-session` runs ELIZA-style probing on the contradicting items → captures owner's resolution into `captured_items` (with `type: rule` and explicit `conflicts_with`) → next `corpus-ingest` re-run on the affected wiki page rewrites it citing the resolution.

**Multi-device** — single-device-only for now. Two laptops both running Hermes both watching `corpus/inbox/` is undefined behavior (Pinecone races, local file lock, non-network-safe SQLite). Documented as a known constraint in `EXPANSIONS.md` with three forward paths: (1) single-VPS with both laptops as Telegram clients, (2) Turso/LiteFS distributed SQLite with one designated writer, (3) cloud-native Hermes worker. `install.sh` warns if it detects a previous install with a recent `decisions/log.md` entry from a different machine ID. Machine ID source: Linux `/etc/machine-id`; macOS `ioreg -rd1 -c IOPlatformExpertDevice | awk '/IOPlatformUUID/ { gsub(/"/,""); print $3 }'`; fallback random UUID at `~/.hermes/machine.id`.

### §2.8. Retrieval — 5 lanes, 4 Pinecone namespaces

The 5 lanes are *retrieval strategies*; the 4 namespaces live inside Lane 1 (semantic). Orthogonal axes.

| Lane | Strategy | Backed by |
|---|---|---|
| 1. Semantic | Vector similarity across 4 Pinecone namespaces | `solomon-corpus-wiki`, `solomon-captured-items`, `solomon-corpus-raw`, `solomon-decision-log` |
| 2. Recency | Time-windowed query on recent decisions/active threads | `decisions/log.md` recent rows, `db.captured_items` recent rows |
| 3. Entity | Direct lookup by entity slug | `corpus/wiki/entities/<slug>.md` |
| 4. Pressure | Owner-state-modulated salience boost | `db.biometrics`, working memory |
| 5. Foundation | Hard-rule lookup for active scope | `foundation/05-non-negotiables.yaml`, `db.captured_items WHERE type='rule'` |

**Default Pinecone namespace weights** (in `memory/pinecone-index.md`; configurable per query):

```yaml
namespace_weights:
  solomon-corpus-wiki:      0.40    # synthesized, highest signal
  solomon-captured-items:   0.30    # owner's stated rules, second-highest
  solomon-corpus-raw:       0.20    # grounding citations
  solomon-decision-log:     0.10    # historical context
```

Sum = 1.0. Per-query override allowed (e.g., a hard-rule lookup might force `captured-items: 1.0`).

`references/retrieval-5-lane.md` documents the lanes and namespaces; `solomon-corpus-query` is the helper Lane 1 calls.

### §2.9. Sleep cycle — 12 jobs

Nightly jobs run in order. Failure of one does not block the others.

| Job | Name | What it does |
|---|---|---|
| 1 | hindsight | Reviews past 24h decisions; writes audit rows |
| 2 | archival | Moves stale items to long-term storage |
| 3 | surprise-replay | Surfaces unexpected outcomes → `mentoring_queue` priority 4 |
| 4 | stress-test | Simulated edge cases against current rules |
| 5 | conflict-detection | Cross-heuristic conflicts → `mentoring_queue` priority 3 |
| 6 | working-memory-cleanup | Trims hot context |
| 7 | autonomy-reeval | Adjusts Solomon's autonomy level (L0–L4) |
| 8 | mentoring-scheduler | Triggers a mentoring session if either condition holds: (a) `mentoring_queue` has any row with `priority <= 4` and `status = 'queued'`, or (b) 7 days have passed since the last completed mentoring session in `sessions` table. Picks the top 3–5 topics from `mentoring_queue` ordered by priority. Owner override: `/solomon-mentor-now` runs immediately; `/solomon-mentor-skip` defers 7 days. |
| 9 | corpus-lint | Calls `solomon-corpus-lint` (contradictions, stale, orphans, near-duplicates) |
| 10 | corpus-backup | Snapshots `db/solomon.db` + `corpus/`, encrypts with backup key, ships to destination |
| 11 | embed-pending | Picks up rows in `captured_items` and `decisions` `WHERE embedded_at IS NULL`, batch-embeds via `text-embedding-3-large`, upserts to Pinecone with deterministic IDs (`captured:<row.id>`, `decision:<sha256-of-entry-body>:0`), writes `embedded_at = NOW()`. Failure mode: row stays null, retried next night. Interview turns stay fast — embedding is offline. Acquires `db/.pinecone-write.lock` for the duration of the batch. If held, defers to next run. (Vocabulary is not embedded — see §1.) |
| 12 | yaml-reconcile | Re-renders all 7 `foundation/NN-*.yaml` files from current `captured_items` rows. Diffs each against the on-disk YAML; any hand-edits not yet seen by the DB-wins reconciliation are written to `mentoring_queue` (priority 5, source = `yaml_hand_edit`). Catches drift even when no interview session has touched a domain for months. |

**Scheduling**: Hermes' gateway has a built-in cron scheduler (verified: ticks every 60s, runs jobs as fresh isolated agent sessions). All 12 sleep-cycle jobs register via Hermes' `/cron add` slash command. Default schedule is `0 3 * * *` (3am owner-local time). Each job runs in its own isolated agent invocation with the corresponding skill attached (`hermes` invokes `solomon-sleep-<job>` skill, which performs the work via tools). Failure of one does not block the others — each agent invocation is independent. Cron registration is done by the `solomon-setup` skill on first run (not by `install.sh` directly) so it can be re-registered if the owner moves time zones.

Owner overrides (Telegram slash commands, handled by Hermes' gateway):
- `/cron list` — shows all 12 registered jobs
- `/cron run <job-name>` — runs one job immediately
- `/cron pause <job-name>` — pauses until `/cron resume`
- Solomon-specific shortcuts: `/solomon-sleep-now` (runs all 12 in sequence), `/solomon-sleep-job <name>`, `/solomon-sleep-skip <name>` (defers to tomorrow). These are Solomon plugin commands registered via `ctx.register_command()` (verified API).

### §2.10. Backup, restore, encryption key recovery

**Backup** (Job 10, `corpus-backup`):
- Snapshots `db/solomon.db` and `corpus/` (raw + wiki + index.md + log.md). Pinecone is intentionally not backed up (regenerable from raw + wiki). Encrypted tarball.
- **Default destination**: an owner-supplied local path outside the repo (e.g., `~/Backups/solomon/` on an external drive or a syncthing-watched folder). Default in `.env.example`: `BACKUP_DEST_LOCAL=$HOME/Backups/solomon`. The repo's own `archives/backups/` is the fallback if `BACKUP_DEST_LOCAL` isn't writable. **Local path is the default precisely to avoid the chicken-and-egg recovery problem** (see below).
- **Optional secondary destination**: Google Drive folder via `plugins/google-workspace/` if Google Workspace is enabled. Off by default; turning it on writes a second copy of each tarball to Drive.
- **Retention**: rotating — 7 daily, 4 weekly, 12 monthly. Older cleared automatically.
- **On-demand**: `/solomon-export` (alias `/backup-now`) callable any time; optionally sends location URL to Telegram.

**Recovery on a dead laptop — the chicken-and-egg path**: if the laptop is gone, `~/.hermes/.env` is gone with it, including the Drive OAuth tokens. To recover from a Drive-only backup, the owner must (1) install Hermes on the new laptop, (2) clone the repo and run `bash install.sh`, (3) when prompted to enable Google Workspace, complete a fresh OAuth flow using only Google credentials (no Solomon files needed), (4) point `bash install.sh --restore <gdrive-url-or-shared-link>` at the encrypted tarball, (5) supply the BIP-39 mnemonic to decrypt. This is documented in `install/bootstrap.md`. The default-local path avoids this entirely: the owner just plugs the external drive into the new laptop and runs `bash install.sh --restore /path/to/local/backup.tar.gz.enc` with the BIP-39 mnemonic — no OAuth required.

**Encryption key flow**:
- On first install (or first time the backup job runs), `install.sh` generates a 32-byte (256-bit) AES-256-GCM key, derives an Argon2id-protected wrap key from a passphrase the owner enters, and writes:
  - The wrapped key to `~/.hermes/.env` as `SOLOMON_BACKUP_KEY_WRAPPED=…`.
  - The raw key as a **24-word BIP-39 mnemonic** (24 words = 256 bits + 8-bit checksum, the only BIP-39 length that actually encodes the full AES-256 key — 12 words would only encode 128 bits, which would silently halve the key strength). Displayed **once** on screen with the instruction "save this to a password manager AND write it on paper. Without it, your backups are unrecoverable."
- `install.sh --restore <tarball>` accepts either the passphrase (re-derives the wrap key) or the 24-word BIP-39 mnemonic (recovery on a fresh laptop where `~/.hermes/.env` is gone).

**Restore procedure** — `bash install.sh --restore <path-or-url-to-tarball>`:

1. Same Hermes-detect, env-prompt, plugin-symlink flow as a normal install.
2. Prompt for passphrase OR BIP-39 mnemonic.
3. Decrypt tarball into a temp dir.
4. Restore `db/solomon.db` and `corpus/{raw,wiki,index.md,log.md}` to the new install location.
5. **Re-embedding cost/time gate** — print:
   > Restore plan: N raw chunks + M wiki pages + K captured_items + L decision-log entries to embed. Total: (N+M+K+L) vectors. Estimated time at OpenAI's 3,000 RPM rate-limit: ~T minutes. Cost: see https://openai.com/api/pricing for `text-embedding-3-large` current rate × (N+M+K+L). Proceed? [y/N]
   Default `N`. Idempotent — re-fires if the owner aborts.
6. Re-create the 4 Pinecone namespaces. Three cases:
   - Same Pinecone account, namespaces exist with matching dim → reuse, only re-embed missing vectors.
   - Different account or new namespaces → create them, then **clear `embedded_at` to NULL** on every row in `captured_items` and `decisions` (the restore brought their old timestamps in but those vectors don't exist in the new account); re-embed everything: raw chunks from `corpus/raw/`, wiki pages from `corpus/wiki/`, and the now-pending `captured_items` + `decisions` rows. Job 11 picks them up on the next run, or the restore can run an inline embed pass if the owner proceeded past the cost gate in step 5.
   - Namespaces exist but `EMBEDDING_DIM` mismatches → fail with explicit message; owner edits `.env`.
7. Run a `solomon-audit` integrity pass; surface any rows in `ingested_files.status != success`.
8. Auto-launch a "welcome back" Telegram message confirming counts.

Restore is idempotent — running it twice on the same target is a no-op for unchanged content.

### §2.11. Pinned defaults

**Embedding model**: `text-embedding-3-large` at **3072 dimensions**. v1 default; OpenAI is the embedding provider. Override allowed in `.env` (`EMBEDDING_MODEL=…`, `EMBEDDING_DIM=…`); install.sh validates the dim matches Pinecone. Other providers are an EXPANSIONS.md future expansion only.

**`decisions/log.md` entry format** (canonical):

```markdown
## YYYY-MM-DD — Title (max 60 chars)

**Decision**: one sentence.
**Why**: 1–3 sentences.
**Alternatives considered**: bullets (2–4 lines).
**Owner**: name or initials.
```

Embedding: one chunk per entry, body minus the H2 title. Vector ID `decision:<sha256-of-entry-body>:0`. Documented in `decisions/log.md` header and `references/orchestrator-pipeline.md`.

**Date assignment for ported v1 decisions** (cascade): git first-commit ISO date → file mtime → `## UNKNOWN-DATE — <Title>` queued in `mentoring_queue` (source = `legacy_decision_undated`, priority 6) for owner correction. Original prose preserved under a `<details>` block per entry but excluded from embedding.

**Vocabulary normalization** (the `phrase` lookup key): lowercase, strip surrounding punctuation, collapse internal whitespace to single spaces, strip leading/trailing articles (`the`, `a`, `an`). No stemming. Hyphens preserved as-is. `aliases` JSON column handles equivalences. Documented in `db/schemas/vocabulary.sql` header.

**Probe priority semantics**: lower number wins. Priority 1 fires before priority 9. Pinned in `skills/interview/solomon-interview-engine/probe_library/README.md` schema header. Same convention as `mentoring_queue.priority`.

**Required env vars** (`.env.example` and `connections.md` row 1 / row 3):
- `PINECONE_API_KEY=` (required)
- `OPENAI_API_KEY=` (required for embeddings, can also be used for Whisper transcription if owner opts in)
- `EMBEDDING_MODEL=text-embedding-3-large`
- `EMBEDDING_DIM=3072`
- `TELEGRAM_BOT_TOKEN=`, `TELEGRAM_CHAT_ID=` (required)
- `GOOGLE_MCP_SERVER_URL=` (required if Google Workspace integration is enabled — OAuth alone is insufficient)
- `SOLOMON_BACKUP_KEY_WRAPPED=` (auto-generated by install.sh)

**Telemetry**: `solomon-audit` reports vector counts per namespace, total bytes in `corpus/`, wiki/raw/captured_items/decision counts, last ingest/lint/mentoring/backup timestamps, top 20 vocabulary phrases by frequency. **No dollar estimates** — pricing rots; the audit emits one stable URL line for owner reference: `# To estimate monthly cost, see https://www.pinecone.io/pricing — vector count above × current rate.`

**Autonomy spectrum (per scope)** — pinned five-level scale, stored per scope in `db.scope_autonomy` (§2.7):

| Level | Name | Behaviour |
|---|---|---|
| L0 | Manual | Solomon does nothing automatic; only answers when asked. |
| L1 | Suggested | Solomon proposes; owner approves every action via Telegram. |
| L2 | Drafted | Solomon drafts and ships only after owner one-tap. |
| L3 | Supervised | Solomon ships routine actions; novel / high-stakes still need approval. |
| L4 | Autonomous | Solomon ships everything in scope; daily digest summarizes. |

Each scope (pricing, hiring, ops, customer, vendor, finance, …) starts at L0 on install. Promotion: ≥20 events in scope (`db.events`) over the trailing 30 days with override rate < 10% AND audit-pass rate > 90% → `level + 1`. Demotion: override rate > 25% OR a hard-rule violation in scope → `level - 1`. Sleep-cycle Job 7 (autonomy-reeval) computes promotions/demotions and writes a `decisions/log.md` entry per transition. The owner-state gate (§2.2.5 Stage 9) provides a per-event ceiling on top of the scope level.

**LLM model assignments per stage** (pinned; configurable in `.env`):

| Stage / use | Model | Notes |
|---|---|---|
| Salience scorer (Stage 2) | Claude Haiku | Cheap, fast, ~50 tokens out |
| Classification (Stage 3) | Claude Sonnet | Structured output to schema |
| System 1 predictor (Stage 6) | Claude Sonnet | Rules-only, no reasoning |
| System 2 reasoner (Stage 7) | Claude Opus | Chain-of-thought allowed |
| Audit gate (Stage 8) | Claude Opus | Independent of System 2 |
| Interview-engine probe rendering | Claude Sonnet | Verbatim phrase substitution |
| Vocabulary-capture LLM pass | Claude Sonnet | Idioms/metaphors only |
| Corpus-ingest entity extraction | Claude Sonnet | Drafts wiki page bodies |
| Corpus-forget rewrite | Claude Opus | Higher reasoning load |
| Embedding (Job 11, Pinecone upserts) | OpenAI `text-embedding-3-large` | 3072 dims, see §1 |

Override env vars: `SOLOMON_MODEL_SALIENCE`, `_CLASSIFICATION`, `_SYSTEM1`, `_SYSTEM2`, `_AUDIT`, `_INTERVIEW`, `_VOCAB`, `_INGEST`, `_FORGET`. Hermes routes via OpenRouter or direct Anthropic OAuth (already managed; Solomon does not store an Anthropic API key).

**Pinned `phase` field per skill**:

| Skill | Phase |
|---|---|
| `solomon-setup`, `solomon-guide` | decision |
| `solomon-onboarding`, `-onboarding-status`, `-onboarding-00..06` | interview |
| `solomon-interview-engine`, `-extraction`, `-vocabulary-capture`, `-coverage-tracker`, `-contradiction-check` | interview |
| `solomon-corpus-ingest`, `-lint`, `-query`, `-forget` | decision |
| `solomon-redact` | utility (phase-agnostic; callable from any context) |
| `solomon-profile-loader`, `solomon-listening-agent` | decision |
| `solomon-mentoring-session` | interview |
| `solomon-decision-log` | decision |
| `solomon-audit` | decision |
| `solomon-level-up` | interview |

CI tests assert no skill loads under the wrong phase.

---

## §3. AIS-OS Primitive → Solomon Mapping

| AIS-OS primitive | Lands in Solomon as | Changes |
|---|---|---|
| Root `CLAUDE.md` | `solomon/CLAUDE.md` | Sections for Hermes binding, two-phase architecture, foundation YAMLs, hard-rule pointer |
| `context/` | `solomon/context/` | Add `owner-state.md` for Whoop modulation |
| `references/` | `solomon/references/` | 22 docs incl. distilled runtime, Hermes binding, ELIZA explainer, interview architecture, corpus LLM-Wiki, portability, integrations pattern, transcription, OCR (Workers reference deferred to EXPANSIONS.md) |
| `connections.md` | `solomon/connections.md` | 13-row table; Pinecone + Telegram + Google Workspace required |
| `decisions/log.md` | `solomon/decisions/log.md` | Adopt canonical format from §2.11; port the 12 v1 decisions in via LLM rewrite |
| `archives/` | `solomon/archives/` | Park large prose docs + ELIZA source code + Karpathy gist |
| `.claude/skills/` | `solomon/skills/` (7 categories) | Renamed to `skills/` for Hermes resolution; `interview/`, `corpus/`, and `utilities/` are new categories |
| `aios-intake.md` | `solomon/intake.md` | Expanded to 7 sessions matching foundation YAMLs |
| `EXPANSIONS.md` | `solomon/EXPANSIONS.md` | Adopted; sections per §12 step 3 |

---

## §4. Hermes Primitives Embedded in Solomon

| Hermes primitive | Solomon file | Role |
|---|---|---|
| `SOUL.md` | `solomon/SOUL.md` | Solomon's voice + decision philosophy + ELIZA-listening rule (interview-phase only) |
| `MEMORY.md` | `solomon/MEMORY.md` | Agent-curated facts learned across sessions (starts empty) |
| `USER.md` | `solomon/USER.md` | Agent-curated owner facts (filled progressively as captured_items → derived summaries) |
| `~/.hermes/.env` | `solomon/.env.example` | Template; user copies to `.env` with real keys |
| `~/.hermes/skills/solomon/` | repo root after install | Hermes resolves the whole pack here |
| `~/.hermes/plugins/<name>/` | `solomon/plugins/<name>/` | Symlinked at install time |
| Hermes `delegate_task` | n/a in v1 | Sub-agents (Hermes-native parallel reasoners) deferred to EXPANSIONS.md (v2 scope). Distinct from Solomon's v1 "workers" (§2.4.6.5), which are OS-supervised Python services, not Hermes sub-agents. |

---

## §5. Four Cs and Three Ms → Solomon Primitives

| Lens | Solomon primitive | File location |
|---|---|---|
| **Context** (4C) | Foundation YAMLs + captured_items + `context/` + `MEMORY.md` + `USER.md` | `foundation/`, `db/schemas/captured_items.sql`, `context/`, root `MEMORY.md`, `USER.md` |
| **Connections** (4C) | Integrations registry + Hermes plugins | `connections.md`, `plugins/`, `references/api-*.md` |
| **Capabilities** (4C) | Skills + orchestrator pipeline | `skills/`, `orchestrator/pipeline/` |
| **Cadence** (4C) | Sleep cycle + mentoring + audit | `orchestrator/sleep-cycle/`, `skills/learning/{solomon-mentoring-session,solomon-audit}/` |
| **Mindset** (3M) | Belief / Why / Principles YAMLs | `foundation/01-`, `02-`, `03-` |
| **Method** (3M) | Decision log + System 1/2 + 5-lane retrieval | `decisions/log.md`, `references/system1-system2.md`, `references/retrieval-5-lane.md` |
| **Machine** (3M) | Orchestrator runtime + skill pack + plugins | `orchestrator/`, `skills/`, `plugins/` |

---

## §6. Skill Reorganization

**27 total skills** in **7 categories**. 14 carry over from current Solomon (the 16 minus `solomon-profile`, replaced by `solomon-profile-loader`, and `spec-open-question-resolution`, moved to `archives/`). 13 net-new skills are added.

```
skills/
├── setup/  (2)               solomon-setup, solomon-guide
├── onboarding/  (9)          solomon-onboarding, solomon-onboarding-status, 00–06 sessions
├── interview/  (5) NEW       solomon-interview-engine (+probe_library/),
│                             solomon-extraction,
│                             solomon-vocabulary-capture,
│                             solomon-coverage-tracker,
│                             solomon-contradiction-check
├── corpus/  (4) NEW          solomon-corpus-ingest,
│                             solomon-corpus-lint,
│                             solomon-corpus-query,
│                             solomon-corpus-forget
├── runtime/  (2)             solomon-profile-loader (NEW — replaces solomon-profile),
│                             solomon-listening-agent
├── learning/  (4)            solomon-mentoring-session,
│                             solomon-decision-log,
│                             solomon-audit (NEW),
│                             solomon-level-up (NEW)
└── utilities/  (1) NEW       solomon-redact (global PII pass)
```

**How existing onboarding skills change**: each `solomon-onboarding-NN-*` becomes a thin wrapper that sets the active domain and delegates to `solomon-interview-engine`. After every owner turn the wrapper invokes `solomon-extraction` + `solomon-vocabulary-capture` + `solomon-contradiction-check` in parallel; `solomon-coverage-tracker` decides when the session is done. At session close, the wrapper compiles `captured_items` rows into `foundation/NN-*.yaml`.

**How `solomon-mentoring-session` changes**: same mechanics. Runs the same 5 interview skills but scopes to recent decision-log entries and surprise/conflict signals from `mentoring_queue` (`WHERE status = 'queued' ORDER BY priority`).

**Uniform `SKILL.md` front-matter** (added in one pass to every skill):

```yaml
---
name: solomon-interview-engine
category: interview
phase: interview                # interview | decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-interview", "begin interview"]
inputs: [active_domain, last_answer, probe_library/<domain>.yaml, db.coverage, db.vocabulary, db.clarification_queue]
outputs: [next_question, db.coverage (probe_count++)]
reads_only: false
autonomy_level: L1               # L0–L4 from references/autonomy-spectrum.md
depends_on: []
portable: true                   # contents agent-neutral
---
```

---

## §7. Root `CLAUDE.md` Section Headings

```
# Solomon — Personal Business Brain (Hermes Skill Pack)
## What Solomon is (Hermes-native single-agent in v1; Workers deferred to v2)
## Two-phase model (Interview vs Decision — never co-mingled)
## How to read this repo (Four Cs map → folders)
## Install (bash install.sh — single command; do NOT use `hermes skills install`)
## Hard rules (foundation/05-non-negotiables.yaml — read first, always)
## Identity (SOUL.md)
## Memory (Hermes auto-loads MEMORY.md + USER.md every turn)
## Captured items + vocabulary (db/schemas/*.sql — interview output, decision input)
## Decision-phase pipeline (10 stages: Capture → Salience → … → Action; §2.2.5)
## Hermes plugin contract (plugin.yaml + register(ctx); §2.4.6)
## Telegram bot (the only owner-facing UI; §2.4.8)
## Failure handling (Pinecone down / OpenAI rate-limit / IMAP auth / Hermes crash; §2.4.7)
## Autonomy spectrum (L0–L4 per scope, modulated by owner state; §2.11)
## Corpus & LLM Wiki (corpus/ — bulk ingestion, Pinecone-backed; raw/wiki/index/log)
## Knowledge base (Q1 + Q3 distilled)
## Voice (references/voice.md + db.vocabulary head)
## Connections (Pinecone, Telegram, Google Workspace required; others optional)
## Skills index (Setup / Onboarding / Interview / Corpus / Runtime / Learning / Utilities)
## Orchestrator entry points (orchestrator/README.md)
## Sleep Cycle (12 jobs incl. J9 corpus-lint + J10 corpus-backup + J11 embed-pending + J12 yaml-reconcile)
## Foundation YAMLs (links to all 7 derived summaries)
## Decision log (pointer + canonical format)
## Autonomy spectrum (L0–L4)
## Plugins (8 incl. _template + corpus-inbox-watcher). Workers deferred to v2 (see EXPANSIONS.md)
## Portability (references/portability.md)
## How you work with me (operator preferences, ELIZA listening rule, phase rules)
## Default Shift (3Ms ritual)
```

---

## §8. `intake.md`

Complements (does not replace) the seven onboarding skills.

- `intake.md` = single-file paste/voice-dump source of truth.
- `solomon-onboarding-NN-*` skills = interactive ELIZA-style guided flows backed by `solomon-interview-engine`.
- Both write to `captured_items` (raw rows) → derived `foundation/NN-*.yaml`.
- Pasted intake answers are still parsed by `solomon-extraction` + `solomon-vocabulary-capture` + `solomon-contradiction-check` (each preceded by `solomon-redact` per §2.6). The only thing skipped is the live probing loop.

Structure: 7 H2 sections matching the YAMLs, each with 1–3 sub-prompts and a fenced code block for the answer. Plus a Q0 voice-samples block (verbatim paste; contamination warning).

---

## §9. `connections.md` — 13 Initial Rows

Columns: *Domain | Tool | Mechanism | Auth | Required | Last Checked*.

1. **Vector memory** — Pinecone (4 namespaces: `solomon-corpus-wiki`, `solomon-corpus-raw`, `solomon-captured-items`, `solomon-decision-log`) — `plugins/pinecone-bridge/` — `PINECONE_API_KEY` + `OPENAI_API_KEY` + `EMBEDDING_MODEL` + `EMBEDDING_DIM` — **required**
2. **Owner interface** — Telegram — Hermes gateway adapter (built-in, configured via `hermes gateway setup`) — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — **required**
3. **Email + Calendar + Docs/Drive/Sheets** — Google Workspace — `plugins/google-workspace/` (Google MCP) — OAuth + `GOOGLE_MCP_SERVER_URL` — **required**
4. **Workflow orchestrator** — n8n or make.com — `plugins/workflow-bridge/` — `WORKFLOW_WEBHOOK_URL` + scenario IDs — optional
5. **Voice capture** — Plaud — `plugins/plaud-ingest/` (file watcher) — local path — optional
6. **Owner state** — Whoop — `plugins/whoop-bridge/` — OAuth — optional
7. **Decision store** — SQLite — local file `db/solomon.db` — none — **required (auto)**
8. **Sub-agents (v2)** — Hermes parallel reasoners via `delegate_task` — n/a — n/a — **deferred to v2 (see EXPANSIONS.md section 6)**; v1 runs all reasoning in the main Hermes agent. Distinct from Solomon's `workers/` (§2.4.6.5), which are real v1 components.
9. **Host runtime** — Hermes — `~/.hermes/` — n/a — **required**
10. **LLM** — OpenRouter / Anthropic — Hermes-managed — OAuth or API key — **required**
11. **Cloud worker host (future)** — Render/Railway — future expansion — n/a — optional
12. **Corpus auto-ingest** — File watcher (watchdog) — `workers/corpus-inbox-watcher/` (separate Python service, not a Hermes plugin) — none — optional (recommended; default ON)
13. **Backup destination** — Google Drive folder (or local fallback) — sleep-cycle Job 10 (`corpus-backup`) — Google OAuth — optional (recommended)

Custom integrations (CRM, Stripe, Notion, Slack, accounting, industry-specific) are added by copying `plugins/_template/` and appending a row. Pattern documented in `references/integrations-pattern.md`.

---

## §10. Install — `bash install.sh` (Single Command)

The single supported install entry. **`hermes skills install <repo>` is NOT supported** because it skips DB init, plugin symlinks, namespace creation, and the backup-key flow. `README.md` and `install/README.md` say so explicitly.

```bash
git clone <owner>/solomon && cd solomon && bash install.sh
```

Or, for recovery on a fresh laptop:

```bash
git clone <owner>/solomon && cd solomon && bash install.sh --restore <path-or-url-to-tarball>
```

**`install.sh` flow** (idempotent, every step skippable when already-done):

1. **Fresh-vs-restore disambiguation**. Prompt:
   > Choose: [1] Fresh install — generate a new backup key and start blank intake. [2] Restore from backup — point me at a tarball. [3] Other — show advanced options.
   If `[1]` is chosen but `corpus/raw/` or `db/solomon.db` already has content, refuse to generate a new key and switch to a "did you mean `--restore`?" prompt.
2. **Detect Hermes**. If absent: print one-line install link (`curl https://get.hermes-agent.nousresearch.com | bash`) and exit cleanly.
3. **Reuse existing Hermes config**. Read `~/.hermes/.env`. Anything already set is reused — never re-prompted.
4. **Prompt only for missing required keys**: `PINECONE_API_KEY`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. `EMBEDDING_MODEL` and `EMBEDDING_DIM` default to `text-embedding-3-large` / `3072`.
5. **Optional integrations menu** (multi-select, defaults shown):
   - `[ ]` Google Workspace (Gmail + Calendar + Drive — also asks for `GOOGLE_MCP_SERVER_URL`)
   - `[ ]` Whoop
   - `[ ]` Plaud
   - `[ ]` n8n / make.com
   - `[x]` **Corpus auto-ingest watcher** (default ON — installs `watchdog`, symlinks `plugins/corpus-inbox-watcher/`)
   - `[ ]` Add custom integrations later
6. **Symlink** repo to `~/.hermes/skills/solomon/`; symlink each `plugins/*/` to `~/.hermes/plugins/`. Idempotent.
7. **Initialize** `db/solomon.db` from `db/schemas/*.sql` if missing. Set `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;` on first open and on every subsequent connection (every Solomon plugin and worker that opens the DB applies these pragmas — they are NOT injected by Hermes per §2.4.6 verification). This ensures concurrent writes from the plaud-ingest worker, the corpus-inbox-watcher worker, the pipeline-tick worker, the Hermes gateway, and Job 11 don't throw `database is locked`. Includes the 12 new tables (captured_items, coverage, vocabulary, ingested_files, mentoring_queue, sessions, clarification_queue, wiki_vectors, events, working_memory, scope_autonomy, proposed_rules) plus the 5 carry-over tables, plus per-worker state tables for any locked ingress integrations (v1: just plaud_state).
8. **Generate or restore the backup key** (BIP-39 flow from §2.10).
9. **Create the Pinecone serverless index** named `solomon` (or whatever `PINECONE_INDEX_NAME` is set to; default `solomon`) with `dimension=EMBEDDING_DIM`, `metric=cosine`, and the cheapest serverless tier (us-east-1 by default, owner-overridable via `PINECONE_REGION`). If the index already exists with a different dim, fail with explicit message. **Then** create the 4 namespaces inside it (`solomon-corpus-wiki`, `solomon-corpus-raw`, `solomon-captured-items`, `solomon-decision-log`); namespaces are created lazily on first upsert per Pinecone semantics, so this step writes a single zero-vector to each namespace and immediately deletes it to materialize the namespace metadata. Validate dim end-to-end before proceeding.
10. **Verify** plugins load. Surface failures with concrete fixes.
11. **Log** first entry to `decisions/log.md`.
12. **Auto-launch** `hermes -s solomon-onboarding -q "begin"` — owner is dropped straight into Session 0.
13. **Re-run safety**. Re-running just verifies and exits "all good"; never re-prompts intake.

The `solomon-setup` skill is callable manually as `/solomon-setup` to repair or re-onboard but is NOT the install entry.

---

## §11. Verification — Four-Cs + Phase Scorecard

The structure passes when a fresh agent answers all of these from files alone in target time. Body of `/solomon-audit`.

| Test | Source files | Target |
|---|---|---|
| Context: "What does the owner sell, to whom, this quarter's priorities?" | `context/about-business.md`, `context/priorities.md`, `foundation/00-industry.yaml` | < 30s |
| Context: "What's a hard rule the owner will never break?" | `foundation/05-non-negotiables.yaml`, `db.captured_items WHERE domain='non-negotiables'` | < 15s |
| Connections: "Where does revenue land and how does Solomon reach it?" | `connections.md`, `references/api-*.md` | < 30s |
| Connections: "Is Pinecone configured?" | `connections.md` row 1, `.env`, `plugins/pinecone-bridge/plugin.yaml` | < 15s |
| Connections: "Can Solomon read the owner's Gmail and Calendar?" | `connections.md` row 3, `references/api-google-workspace.md` | < 20s |
| Connections: "How do I add a new tool the owner uses?" | `references/integrations-pattern.md`, `plugins/_template/` | < 30s |
| Capabilities: "What skill processes a Plaud voice transcript?" | `skills/runtime/solomon-listening-agent/SKILL.md` | < 20s |
| Capabilities: "What's the orchestrator pipeline order?" | `references/orchestrator-pipeline.md` | < 30s |
| Capabilities: "Which skills run during interview vs decision phase?" | `references/interview-architecture.md`, SKILL.md `phase` fields | < 30s |
| Cadence: "What ran in the last sleep cycle and when's the next mentoring session?" | `orchestrator/sleep-cycle/README.md`, `decisions/log.md` tail | < 45s |
| Mindset: "What does the owner believe about how decisions get made?" | `foundation/01-belief-system.yaml`, `03-principles.yaml` | < 30s |
| Voice: "Give me the owner's voice register in one paragraph." | `references/voice.md`, `db.vocabulary ORDER BY frequency DESC LIMIT 30` | < 15s |
| Interview: "What domains are most under-probed right now?" | `db.coverage WHERE gap_score > 0.4` | < 20s |
| Interview: "Are there any contradicting rules in the captured store?" | `db.captured_items WHERE conflicts_with IS NOT NULL` | < 20s |
| Interview: "How do I resume a half-finished onboarding session?" | `db.sessions` table, `solomon-onboarding/SKILL.md` resumption rule | < 20s |
| Interview: "Where do real-time contradictions go for resolution?" | `db.clarification_queue` schema, `solomon-interview-engine/SKILL.md` | < 20s |
| Corpus: "What does the wiki say about customer Acme Corp?" | `corpus/wiki/entities/customer-acme-corp.md`, Pinecone `solomon-corpus-wiki` | < 20s |
| Corpus: "Where can I drop a new SOP, and what happens after?" | `corpus/README.md`, `solomon-corpus-ingest/SKILL.md`, `plugins/corpus-inbox-watcher/README.md` | < 20s |
| Corpus: "Is the inbox watcher running, and what's its debounce window?" | `plugins/corpus-inbox-watcher/plugin.yaml`, `connections.md` row 12 | < 20s |
| Corpus: "How does Solomon avoid double-ingesting the same file?" | `db.ingested_files` schema, `solomon-corpus-ingest/SKILL.md` (sha256 rule) | < 20s |
| Corpus: "How do I delete a customer's data on request?" | `solomon-corpus-forget/SKILL.md` | < 20s |
| Corpus: "Where do flagged contradictions go and who resolves them?" | `db.mentoring_queue` schema, `solomon-mentoring-session/SKILL.md` | < 30s |
| Corpus: "Are any wiki pages stale, contradictory, or holding orphaned vectors?" | `corpus/log.md` last lint run, `solomon-corpus-lint/SKILL.md`, `db.wiki_vectors` schema | < 20s |
| Operations: "How do I install Solomon?" | `README.md`, `install/README.md` (must say `bash install.sh` only) | < 15s |
| Operations: "When was the last backup, and where did it land?" | sleep-cycle Job 10, `connections.md` row 13, `archives/backups/` | < 30s |
| Operations: "If my laptop dies tomorrow, how do I recover Solomon?" | `install/bootstrap.md` (restore section), `EXPANSIONS.md` (security) | < 45s |
| Operations: "What embedding model and vector dim is in use?" | `references/api-pinecone.md`, `.env` `EMBEDDING_MODEL` / `EMBEDDING_DIM` | < 15s |
| Operations: "What's the canonical decision-log entry format?" | `decisions/log.md` header, `references/orchestrator-pipeline.md` | < 15s |
| Operations: "How does the mentoring queue rank items?" | `db/schemas/mentoring_queue.sql` header comment | < 30s |
| Operations: "When do captured_items get embedded into Pinecone?" | sleep-cycle Job 11 (`embed-pending`), `db.captured_items.embedded_at` column | < 20s |
| Portability: "If we ported off Hermes to Claude, what changes?" | `references/portability.md` | < 30s |
| Pipeline: "What is the orchestrator's stage order and which model runs each stage?" | `§2.2.5`, `§2.11` LLM model assignments | < 30s |
| Pipeline: "How does Solomon block an action that violates a hard rule?" | `foundation/05-non-negotiables.yaml` schema, `§2.2.5` Stage 4 | < 30s |
| Pipeline: "What's the autonomy level of each scope?" | `db.scope_autonomy`, `§2.11` autonomy spectrum | < 20s |
| Operations: "What does Solomon do when Pinecone is unreachable?" | `§2.4.7` failure-handling table | < 20s |
| Operations: "How does the owner approve or edit a one-tap suggestion?" | `§2.4.8` Telegram bot, inline button callback flow | < 20s |
| Operations: "When does the sleep cycle run and how do I trigger it manually?" | `§2.9` scheduling note, `/solomon-sleep-now` command | < 15s |
| Operations: "What keeps Hermes running between Telegram messages?" | `§2.4.9` process supervisor (Hermes gateway + 3 worker services as launchd/systemd units) | < 20s |
| Operations: "Where do owner rules in SOPs and emails get surfaced for confirmation?" | `db.proposed_rules` schema, `solomon-corpus-ingest` rule-extraction pass, `mentoring_queue.source = corpus_rule_proposal` | < 30s |
| Operations: "Why isn't Solomon's plugin contract using ctx.subscribe / ctx.schedule / ctx.db?" | `§2.4.6` verified Hermes API (no pubsub, gateway-level cron, plugins manage own DB), `§2.4.6.5` workers pattern | < 30s |
| Operations: "How are concurrent SQLite writes handled?" | `§10` step 7 WAL + busy_timeout pragmas, `db/README.md` | < 15s |
| Operations: "How is the Pinecone index created on install?" | `§10` step 9 (index creation before namespaces) | < 20s |
| Operations: "How do I recover Solomon if my laptop dies and I only have the BIP-39 mnemonic?" | `§2.10` recovery-on-dead-laptop section, default-local destination | < 30s |
| Operations: "If no session has run for 3 months, how do hand-edited foundation YAMLs reconcile?" | `§2.9` Sleep-Cycle Job 12 yaml-reconcile | < 20s |
| Pipeline: "How does the System 1 vs System 2 divergence check work without burning embeddings?" | `§2.2.5` Stage 7b (token-Jaccard, no API call) | < 20s |

**Pass threshold**: 45/45 from files alone, total agent walltime < 14 min. Run weekly via `/solomon-audit`. Score deltas land in `decisions/log.md`.

---

## §12. Migration Plan (19 Steps)

1. `mkdir /Users/kekeliefu/Documents/Project Solomon/solomon/` and `git init` it.
2. Download Karpathy's LLM Wiki gist (<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>) to two locations: `Support Information/Nate Support/karpathy-llm-wiki.md` (reference) and `solomon/archives/karpathy-llm-wiki.md` (bundled with the repo). Update [Nate Support/README - Links.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/README%20-%20Links.md) to point to the local copy.
3. Copy AIS-OS scaffolding as starting templates: `LICENSE`, `.gitignore`. Author `EXPANSIONS.md` with six pinned sections: (1) Portability — non-Hermes paths, (2) Security — full BIP-39 backup-key flow + key rotation + redaction allowlist + encryption at rest, (3) Multi-device — three forward paths (single-VPS, distributed SQLite via Turso/LiteFS, cloud-native deployment), (4) Cloud-native deployment — deferred Hermes-cloud-deployment idea, (5) What we considered and rejected — design graveyard incl. `hermes skills install` as primary path (rejected: skips DB init), (6) **Hermes sub-agents** — when Solomon needs parallel reasoners (research, multi-domain audit), spawned via Hermes `delegate_task`. Distinct from v1 Solomon `workers/` (which are OS-supervised Python services, §2.4.6.5). Sub-agents are out of scope for v1; v1 runs all reasoning in the main Hermes agent.
4. Create `archives/` and copy in (don't move): `orchestrator-design-original.md`, `solomon-spec-v1.0.md`, `solomon-spec.md`, `12-DECISIONS-RESOLVED.md`, `MEMORY-ENTRIES.md`, `spec-open-question-resolution/`, plus the ELIZA `MAD-SLIP_transcription.txt` as `archives/eliza-source-MAD-SLIP.txt`, plus `karpathy-llm-wiki.md`.
5. Author root Hermes primitives:
   - `SOUL.md` (Solomon identity, includes ELIZA listening rule scoped to interview phase)
   - `MEMORY.md` (empty stub with format header)
   - `USER.md` (empty stub)
   - `.env.example` (all required + optional keys per §2.11)
6. Create `foundation/` with 7 YAML stubs + `_schemas/` placeholders. Header comment on each: "Derived summary; canonical store is db/schemas/captured_items.sql."
7. Create `corpus/` skeleton: `README.md`, `schema.md` (page templates and conventions, derived from `archives/karpathy-llm-wiki.md`), `index.md` stub, `log.md` stub, `inbox/`, `raw/{sops,emails,messages,docs,data}/`, `wiki/{entities,concepts,playbooks}/` directories with `.gitkeep`.
8. Create `references/` and author 22 reference docs:
   - From AIS-OS: `3ms-framework.md`, `4cs-framework.md`
   - From ELIZA: `eliza-listening.md` (interview phase only; what we borrow vs ignore vs add)
   - **NEW**: `interview-architecture.md` (two-phase model, captured-items schema, skill chain — distilled §0–§2.2)
   - **NEW**: `corpus-llm-wiki.md` (Karpathy attribution + Solomon's Pinecone-extended adaptation — distilled §2.3–§2.5)
   - New: `autonomy-spectrum.md`, `hermes-skill-pack.md`, `portability.md`, `integrations-pattern.md`
   - Distilled from `archives/orchestrator-design-original.md`: `orchestrator-pipeline.md`, `sleep-cycle-jobs.md` (12 jobs incl. J9 corpus-lint + J10 corpus-backup + J11 embed-pending + J12 yaml-reconcile), `retrieval-5-lane.md` (5 strategies; Lane 1 queries 4 namespaces — orthogonal axes), `system1-system2.md`
   - `voice.md` template
   - `api-*.md`: Pinecone, Telegram, Google Workspace, Workflow, Whoop, Plaud, Transcription (whisper.cpp / Whisper API), OCR (pytesseract / Google Vision)
9. Create `context/` with 4 templates: `about-me.md`, `about-business.md`, `priorities.md`, `owner-state.md`.
10. Create `orchestrator/` skeleton: `README.md` + `pipeline/`, `sleep-cycle/` (with stubs for 12 jobs: hindsight, archival, surprise-replay, stress-test, conflict-detection, working-memory-cleanup, autonomy-reeval, mentoring-scheduler, **corpus-lint**, **corpus-backup**, **embed-pending**, **yaml-reconcile**), `schemas/` with stub READMEs.
11. Create `memory/` (README + working-memory + pinecone-index documenting the 4 namespaces with default weights).
12. Create `db/schemas/` with all `*.sql` files: 12 new shared tables (`captured_items.sql`, `coverage.sql`, `vocabulary.sql`, `ingested_files.sql`, `mentoring_queue.sql`, `clarification_queue.sql`, `sessions.sql`, `wiki_vectors.sql`, `events.sql`, `working_memory.sql`, `scope_autonomy.sql`, `proposed_rules.sql`) + 5 carry-over (`decisions.sql`, `audits.sql`, `biometrics.sql`, `rules_of_thumb.sql`, `mentoring_sessions.sql`) + per-worker state tables (`plaud_state.sql` is the only locked one for v1; others added when their ingress spec is locked). Embedded tables (`captured_items`, `decisions`) get an `embedded_at` column; vocabulary stays SQL-only. README documents the canonical-store-vs-derived-YAML relationship, idempotency-via-sha256, the embed-pending pattern, the wiki-vector cleanup rule, the per-worker-state-table convention, the events/working-memory pipeline writes, and the corpus-rule-promotion workflow via proposed_rules.
13. Create `decisions/log.md` in the §2.11 canonical format. Port the 12 v1 decisions from `archives/12-DECISIONS-RESOLVED.md` via an LLM pass that rewrites each into the canonical four-field structure (Decision / Why / Alternatives considered / Owner). Original prose preserved under a `<details>` block per entry, excluded from embedding. Date cascade: git first-commit ISO date → file mtime → `## UNKNOWN-DATE — <Title>` queued in `mentoring_queue` (source = `legacy_decision_undated`, priority 6).
14. Create the **two-family plugin/worker layout** per §2.4.6 + §2.4.6.5:
    - `solomon/hermes-plugins/<name>/` — Hermes plugins (stateless event handlers; verified API). v1 plugins: `_template-hermes-plugin/`, `solomon-pipeline-injector/` (the `pre_llm_call` hook that classifies inbound messages and writes `db.events`), `pinecone-bridge/` (provides Pinecone tools to skills), `google-workspace/` (provides Gmail/Calendar/Drive tools via Google MCP), `workflow-bridge/` (n8n/make.com webhook tool), `whoop-bridge/` (Whoop biometrics tool). Each: `plugin.yaml` + `__init__.py` (with `register(ctx)`) + `README.md`. The deferred-spec ones (`google-workspace`, `workflow-bridge`, `whoop-bridge`) ship with `_TODO_SPEC.md` per §2.4.5.
    - `solomon/workers/<name>/` — long-lived Python services (separate processes, supervised by launchd/systemd per §2.4.9). v1 workers: `_template-worker/`, `plaud-ingest/`, `corpus-inbox-watcher/`, `pipeline-tick/`. Each: `worker.yaml` + `__main__.py` (the `python -m solomon.workers.<name>` entrypoint) + `README.md`. The `plaud-ingest` worker gets a real implementation per §2.4.5 (IMAP IDLE + 60s poller + UNSEEN+FROM search + `\Seen` marking + dedup set + ISO-timestamped filenames + `db.plaud_state`). The `corpus-inbox-watcher` worker gets a real watchdog implementation per §2.4 (30s debounce + 5-reset/5-min cap + 3s file-stable + recursive watch + catch-up + sha256 manifest dedup). The `pipeline-tick` worker scans `db.events WHERE status='pending'` every 60s and spawns Hermes agent sessions per pending event (max 5 in-flight).
    - `_template-hermes-plugin/` and `_template-worker/` document the two patterns. Owners add custom integrations by copying the right template.
    - The Telegram adapter is **NOT a Solomon plugin** — it's the Hermes gateway built-in adapter (§2.4.8). Configured via `hermes gateway setup` during install.
15. Create `install/` (README, bootstrap.md, post-install-skill.md) and root `install.sh` (~80–100 lines, the §10 flow). Install also creates the 4 Pinecone namespaces if missing and primes `corpus/index.md` + `corpus/log.md`.
16. Build `skills/` tree: `mkdir` 7 categories. Copy 14 carry-over skills into the right categories (drop `solomon-profile`; move `spec-open-question-resolution` to `archives/`). Author 13 net-new skills:
   - 5 interview: `solomon-interview-engine` (with seeded `probe_library/` for 6 domains: pricing, hiring, ops, customer, vendor, finance, plus `_generic.yaml`, plus `probe_library/README.md` pinning the schema + semver convention), `solomon-extraction`, `solomon-vocabulary-capture`, `solomon-coverage-tracker`, `solomon-contradiction-check`
   - 4 corpus: `solomon-corpus-ingest`, `solomon-corpus-lint`, `solomon-corpus-query`, `solomon-corpus-forget`
   - 1 utility: `solomon-redact` (with fixtures/ folder for CI)
   - 1 runtime: `solomon-profile-loader` (replaces `solomon-profile`)
   - 2 learning: `solomon-audit`, `solomon-level-up` (adapted from AIS-OS)
   Total: 14 + 13 = **27 skills**.
17. Apply uniform `SKILL.md` front-matter (incl. `phase` field per §2.11) to every skill. Update each `solomon-onboarding-NN-*` to delegate to the interview-engine chain rather than handle Q&A directly.
18. Author root `README.md`, root `CLAUDE.md` (§7 headings), `intake.md` (7 sessions + Q0), `connections.md` (13 rows), and `corpus/schema.md` (routing extension map, redaction allowlist/blocklist patterns, file size + type limits, transcription/OCR backend choice).
19. Add CI infrastructure: `.github/workflows/ci.yml` running `pytest tests/`. Tests cover `solomon-redact` against fixtures, the `phase` loading rule (interview-phase entry points load only `phase: interview` and `phase: utility`; decision-phase entry points load only `phase: decision` and `phase: utility`; utilities never load other utilities), SQLite schema migration (up/down idempotent), SHA256 manifest dedup, and `clarification_queue` end-to-end flow. Run on every PR.

---

## Critical Files to Read Before Implementation

- [orchestrator-design-original.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/orchestrator-design-original.md) — source for 4 distilled `references/*.md` runtime docs
- [solomon-spec-v1.0.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/solomon-spec-v1.0.md) — confirms Hermes skill-pack canonical
- [12-DECISIONS-RESOLVED.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/solomon-backup%202/12-DECISIONS-RESOLVED.md) — initial entries for `decisions/log.md`
- [Hermes-Agent/CLAUDE.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Hermes-Agent/CLAUDE.md) — Hermes binding contract
- [Hermes-Agent/wiki/](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Hermes-Agent/wiki/) — skill / plugin / install conventions
- [Nate AIS-OS CLAUDE.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/CLAUDE.md) — template for root `CLAUDE.md`
- [Nate AIS-OS aios-intake.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/aios-intake.md) — template for `intake.md`
- [Nate AIS-OS connections.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/connections.md) — template for `connections.md`
- [Nate AIS-OS .claude/skills/](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/AIS-OS/.claude/skills/) — adapt `audit/` and `level-up/`
- [the-3ms-framework.html](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/the-3ms-framework.html) and [the-four-cs-of-an-aios.html](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Nate%20Support/the-four-cs-of-an-aios.html)
- [ELIZA.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/ELIZA/ELIZA.md) and [MAD-SLIP_transcription.txt](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/ELIZA/MAD-SLIP_transcription.txt) — sources for `references/eliza-listening.md` and the seeded `probe_library/`
- Karpathy LLM Wiki gist at <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f> — to be downloaded into `Support Information/Nate Support/` and `solomon/archives/`; source for `references/corpus-llm-wiki.md` and `corpus/schema.md`
- [Solomon — A personal business brain.md](/Users/kekeliefu/Documents/Project%20Solomon/Support%20Information/Solomon%20—%20A%20personal%20business%20brain.md) — vision context

---

## Constraints Respected

- **Hermes is the canonical runtime.** SOUL/MEMORY/USER at root; `skills/` matches Hermes resolution; `hermes-plugins/` matches Hermes plugin loader (verified API per §2.4.6); `workers/` are Solomon's OS-supervised Python services (§2.4.6.5). **Install path is `bash install.sh` only**; `hermes skills install` is explicitly NOT supported. v1 runs the Hermes gateway daemon plus three workers; Hermes sub-agents (via `delegate_task`) are deferred to v2 (EXPANSIONS.md section 6).
- **Two-phase architecture is enforced.** Every `SKILL.md` carries a `phase: interview|decision` field (§2.11 table). Interview-phase skills probe and reflect; decision-phase skills act and never reflect. Phases share data, not code paths. CI tests assert no skill loads under the wrong phase (§12 step 19).
- **ELIZA is borrowed, not copied.** Reflective interviewer style + keyword-triggered probing + verbatim echoing + decomposition + ranked fallbacks are taken (§2.1). Canned non-answers are dropped. Runtime script editing is dropped — `probe_library/` is read-only and ships with the skill.
- **Captured items are structured first-class data.** SQLite tables (`captured_items`, `coverage`, `vocabulary`) are the canonical store (§1); the 7 foundation YAMLs are derived summaries. Confidence (stated/repeated/exemplified), contradictions, and source-turn tracking are native columns. DB always wins over YAML hand-edits (§1).
- **Vocabulary becomes voice.** `vocabulary` table feeds both interview probes (verbatim slot fillers) and decision-phase outputs.
- **Pinecone is required and concrete.** Plugin scaffold + connections row 1 + `.env.example` entries + `references/api-pinecone.md` + `memory/pinecone-index.md` documenting all 4 namespaces with default weights (§2.8).
- **Bulk corpus ingestion follows Karpathy's LLM Wiki pattern, adapted for Pinecone.** `corpus/raw/` is immutable; `corpus/wiki/` is LLM-maintained; both feed Pinecone under separate namespaces; wiki pages outrank raw at retrieval time (§2.3, §2.8).
- **Inbox auto-ingest is plug-and-drop.** `plugins/corpus-inbox-watcher/` is a `watchdog`-based Hermes plugin that debounces 30s (capped at 5 resets / 5 minutes), waits 3s for file-stable size, batches bursts, catches up on startup, never mutates files, logs failures (§2.4). Default ON in the install menu.
- **Operational rules are explicit, not implicit.** Routing, idempotency (sha256 manifest), duplicate detection, restart recovery, concurrency lock, file size/type limits, PII redaction, transcription/OCR backends are pinned in §2.5–§2.6. Forget cascade, mentoring queue, clarification queue, sessions table, stale rule, contradiction flow are pinned in §2.7. Retrieval (5 lanes / 4 namespaces / weights) is pinned in §2.8. Sleep cycle (12 jobs) is pinned in §2.9. Backup, restore, key recovery are pinned in §2.10. Pinned defaults (embedding model, decision-log format, vocabulary normalization, session-complete thresholds, machine ID, priority assignments, phase table, env vars) are in §2.11. No "TBD" left.
- **Google Workspace is first-class.** Single plugin covers Gmail + Calendar + Drive (Docs, Sheets) via Google MCP. `GOOGLE_MCP_SERVER_URL` + OAuth required.
- **Workflow orchestrators are first-class.** `plugins/workflow-bridge/` accepts either n8n or make.com via webhook URL.
- **Custom integrations are easy.** `plugins/_template/` + `references/integrations-pattern.md` = copy folder, edit `plugin.yaml`, restart.
- **OpenAI is the v1 embedding provider.** `text-embedding-3-large` at 3072 dims, deterministic at install. Other providers are an EXPANSIONS.md future expansion only.
- **Portability is preserved.** `references/portability.md` and `portable: true` SKILL.md flags mean a port to a non-Hermes agent is a documented swap, not a rewrite.
- **Foundation interviews preserved.** All 7 onboarding skills + `intake.md` paste alternative; both back onto `solomon-interview-engine`.
- **Distribution is GitHub-native and one-command.** `bash install.sh` is the only supported install command; auto-launches Session 0 on completion.
- **Source folders untouched.** Originals copied (not moved) into `solomon/archives/`.
- **No new conceptual frameworks invented.** Solomon's terms + Three Ms / Four Cs from AIS-OS + Hermes' SOUL/MEMORY/USER + ELIZA's interview technique + Karpathy's LLM-Wiki pattern. Nothing else.

---

## Open Questions for v2.1

Real items, not blocking lock. File these for the next consolidation pass:

- `install.sh` real line count is closer to ~300 than the 80–100 estimate in §12 step 15; update the estimate to "~200–350 lines depending on prompt verbosity" when authoring the actual script.
- spaCy `en_core_web_sm` is English-only. Non-English owners need a different model. Out of scope for v1; flag in `EXPANSIONS.md` security section.
- v1 `solomon-corpus-query` is read-only. v2.1 may re-introduce Karpathy's "auto-file synthesized answers back as new concept pages" behavior, but only with a precise durability rule (proposed criteria: same query asked ≥3 times across ≥2 sessions AND answer stable across runs).
- Hermes **sub-agents** (parallel reasoners via `delegate_task`) are deferred to v2. EXPANSIONS.md section 6 holds the contract sketch. v2.1 audit should re-check whether any v1 skill became heavy enough to justify offloading. Note: this is distinct from v1 `workers/` (OS-supervised Python services, §2.4.6.5), which ship in v1.
- **Per-source ingress specs** for Telegram, Google Workspace (Gmail / Calendar / Drive), Whoop, and n8n/make.com webhook are pending owner sign-off (§2.4.5 table). Each must reach Plaud-equivalent depth (idempotency token, dedup mechanism, filename convention, `corpus/inbox/<category>/` target, env-var list, persistent state table) before its plugin scaffold is implemented. Until each spec lands, the plugin ships only the `_TODO_SPEC.md` placeholder.
