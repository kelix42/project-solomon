# Solomon — Technical Specification

Version: 1.0 (baseline, implementation-ready)
Status: locked — all 12 design questions resolved, internal consistency pass complete
Target runtime: Hermes agent framework
Authors: Lynx + Sunny
Last updated: 2026-05-06

Changes from 0.1 → 1.0: all 12 deferred design decisions resolved into the
spec body (see §14); internal consistency pass closed 8 critical and 10
minor issues across schema, cross-references, and prose. From this point
forward, schema or behavior changes go through `solomon-migrate` (§12.6)
and a versioned spec bump.

---

## 1. Overview

Solomon is a skill pack for the Hermes agent framework. It turns a stock Hermes
instance into a personalized chief-of-staff agent for a single business owner.

It is not a product, not a SaaS, and not a standalone application. It is a
collection of Hermes skills, a profile directory layout, and a SQLite database
that together implement a long-running learning loop.

Audience: a single business owner — a founder, principal, sole operator, or
managing partner — who already runs Hermes on a machine they control and who
wants the agent to absorb their decision patterns.

Core promise: given 30 days of structured onboarding plus continuous voice
input (Plaud transcripts), Solomon will move from "summarize and propose" to
"clone the owner's decision-making" for the routine 80% of business choices.
Every decision the owner approves, edits, or rejects becomes training signal.
Over time the bar for owner involvement rises; the agent absorbs the floor.

Out of scope:
- Multi-tenant operation. One Solomon instance serves one owner.
- Acting without owner approval until biometric and audit gates are passed.
- Replacing the owner on judgement-bound decisions (legal, ethical, family).

---

## 2. Architecture

Solomon ships as a Hermes skill pack. There is no daemon, no web app, no
separate process. Hermes itself is the runtime.

Layout under a Hermes installation:

```
/opt/data/skills/solomon/        # the skill pack (this repo)
  solomon-setup/SKILL.md
  solomon-guide/SKILL.md
  solomon-profile/SKILL.md
  solomon-onboarding-*/SKILL.md
  solomon-listening-agent/SKILL.md
  solomon-decision-log/SKILL.md
  solomon-mentoring-session/SKILL.md
  solomon-calibrate-biometrics/SKILL.md   # day-28 calibration, see §7.2
  solomon-export/SKILL.md                 # backup bundle producer, see §12.1
  solomon-import/SKILL.md                 # bundle restore, see §12.2
  solomon-migrate/SKILL.md                # explicit schema migration, see §12.6
  ...

/opt/data/solomon/               # owner-specific data (created at setup)
  profile/                       # YAML knowledge files
  decisions/                     # decision log
  mentoring/                     # mentoring session records
  ingestion/                     # raw incoming events (transcripts, etc)
  solomon.db                     # SQLite history store
```

Three runtime components, all hosted by Hermes:

1. Skills — procedural memory. Each skill is a markdown file with YAML
   frontmatter that Hermes loads on demand. Skills are stateless; they read
   and write profile files, the database, and Hermes memory.

2. Memory — durable identity facts surfaced in every prompt. Solomon writes
   here only the highest-signal items (non-negotiables, identity, top goals).
   Tagged with prefixes like `[solomon-profile]`, `[solomon-learning]`.

3. Sub-agents — Hermes can spawn ephemeral task agents for narrow jobs
   (drafting an invoice reply, processing a transcript). Promoted sub-agents
   become persistent profiles (see Section 8).

There is no Solomon binary. Installing Solomon means dropping a directory of
skill files into a Hermes skills path and running the setup skill once.

---

## 3. Storage Triad

Solomon stores state in exactly three places. Every write goes to one of them
and the choice is determined by the data's nature, not its size.

| Store        | Purpose                                | Format            | Mutable |
|--------------|----------------------------------------|-------------------|---------|
| Memory       | Identity — who the owner is, what they will never do | Hermes memory entries | Slow, deliberate |
| Skill files  | Knowledge — beliefs, principles, taxonomy, procedures | YAML + Markdown | Versioned, editable |
| solomon.db   | History — every event, decision, audit, biometric reading | SQLite | Append-mostly |

Rules:
- A fact lives in exactly one of these. Duplication is a bug.
- Memory is the smallest and slowest-changing. If it can live in YAML, it
  lives in YAML.
- Skill files are the canonical source of truth for what Solomon knows.
- solomon.db is the canonical source of truth for what Solomon has done.

### 3.1 solomon.db schema sketch

SQLite, single file at `/opt/data/solomon/solomon.db`. Created by
`solomon-setup`. All tables use integer primary keys and ISO-8601 timestamps
in UTC.

```sql
-- Raw incoming events from any input adapter.
CREATE TABLE events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            TEXT    NOT NULL,                -- ingestion timestamp (UTC)
  source        TEXT    NOT NULL,                -- 'plaud_email' | 'twilio_sms' | ...
  source_device TEXT,                            -- 'plaud' | 'phone' | 'manual_upload' (for §4.3 dedup)
  external_id   TEXT,                            -- upstream message id, dedup key
  payload_path  TEXT    NOT NULL,                -- file under ingestion/
  scope         TEXT,                            -- top-level scope after triage
  subscope      TEXT,                            -- user-defined sub-scope
  status        TEXT    NOT NULL,                -- 'new'|'processed'|'skipped'|'error'|'duplicate'
  dedup_with    INTEGER REFERENCES events(id),   -- if duplicate, points at the kept event
  processed_at  TEXT,
  UNIQUE(source, external_id)
);

-- Three-pass output for each transcript-like event.
CREATE TABLE transcripts (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id      INTEGER NOT NULL REFERENCES events(id),
  summary       TEXT,                            -- Pass 1
  learnings     TEXT,                            -- Pass 2 (JSON array)
  actions       TEXT,                            -- Pass 3 (JSON array)
  is_private    INTEGER NOT NULL DEFAULT 0
);

-- Every decision proposed by Solomon and the owner's response.
CREATE TABLE decisions (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  ts              TEXT    NOT NULL,
  source_event_id INTEGER REFERENCES events(id),
  scope           TEXT    NOT NULL,
  subscope        TEXT,
  counterparty    TEXT,                          -- third party named in the decision, if any. Used by §6.2.2 retrieval.
  context         TEXT    NOT NULL,
  proposed        TEXT    NOT NULL,
  hard_gate       TEXT    NOT NULL,              -- 'pass'|'block'|'flag'
  soft_gate       TEXT    NOT NULL,              -- 'pass'|'block'|'flag'|'unavailable'
  autonomy_band   TEXT    NOT NULL,              -- 'red'|'yellow'|'green' at decision time
  owner_response  TEXT,                          -- 'approved'|'edited'|'rejected'|'pending'
  owner_edit      TEXT,
  rejection_reason TEXT,
  learning        TEXT,
  responded_at    TEXT
);

-- Audit trail of gate evaluations (one row per evaluation, both gates).
CREATE TABLE audits (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  decision_id  INTEGER NOT NULL REFERENCES decisions(id),
  layer        TEXT    NOT NULL,                 -- 'hard'|'soft'
  rule_id      TEXT,                             -- only for hard gate
  outcome      TEXT    NOT NULL,                 -- 'pass'|'block'|'flag'
  rationale    TEXT,
  evaluated_at TEXT    NOT NULL
);

-- Biometric signal driving autonomy ceilings.
CREATE TABLE biometrics (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            TEXT    NOT NULL,
  source        TEXT    NOT NULL,                -- 'whoop'
  recovery_pct  INTEGER,                         -- 0-100
  hrv_ms        REAL,
  rhr_bpm       REAL,
  sleep_hours   REAL,
  band          TEXT    NOT NULL                 -- derived: 'red'|'yellow'|'green'
);

-- Recurring task patterns. Counts toward sub-agent promotion threshold.
CREATE TABLE task_patterns (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  signature       TEXT    NOT NULL UNIQUE,       -- normalized pattern key
  description     TEXT    NOT NULL,
  scope           TEXT    NOT NULL,
  occurrences     INTEGER NOT NULL DEFAULT 0,
  first_seen      TEXT    NOT NULL,
  last_seen       TEXT    NOT NULL,
  promoted        INTEGER NOT NULL DEFAULT 0,
  promoted_at     TEXT,
  promoted_skill  TEXT                           -- name of resulting skill, if any
);

-- Structured rules-of-thumb. See Section 9.
CREATE TABLE rules_of_thumb (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  scope         TEXT    NOT NULL,
  subscope      TEXT,
  statement     TEXT    NOT NULL,                -- the rule, plain English
  condition     TEXT,                            -- JSONLogic predicate (JSON string), optional. See §9.3.
  confidence    REAL    NOT NULL,                -- 0.0 - 1.0
  evidence_count INTEGER NOT NULL DEFAULT 0,
  contradiction_count INTEGER NOT NULL DEFAULT 0,
  source        TEXT    NOT NULL,                -- 'onboarding'|'mentoring'|'inferred'
  created_at    TEXT    NOT NULL,
  last_reinforced_at TEXT,
  status        TEXT    NOT NULL                 -- 'active'|'suspended'|'retired'
);

CREATE TABLE rule_evidence (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_id     INTEGER NOT NULL REFERENCES rules_of_thumb(id),
  decision_id INTEGER REFERENCES decisions(id),
  kind        TEXT    NOT NULL,                  -- 'reinforce'|'contradict'
  ts          TEXT    NOT NULL,
  note        TEXT
);

-- Mentoring sessions index (the YAML files remain canonical).
CREATE TABLE mentoring_sessions (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  date               TEXT    NOT NULL,
  yaml_path          TEXT    NOT NULL,
  calibration_score  INTEGER,
  triggered_by       TEXT    NOT NULL            -- 'scheduled'|'edit_rate'|'soft_divergence'|'inferred_queue'|'rule_conflict'|'promotion_ready'|'owner_request'|'bundled'
);

-- Profile-vs-inferred rule conflicts. See §9.4.
CREATE TABLE rule_conflicts (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at      TEXT    NOT NULL,
  declared_rule   INTEGER NOT NULL REFERENCES rules_of_thumb(id),  -- onboarding/mentoring source
  inferred_rule   INTEGER NOT NULL REFERENCES rules_of_thumb(id),  -- the suspended one
  evidence_count  INTEGER NOT NULL,                                 -- snapshot at conflict time
  scope           TEXT    NOT NULL,
  subscope        TEXT,
  status          TEXT    NOT NULL,              -- 'open'|'resolved'
  resolution      TEXT,                          -- 'kept_declared'|'updated_declared'|'kept_both'|'retired_inferred' (NULL while open or deferred)
  resolved_at     TEXT,
  resolved_in_session INTEGER REFERENCES mentoring_sessions(id)
);

-- Schema version pointer for solomon-migrate. See §12.6.
CREATE TABLE meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
-- Seeded by solomon-setup with: ('schema_version', '<current code version>')
```

Indexes (assumed, not exhaustive): `events(status, ts)`,
`decisions(ts)`, `decisions(owner_response)`, `audits(decision_id)`,
`biometrics(ts)`, `task_patterns(occurrences)`,
`rules_of_thumb(status, scope)`.

---

## 4. Event Ingestion

Default model: pull-by-default polling. A scheduled Hermes job wakes, asks
each adapter "anything new?", writes raw payloads under
`/opt/data/solomon/ingestion/`, and inserts an `events` row with
`status='new'`. Skills then process new events.

Real-time exception: Twilio (SMS, voice) is permitted to push events via
webhook because SMS latency is part of its value. Twilio writes events
directly into the same table with `source='twilio_sms'` (or `_voice`).

### 4.1 Input adapters

| Adapter            | Mode       | Cadence  | MVP? | Notes |
|--------------------|------------|----------|------|-------|
| `plaud_email`      | Pull (IMAP)| 5 min    | YES  | Mail forwarded by Plaud's AutoFlow. Parse the transcript out of the email body, store as `.txt` payload. |
| `twilio_sms`       | Push       | realtime | No   | Webhook handler; only adapter exempt from polling. |
| `gmail_threads`    | Pull (IMAP/Gmail API) | 15 min | No | Owner's primary inbox, scoped to labeled threads only. |
| `calendar_gcal`    | Pull (API) | 15 min   | No   | Upcoming events, attendee changes, conflicts. |
| `whoop`            | Pull (API) | hourly   | No   | Feeds the biometrics table; not events. |
| `bank_plaid`       | Pull (API) | daily    | No   | Transactions for Financial scope. |

Adapter contract (each adapter is a small Python module or skill that exposes
a `poll()` function):

```
poll() -> list[ {source, external_id, ts, payload_bytes_or_path, hint_scope?} ]
```

The orchestrator deduplicates on `(source, external_id)` and writes the
events table. Adapters never write to other tables.

### 4.2 MVP adapter — Plaud email

1. Hermes cron triggers `solomon-ingest-plaud` every 5 minutes.
2. Skill connects to a configured IMAP mailbox, fetches unseen messages from
   the Plaud sender address, extracts the transcript body and metadata
   (recording timestamp, duration if present).
3. Writes `ingestion/plaud/<external_id>.txt` and a row into `events`.
4. Triggers `solomon-listening-agent` for each new event (three-pass
   processing: summarize, extract learnings, propose actions).

### 4.3 Multi-device input and dedup

v0.1 ships with a single ingestion source (Plaud). No dedup logic is
needed and none is implemented. The `events` table includes a
`source_device` column from day one so multi-device support can be added
without schema migration.

v0.2 adds multi-device support with the following dedup approach (committed
here so it does not get re-litigated later):

- When a new transcript arrives, query `events` for any other transcript
  ingested within the last 10 minutes.
- Compute a normalized hash over the first 200 characters of each
  candidate (lowercase, strip whitespace and punctuation).
- If a hash matches an existing event, treat both as the same conversation:
  keep the higher-priority source, mark the other as superseded by writing
  the kept event's id into the discarded event's `dedup_with` column, and
  do not run the listening agent on the duplicate.
- Source priority is configurable in `profile/ingestion.yaml`. Default
  order: `plaud > phone > manual_upload`.

Known limitations of this approach (documented so they are not surprises):

- Paraphrase-heavy overlap will not dedup. If Plaud caught the first half
  and the phone caught the second half of the same conversation, both will
  ingest. This is judged the correct failure mode — better to surface a
  duplicate than to silently merge two conversations that were actually
  distinct.
- The 10-minute window assumes both devices upload within that span. If a
  phone recording is uploaded hours later, it will ingest as a new event.
  Owner can manually mark it `dedup_with` via a future mentoring tool.

---

## 5. Scope Taxonomy

Every event, decision, and rule lives under exactly one top-level scope and
zero or more user-defined sub-scopes. Top-level scopes are fixed by Solomon;
sub-scopes are created by the owner during onboarding (Session 6) and can
grow over time.

Canonical top-level scopes (v0.1):

| Scope       | Definition |
|-------------|------------|
| Financial   | Money in, money out, cash position, taxes, pricing, contracts with monetary terms. |
| Operational | Day-to-day delivery of work — clients, projects, vendors, scheduling, internal process. |
| Strategic   | Direction of the business — positioning, partnerships, hiring, market choices, multi-month bets. |
| Personal    | Owner's health, family, energy, time off. Restricted from autonomous action. |
| Relational  | People — clients, prospects, peers, mentors, staff. Distinct from Operational because the unit is the relationship, not the project. |
| Legal       | Contracts, IP, compliance, disputes. Always requires owner sign-off; no autonomous action ever. |
| Learning    | Reading, courses, experiments, research. Lowest-stakes scope; useful sandbox. |
| Admin       | Filing, bookkeeping entries, document management, recurring forms. Highest automation candidate. |

Rules:
- A decision must be tagged with exactly one top-level scope before it
  reaches either gate.
- Sub-scopes are free-form strings under a top-level scope, e.g.
  `Operational/clients/acme-law` or `Financial/aging-receivables`.
- Sub-scopes are stored as plain strings in the `subscope` column; no
  separate sub-scope table in v0.1.
- The `Legal` and `Personal` scopes have hard-coded ceilings (see Sections 6
  and 7) regardless of any rule the owner adds.

---

## 6. Audit System

Every proposed decision passes through two layers, in order. Both layers
write to the `audits` table. The decision proceeds to the owner only if both
return `pass` or `flag`; a `block` from either layer kills the proposal and
notifies the owner with the rationale.

### 6.1 Layer 1 — Hard Gate (deterministic)

A rules engine. Inputs:
- The proposed decision (`scope`, `subscope`, `proposed`, `context`).
- Profile non-negotiables (`05-non-negotiables.yaml`).
- Hard-coded scope ceilings (Legal, Personal).
- Current autonomy band (Section 7).

Implemented as a pure function over a list of rule records. Each rule has an
`id`, a `condition` (JSONLogic predicate evaluated against a fixed context
object built from the proposed decision — see §9.3 for the language and the
context schema), and an `action` (`block` | `flag` | `pass`). Rule list is
loaded from `05-non-negotiables.yaml` plus a built-in baseline. There is no
`eval` of free-form code; JSONLogic is a JSON tree of named operators only.

Output: `{outcome, rule_id, rationale}`. Written to `audits` with
`layer='hard'`. Outcome also stored on `decisions.hard_gate`.

If outcome is `block`, processing stops. The decision is still written, with
`owner_response='pending'` and a notification sent to the owner explaining
which rule fired.

### 6.2 Layer 2 — Soft Gate (LLM reasoning)

Only invoked if the hard gate returned `pass` or `flag`. Inputs:
- The proposed decision and its hard-gate outcome.
- The owner's profile (all YAML files in `profile/`).
- A hybrid retrieval over the decision log (see §6.2.2 below) — not a flat
  "last 20" window.
- All `active` rules of thumb relevant to the scope.

The LLM is asked one question: "Would the owner be comfortable with this
proposal, given everything you know about how they think? Answer pass, flag,
or block, and give one paragraph of reasoning."

Output is parsed into `{outcome, rationale}` and written to `audits` with
`layer='soft'`. Outcome stored on `decisions.soft_gate`.

#### 6.2.1 Soft Gate LLM hosting

The Soft Gate model is configurable per scope. Two routing rules apply:

- `Personal` scope — biometrics, health, family, anything containing PII or
  medical data — MUST use a locally-hosted LLM. Personal-scope payloads
  never leave the owner's machine, including for Soft Gate evaluation.
  Specific local model is deferred (see Open Question #2a); the requirement
  is that the runtime is local-capable (Ollama, llama.cpp, vLLM, etc.) and
  the chosen model can follow the Soft Gate prompt format reliably.
- `Operational` and `Strategic` scopes use a hosted LLM by default for
  reasoning quality. Default provider is Anthropic Claude. The provider is
  pluggable via configuration so the owner can swap to OpenAI, a different
  Anthropic tier, or another local model without code changes.

Configuration lives in `profile/audit.yaml`:

```
soft_gate:
  personal:
    provider: local          # required for Personal scope
    model: <deferred>        # owner picks at install time
    endpoint: http://localhost:11434
  operational:
    provider: anthropic      # default; pluggable
    model: claude-sonnet-4
  strategic:
    provider: anthropic
    model: claude-opus-4
```

Degraded-mode behavior: if the configured Soft Gate model for a scope is
unreachable (local model OOM'd, hosted API down, network partition), Solomon
degrades that scope to `suggest-only` mode for the duration of the outage —
same pattern as a Red biometric day. Decisions still flow through the Hard
Gate and are written to the decision log with `soft_gate='unavailable'`,
but no autonomous action ships until the Soft Gate is restored or the owner
manually approves. Solomon MUST NOT silently fall back from a local
Personal-scope model to a hosted one; that would defeat the privacy
guarantee.

#### 6.2.2 Decision-log retrieval for the Soft Gate

The Soft Gate sees a curated subset of the decision log, not a flat last-N
window. The retrieval uses three SQL streams against the `decisions` table
that target three different signals: current temperature, precedent for
this exact relationship/topic, and past corrections. Total budget is
~18 rows so the prompt size stays comparable to the previous "last 20"
default.

| Stream      | Query                                                                                              | Rows |
|-------------|----------------------------------------------------------------------------------------------------|------|
| `recent`    | Last N decisions in the same `scope` as the proposal, ordered by `ts` desc                         | 10   |
| `relevant`  | Last N decisions matching the same `subscope` OR same `counterparty` as the proposal, any scope    | 5    |
| `correction`| Top N scope-matched decisions in the last 90 days where the owner edited or rejected the Soft Gate's recommendation, ordered by `ts` desc | 3 |

Deduplication: if the same decision is returned by more than one stream,
keep it once under its highest-priority tag. Priority order:
`correction > relevant > recent`. Net unique rows are typically 12-18.

Prompt structure: the rows are grouped under three labelled headers in the
Soft Gate prompt — "Recent decisions in this scope", "Decisions involving
this subscope or counterparty", and "Past cases where you and the owner
disagreed". Do not flatten them into a single chronological list; the LLM
treats correction signals very differently from generic recency when it
knows which is which.

Implementation note: all three queries are exact-match SQL — no embeddings
required. If `subscope` and `counterparty` are both null on the proposed
decision, the `relevant` stream returns zero rows and that slot is simply
left empty rather than padded from elsewhere.

### 6.3 Data flow

```
event ──> listening-agent (3 passes) ──> proposed action
            │
            ▼
     decisions row (status: pending gates)
            │
            ▼
     Hard Gate ── block ──> notify owner, stop
            │ pass|flag
            ▼
     Soft Gate ── block ──> notify owner, stop
            │ pass|flag
            ▼
     surface to owner (Telegram) with 1/2/3 options
            │
            ▼
     owner responds ──> decision-log update ──> rule evidence update
```

Both gate outcomes are immutable once written. A new evaluation creates a new
`audits` row.

---

## 7. Biometric Ceilings

Solomon caps its own autonomy based on the owner's recovery state, on the
theory that a tired owner should not have an over-eager agent shipping
decisions in their name.

Source of truth in v0.1: Whoop. The `biometrics` table is updated hourly by
the Whoop adapter. The `band` column is derived at write time from
`recovery_pct`. Default thresholds match Whoop's own bands so the numbers
Solomon uses match what the owner already sees in the Whoop app:

| Band   | Whoop recovery | Meaning |
|--------|----------------|---------|
| Green  | 67-100         | Owner is well-recovered. Maximum autonomy permitted. |
| Yellow | 34-66          | Owner is mid-recovery. Partial autonomy; bias to surface. |
| Red    | 0-33           | Owner is depleted. Minimum autonomy; everything goes through the owner. |

These are placeholders in the same sense Whoop's defaults are placeholders:
they are population averages, not calibrated to the owner. The spec treats
them as the starting point, not the final policy. Personalization happens
via the calibration period in §7.2.

The current band is the band of the most recent biometrics row no older than
24 hours. If no fresh reading exists, default to Yellow.

### 7.1 What each band restricts

| Capability                                         | Green | Yellow | Red |
|----------------------------------------------------|-------|--------|-----|
| Auto-execute "approved by precedent" decisions     |  yes  |  no    | no  |
| Send a draft to a third party without confirmation |  yes  |  no    | no  |
| Propose decisions in any scope                     |  yes  |  yes   | yes |
| Propose decisions in `Strategic` scope             |  yes  |  yes   | no (defer) |
| Propose decisions in `Financial` over a threshold  |  yes  |  flag  | block |
| Schedule mentoring sessions                        |  yes  |  yes   | no  |
| Run sub-agent promotion                            |  yes  |  yes   | no  |
| Surface only what is urgent                        |  no   |  no    | yes |

"Approved by precedent" means a rule of thumb with `confidence >= 0.85` and
`evidence_count >= 10` exists for the exact (scope, subscope) pair.

The ceiling is enforced in the Hard Gate as a synthetic rule
`biometric_ceiling`, so it leaves an audit trail.

### 7.2 Calibration period

For the first 28 days after install, Solomon runs in calibration mode for
biometrics. During this period:

- Default Whoop bands (see the band table earlier in §7) are in effect for
  autonomy enforcement.
- Every `decisions` row carries the autonomy band in effect at decision
  time via the existing `autonomy_band` column.
- Every `owner_response` is logged as usual.
- The `biometrics` table continues to record hourly readings (`recovery_pct`,
  `band`, etc.) with their own `ts`. Calibration recovers the
  decision-time biometric snapshot by joining each decision against the
  most recent `biometrics` row at or before `decisions.ts`.

At day 28, the `solomon-calibrate-biometrics` skill runs. It joins each
decision against the nearest-prior `biometrics` reading and produces a
report covering:

- Acceptance rate (`approved` + `edited`) by recovery band.
- Acceptance rate by recovery decile (0-9, 10-19, ... 90-100).
- Inverted cases: Red-day decisions the owner approved without edits, and
  Green-day decisions the owner rejected. These are the signal that the
  default thresholds disagree with the owner's actual judgment.
- A proposed personalized threshold pair `(red_max, green_min)` chosen so
  that the boundary deciles roughly match the owner's observed acceptance
  inflection points.

The proposal is surfaced through the standard mentoring flow — owner
reviews, approves, edits, or rejects. Approved thresholds are written to
`profile/biometrics.yaml` as `red_max` and `green_min` and override the
defaults. The same skill can be re-run later (quarterly, or after a
lifestyle change) to re-calibrate.

Until a calibration result is approved, the Whoop defaults stand. The spec
does not assume calibration will always tighten thresholds — it may loosen
them, and that is a valid outcome.

---

## 8. Sub-Agent Promotion

Hermes can spawn ephemeral sub-agents for narrow tasks (e.g. "draft a polite
no to this vendor"). Solomon counts the patterns of these spawns and, when a
pattern recurs often enough, promotes it into a persistent Hermes profile —
a dedicated skill so the next instance is faster and more consistent.

### 8.1 Pattern signature

Every sub-agent spawn writes a `task_patterns` row keyed by a `signature`
string. The signature is computed by the calling skill as:

```
sha1( normalize(scope) + '|' + normalize(intent) + '|' + normalize(object_type) )
```

Where `intent` is a verb phrase (`draft_reply`, `extract_invoice`,
`schedule_followup`) and `object_type` is the noun the agent acts on
(`vendor_email`, `client_quote`, `calendar_conflict`).

If the signature already exists, increment `occurrences` and update
`last_seen`. If not, insert with `occurrences = 1`.

### 8.2 Promotion threshold

Promotion thresholds are per-scope, because what counts as "recurring" is
very different across scopes. Admin work recurs daily; Strategic work
recurs over years. A single global threshold would either spam Admin
promotions or never fire for low-volume scopes.

| Scope     | `occurrences` threshold | Notes |
|-----------|-------------------------|-------|
| Admin     | 15                      | High-volume, low-stakes patterns (scheduling, invoice extraction, vendor replies). |
| Operational | 20                      | Default. Client work, drafting, scoping. |
| Personal  | 10                      | Lower volume, lower stakes; faster promotion is fine. |
| Strategic | never (manual only)     | Volume too low for statistical promotion; mentoring proposes manually if at all. |

A pattern becomes eligible for promotion when all of the following hold:

- `occurrences >= threshold(scope)` from the table above.
- `last_seen` is within the last 60 days (still active). Applies to all
  scopes; cold patterns do not promote regardless of historical volume.
- Of the last `threshold(scope)` instances, at least 75% produced decisions
  where `owner_response IN ('approved', 'edited')`. The window scales with
  the threshold so low-volume scopes are not promoted on a thin evidence
  base — e.g. Personal needs 8 of 10 approved/edited, Admin needs 12 of 15,
  Operational needs 15 of 20.
- No rule of thumb tagged for this signature has `status = 'suspended'`.

Strategic patterns never trigger automatic eligibility. They surface as a
note in mentoring ("you've handled 6 partnership conversations this
quarter; want to draft a profile?") and the owner decides explicitly.

When eligibility is met, Solomon raises a promotion proposal during the next
mentoring session (never autonomously). Owner approval triggers:

1. Generate a new skill at `/opt/data/skills/solomon/solomon-task-<slug>/`
   containing the distilled procedure.
2. Set `task_patterns.promoted = 1`, `promoted_at = now`,
   `promoted_skill = '<skill name>'`.
3. Future spawns matching the signature load the persistent skill instead of
   creating an ephemeral agent.

### 8.3 Demotion policy

A promoted skill can fail in two distinct ways: sudden breakage (API
changed, client relationship shifted, owner's preferences moved) and slow
drift (skill was great a year ago but is now wrong 40% of the time). The
demotion policy uses two triggers, one for each failure mode.

Hard trigger — immediate suspend:

- 3 `rejected` responses within the last 5 invocations of the skill.
- The skill is moved to `status = 'suspended'` immediately and a
  notification is sent to the owner. No autonomous use until the owner
  reviews. Catches sudden breakage without requiring three rejections in a
  row (one accidental approval would otherwise reset a strict consecutive
  counter).

Drift trigger — suspend on review:

- Over the last 20 invocations, approval rate
  (`approved + edited`) drops below 60%.
- The skill is NOT suspended automatically. It is queued as a mentoring
  proposal: "this skill's approval rate has dropped from X% to Y% over the
  last 20 invocations; revise, retire, or keep?" The owner decides during
  the next session.

While a skill is `suspended`:

- Future spawns matching its signature revert to ephemeral sub-agents
  rather than loading the suspended skill. A skill that keeps loading
  would keep failing; ephemeral agents at least give the system a chance
  to behave correctly while the owner reviews.
- The original `task_patterns` row keeps `promoted = 1` so the system
  remembers this signature has a skill (suspended), preventing a duplicate
  promotion proposal.

Re-promotion / reactivation:

- During mentoring, the owner can manually move a suspended skill back to
  `active`. On reactivation, the approval-rate window is reset (next 20
  invocations are evaluated fresh against the 60% drift threshold).
- The owner can also retire a suspended skill permanently
  (`status = 'retired'`). Retired skills stay in the database for audit but
  never load and never re-promote without a fresh promotion cycle on the
  underlying pattern.

---

## 9. Rules of Thumb

Rules of thumb are the owner's heuristics — "I never quote a fixed price
without a one-hour scoping call." Solomon stores them as structured records,
not as free text in markdown, because every rule needs confidence and
evidence tracking to know when to trust it and when to revisit it.

### 9.1 Schema

See `rules_of_thumb` and `rule_evidence` in Section 3.1. Key fields:

| Field                | Purpose |
|----------------------|---------|
| `statement`          | Plain-English rule, owner-readable. |
| `condition`          | Optional JSONLogic predicate (stored as a JSON string) that lets the Hard Gate machine-check the rule. Null for rules that only the Soft Gate can apply. See §9.3 for the language and context contract. |
| `confidence`         | 0.0–1.0. Updated by `confidence = evidence_count / (evidence_count + contradiction_count + 1)`. |
| `evidence_count`     | Times the rule was applied and the owner approved the resulting decision. |
| `contradiction_count`| Times the rule was applied and the owner rejected or substantially edited. |
| `source`             | `onboarding` (declared during Sessions 0–6), `mentoring` (extracted during a session), `inferred` (LLM proposed it from the decision log). |
| `status`             | `active` — used by gates; `suspended` — under review; `retired` — kept for history. |

### 9.2 Lifecycle

1. New rule inserted with `confidence = 0.5`, `status = 'active'` if
   declared by the owner; `status = 'suspended'` if `inferred` and pending
   confirmation at the next mentoring session.
2. Each decision evaluated under a rule writes a `rule_evidence` row.
   Confidence is recomputed on write.
3. If `confidence < 0.3` and `evidence_count + contradiction_count >= 5`,
   automatically move to `status = 'suspended'` and queue for mentoring
   review.
4. Owner can manually retire any rule from a mentoring session.

Inferred rules are never enforced by the Hard Gate. They live in the Soft
Gate's context and in mentoring proposals only.

### 9.3 The `condition` language: JSONLogic with a context whitelist

Rule conditions are written in JSONLogic (https://jsonlogic.com), stored in
the `condition` column as a JSON string. JSONLogic was chosen because it is
safe by construction (no code eval, no string parsing, just a JSON tree of
named operators), small enough that an LLM can author and edit rules
reliably from a system prompt, and mature with reference implementations in
many languages.

The Hard Gate evaluates conditions against a fixed context object it
builds from the proposed decision. The context schema is the contract: any
field not listed below is unavailable to JSONLogic, and the LLM authoring
rules must be told the schema explicitly. There is no filesystem, network,
or database cursor exposed.

Context fields available via `var`:

| Path                        | Type    | Meaning |
|-----------------------------|---------|---------|
| `decision.scope`            | string  | `Personal`, `Operational`, `Strategic`, ... |
| `decision.subscope`         | string  | scope-specific subkey, e.g. `client_email` |
| `decision.intent`           | string  | verb phrase from the listening agent |
| `decision.amount`           | number  | monetary amount if applicable, else null |
| `decision.counterparty`     | string  | name of the third party if any |
| `decision.urgency`          | string  | `low`, `normal`, `high`, `urgent` |
| `decision.tags`             | array   | free-form tags from the listening agent |
| `biometric.band`            | string  | `green`, `yellow`, `red` |
| `biometric.recovery_pct`    | number  | 0-100 |
| `recent.approval_rate_30d`  | number  | 0.0-1.0 over last 30 days, this scope |
| `recent.contradictions_30d` | number  | count of rejections this scope, last 30 days |
| `time.hour_local`           | number  | 0-23, owner's timezone |
| `time.is_weekend`           | boolean | |

Operators allowed: the JSONLogic standard set — comparisons (`==`, `!=`,
`<`, `<=`, `>`, `>=`), logical (`and`, `or`, `!`, `if`), arithmetic (`+`,
`-`, `*`, `/`, `%`), `in`, `var`, `missing`, string `cat`, and `log`. No
custom operators in v0.1; if a real rule needs one, that is a signal to
add it to the whitelist deliberately rather than to extend the language.

Example — "block any Operational-scope decision over $5,000 on a Red day":

```
{ "and": [
    { "==": [ { "var": "decision.scope" }, "Operational" ] },
    { ">":  [ { "var": "decision.amount" }, 5000 ] },
    { "==": [ { "var": "biometric.band" }, "red" ] }
] }
```

Hard Gate evaluation: a `true` result means the rule fires. The rule's
`statement` field carries the human-readable explanation written into the
audit trail. A `false` result means the rule does not apply to this
decision and the Hard Gate moves on. Rules with `condition = null` are
never evaluated by the Hard Gate; they exist solely as Soft Gate context.

When the LLM proposes a new rule during mentoring, it is asked to produce
both `statement` (English) and `condition` (JSONLogic, optional). The
mentoring skill validates the JSONLogic against the context schema before
accepting it; an invalid condition is offered to the owner as
"statement-only, no machine check."

### 9.4 Profile-vs-inferred conflict resolution

The profile YAML (declared during onboarding, source = `onboarding`) and
inferred rules (proposed by the `inferred` source from the decision log)
can drift apart. The owner might have declared "I always quote fixed price
up front" in onboarding but then declined fixed-price quotes seven times
in a row. Both signals are real; the spec defines how they are reconciled.

Rule: profile wins for enforcement, conflicts surface in mentoring.

Two mechanisms together:

1. **Enforcement is profile-first.** When an `inferred` rule contradicts
   an `onboarding`- or `mentoring`-source rule on the same `scope` and
   `subscope`, the inferred rule is automatically set to
   `status = 'suspended'` regardless of its `evidence_count` or
   `confidence`. It does not influence the Hard Gate (inferred rules
   never do, per §9.2) and it does not enter the Soft Gate's context
   while suspended. The declared rule continues to fire as written.

2. **Contradiction is logged, not silenced.** A `rule_conflicts` row is
   written the moment the suspension happens (table DDL in §3.1). Each
   row captures both rules, the inferred rule's evidence count at conflict
   time, the affected scope/subscope, and a status that starts as `open`.

   Open `rule_conflicts` rows are surfaced in the next mentoring session.
   The owner sees: "Your declared rule says X. The system has observed Y
   in the last N decisions. Want to (a) keep the declaration as-is and
   retire the inferred rule, (b) update the declaration to match
   behavior, (c) keep both — the declaration enforces, the inference
   stays as Soft Gate context only, or (d) defer." The chosen option is
   written to `resolution` and `status` becomes `resolved`.

Detection mechanics: contradiction is detected at inferred-rule-insert
time by the same `solomon-mentoring-session` skill that proposes the
rule. The check is structural — same scope, same subscope, opposing
condition (negation of the JSONLogic predicate, or contradictory
statement detected by the LLM at proposal time and flagged in the
proposal). Cross-scope conflicts are not auto-detected in v0.1; if they
matter, they show up as low-confidence rules and get caught by the
existing §9.2 lifecycle.

Why this design: profile-always-wins (silent) ignores a real signal that
the owner's stated principles may be stale. Inference-always-wins
overwrites the deliberate layer with short-term behavior drift, which is
exactly what profile YAML exists to resist. Confidence-weighted blending
treats declared rules as statistical artifacts they are not. Surfacing
the conflict for owner judgment preserves declared-rule authority while
keeping the disagreement visible — which is the whole point of the
mentoring loop.

---

## 10. Mentoring Loop

A mentoring session is a structured conversation between Solomon and the
owner. The skill `solomon-mentoring-session` already defines the format
(decision review → pattern summary → profile update → calibration score).
This section specifies when sessions are triggered.

### 10.1 Trigger conditions

A session is offered to the owner when any of the following becomes true:

| Trigger              | Condition | First active in |
|----------------------|-----------|-----------------|
| Scheduled            | 7 days have passed since the last session of any kind. | v0.1 |
| Owner request        | Owner says "mentor me" or equivalent. | v0.1 |
| Edit rate            | In the last 20 decisions, `edited + rejected >= 8`. | v0.2 |
| Soft-gate divergence | In the last 20 decisions, the soft gate flagged or blocked something the owner then approved (or vice versa) ≥ 4 times. | v0.2 |
| Inferred-rule queue  | ≥ 3 inferred rules are sitting in `status = 'suspended'` awaiting review. | v0.2 (depends on inference, §13.1) |
| Rule conflict        | ≥ 1 `rule_conflicts` row has `status = 'open'`. See §9.4. | v0.2 (depends on inference) |
| Promotion ready      | ≥ 1 task pattern has crossed the promotion threshold (Section 8). | v0.2 (promotion proposals are v0.2 per §13.1) |

In v0.1 only the Scheduled and Owner-request triggers fire. The remaining
rows are present in the schema and the trigger evaluation code from day
one so v0.2 turns them on by configuration rather than by patch.

### 10.2 Cap

At most one mentoring session per 7-day rolling window, regardless of how
many triggers fire. If multiple triggers accumulate, they are bundled into
the next session's agenda.

Exception: an explicit owner request is never blocked by the cap.

The `mentoring_sessions.triggered_by` column records which trigger fired (or
`bundled` if more than one).

### 10.3 Outputs

A mentoring session produces:
- A YAML file under `/opt/data/solomon/mentoring/YYYY-MM-DD-mentoring.yaml`
  (canonical record, human-editable).
- A `mentoring_sessions` row in solomon.db (index/lookup only).
- Zero or more updates to `rules_of_thumb` and to profile YAML files.
- Optional sub-agent promotions (Section 8).

---

## 11. Installation

Solomon is installed by cloning the skill pack repo and running a setup
skill inside Hermes. There is no PyPI package, no Docker image, no installer
script beyond what the setup skill does.

### 11.1 Steps

```
# 1. Prerequisites: Hermes is installed and runnable on the target machine.
#    /opt/data/skills/ exists and is on the Hermes skill search path.

# 2. Clone the skill pack into the skills directory.
cd /opt/data/skills
git clone https://github.com/<owner>/solomon.git

# 3. Start Hermes and run the setup skill in a chat.
hermes
> run solomon-setup
```

### 11.2 What `solomon-setup` does

1. Creates `/opt/data/solomon/` and subdirectories: `profile/`,
   `decisions/`, `mentoring/`, `ingestion/plaud/`.
2. Creates `/opt/data/solomon/solomon.db` and applies the full schema in
   §3.1 (all tables including `meta`, `rule_conflicts`, `rules_of_thumb`,
   etc. are created at install time even when the v0.1 in-scope feature
   set does not yet write to all of them — §13.1).
3. Seeds `meta` with `('schema_version', '<current code version>')` so
   `solomon-migrate` (§12.6) has a starting point on the very first cron
   run. No `solomon-migrate` invocation is needed at fresh install.
4. Writes a starter `config.yaml` at `/opt/data/solomon/config.yaml` with
   placeholders for: IMAP credentials (Plaud), Telegram bot token and owner
   chat ID, and (optional) Whoop API token.
5. Walks the owner through the explanation in plain language and points
   them at the seven onboarding sessions in order.
6. Schedules the Plaud poll job (every 5 minutes) via Hermes' scheduler.

### 11.3 Updates

`git pull` inside `/opt/data/skills/solomon` is the upgrade path for code.
Schema changes are NOT applied by `solomon-setup`; they ship as numbered
migration files under `migrations/` and are applied by the dedicated
`solomon-migrate` skill, which the owner explicitly invokes after Solomon
detects a version mismatch on the next cron run. See §12.6 for the full
migration flow, the `meta.schema_version` contract, and the
auto-export-before-migrate safety step.

---

## 12. Backup and Portability

Solomon stores three things that, taken together, ARE the system: structured
data in `solomon.db`, profile YAML in `profile/`, and identity facts in
Hermes Memory. A backup that captures only one or two of these is not a
backup — it's a partial snapshot that will silently lose state on restore.
This section specifies the export bundle so that machine moves, debugging,
and schema migrations are all routine operations rather than recovery
projects.

### 12.1 The export bundle

The `solomon-export` skill produces a single timestamped directory (or zip)
with the following structure:

```
solomon-export-<YYYYMMDD-HHMMSS>/
  manifest.json
  db/
    decisions.jsonl
    audits.jsonl
    rules_of_thumb.jsonl
    rule_evidence.jsonl
    task_patterns.jsonl
    biometrics.jsonl
    rule_conflicts.jsonl
    mentoring_sessions.jsonl
  profile/
    <all YAML files copied as-is>
  memory.json
  skills/
    <all promoted skill directories copied as-is>
```

`manifest.json` is the export's contract:

```
{
  "solomon_version": "0.1.3",
  "schema_version": 4,
  "exported_at": "2026-05-06T15:42:00-05:00",
  "owner_id": "<from profile>",
  "row_counts": { "decisions": 1247, "audits": 2389, ... },
  "memory_entries": 18,
  "promoted_skills": 6
}
```

JSONL is used for database tables (one JSON object per line) so the bundle
is human-readable, diffable, and partially recoverable if a single line is
corrupted. YAML profile files are copied byte-for-byte. Memory is dumped
to `memory.json` via the Hermes Memory API rather than read from Hermes'
internal storage directly, so the bundle survives Hermes-side storage
changes.

### 12.2 The import skill

The `solomon-import` skill reads `manifest.json` first, validates
`schema_version` against the current code, and either:

- imports directly if versions match;
- runs the version-N-to-current migration chain if the bundle is older;
- refuses with a clear error if the bundle is newer than the running code.

Import is transactional per table: a failure mid-import rolls back to the
state before the import began. Memory entries are upserted by content hash
so re-importing the same bundle does not duplicate identity facts.

### 12.3 What is NOT in the bundle

- The `events` and `transcripts` tables. These are upstream ingestion
  lineage, not identity data — every row points at a payload file under
  `/opt/data/solomon/ingestion/` (Plaud emails, Twilio webhook payloads,
  etc.) and the three-pass listening agent output is regenerable from
  those payloads. Including them would roughly double bundle size for
  data that the owner can either re-ingest from the source or forfeit
  with no impact on Solomon's behavior. Owners who want full lineage
  should back up `/opt/data/solomon/ingestion/` separately.
- SQLite WAL/journal files (the export reads from a clean `.dump`).
- Hermes runtime state outside of Memory (skills the owner authored
  manually live in Hermes' skills directory and are the owner's
  responsibility to back up separately).
- Cached transcripts and intermediate listening-agent artifacts in
  `/opt/data/solomon/cache/` — these are derivable and not worth the
  bundle size.

### 12.4 Encryption

The bundle is plaintext by default. The owner is responsible for encrypting
at rest if storing offsite (S3, Dropbox, etc.). Forced encryption was
considered and rejected: most backups happen on the owner's own machine,
and forced encryption adds a key-management workflow that the average
backup routine will skip, defeating itself. Owners who need encrypted
offsite backups can pipe the bundle through `age` or `gpg`; the export
format does not change.

### 12.5 Recommended cadence

- Automatic: `solomon-export` runs weekly via cron, writing to
  `/opt/data/solomon/backups/`. Last 8 bundles retained.
- Manual: before any schema migration, before any machine move, and on
  request.

### 12.6 Schema migrations

Schema changes are managed by a dedicated `solomon-migrate` skill, not by
re-running `solomon-setup`. Conflating first-install with upgrade is a
known failure mode for one-of-a-kind data; the two operations stay
separate.

The current schema version lives in the `meta` table (DDL in §3.1):

```
SELECT value FROM meta WHERE key = 'schema_version';
```

`solomon-setup` seeds this row with the version embedded in the running
code at install time. `solomon-migrate` updates it after each successful
migration step.

Migration files live in the Solomon repo under `migrations/`, named by the
version transition they perform:

- `001_to_002.sql` — pure SQL DDL/DML. Owner-readable.
- `003_to_004.py` — used when a migration needs logic (data backfill,
  conditional changes, foreign-key reshuffles). Same numbering scheme.

`solomon-migrate` reads `meta.schema_version`, finds all migration files
whose start version is ≥ the current value, applies them in order, and
updates `meta.schema_version` after each successful step. Each migration
runs inside a SQLite transaction (or a Python try/rollback block) so a
mid-migration failure leaves the DB at the previous version, not in a
half-migrated state.

Discovery and prompting:

- On every cron run, Solomon compares `meta.schema_version` against the
  version baked into the running code.
- If they match: continue normally.
- If the DB is behind the code: send a Telegram message — "Schema is at
  vN, code expects vM. Run `solomon-migrate` to update. An export bundle
  has been auto-written to /opt/data/solomon/backups/<timestamp>/." Then
  pause normal processing (no listening agent runs, no decisions ship)
  until the migration completes. The owner explicitly invokes the
  migration; Solomon never auto-migrates silently.
- If the DB is ahead of the code (e.g. owner downgraded): refuse to start
  with a clear error pointing at the bundle for restore.

The auto-export-before-migrate step is the safety net. If a migration
produces wrong results — wrong column types, lost data, broken foreign
keys — the bundle written seconds earlier is the rollback path. This ties
directly to §12.1 (export bundle format) and §12.2 (import skill).

Why explicit-with-prompting beats silent auto-migrate: this is a
single-owner system holding identity data. A bad migration that runs
silently is discovered days later when a decision references a missing
field. A bad migration the owner explicitly ran is discovered immediately.
Loud is correct.

---

## 13. MVP Scope (v0.1)

Ship the smallest end-to-end loop that proves the model. Everything else is
deferred.

### 13.1 In scope for v0.1

| Area                  | v0.1 |
|-----------------------|------|
| Input adapters        | `plaud_email` only |
| Owner interface       | Telegram only (1/2/3 reply pattern for Approve / Edit / Discuss) |
| Processing            | Three-pass per transcript: summarize, extract learnings, propose actions |
| Storage triad         | Memory + skill files + solomon.db (all tables created, only the relevant ones populated) |
| Onboarding            | All 7 sessions (already implemented) |
| Decision log          | Append-only YAML plus `decisions` table mirror |
| Mentoring             | Manual trigger ("mentor me") and the 7-day scheduled trigger only. Edit-rate, divergence, inferred-queue, rule-conflict, and promotion-ready triggers are wired in code but inactive — see §10.1 for the v0.1/v0.2 split. |
| Audit                 | Hard Gate active (non-negotiables only); Soft Gate active for all proposals |
| Biometric ceilings    | Off in v0.1; band defaults to Green; Whoop adapter not shipped. `solomon-calibrate-biometrics` ships in v0.2 alongside Whoop. |
| Sub-agent promotion   | Pattern counting active; promotion proposals deferred to v0.2 |
| Rules of thumb        | Onboarding-sourced rules only; inference (and the §9.4 conflict-resolution machinery + the §10.1 inferred-queue and rule-conflict triggers it powers) deferred to v0.2 |
| Installation          | git clone + `solomon-setup` |

### 13.2 Explicitly out for v0.1

- Twilio, Gmail, Calendar, Plaid, Whoop adapters
- Auto-execution of any decision (every action requires owner approval)
- Sub-agent promotion (counting only)
- Inferred rules of thumb
- Edit-rate and divergence mentoring triggers
- Multi-owner support
- Any UI other than Telegram

### 13.3 Definition of done for v0.1

- Owner can record on Plaud, get an email, and within 5 minutes receive a
  Telegram message with summary + proposed action(s) numbered 1/2/3.
- Owner reply is logged as a decision row plus a YAML decision-log entry.
- Both gate outcomes are recorded in `audits` for every proposal.
- "mentor me" produces a complete mentoring YAML and updates profile files.

---

## 14. Resolved Questions and Deferred Items

The following were the deliberately-undecided design questions during spec
authoring. All twelve are now resolved; one carries a sub-item (#2a) that
is a deliberate scope deferral rather than an open design question — the
spec specifies the constraint, the owner picks the implementation at
install time.

1. RESOLVED — Owner interface stays Telegram-first, augmented by a
   read-mostly local web view (PWA or static HTML) starting around v0.3.
   Telegram handles capture, notify, and quick approve/reject. Web view
   handles browsable surfaces: pending-decision queue, decision log
   timeline, rules of thumb with confidence/evidence, biometric trends vs.
   ceilings, and sub-agent profiles. Solomon writes; web view renders.
   No move to Signal/Matrix.
2. RESOLVED — Soft Gate LLM is configurable per scope. Personal scope uses
   a local model (mandatory, no fallback); Operational and Strategic use a
   hosted model with Anthropic Claude as the pluggable default. On model
   unavailability, the affected scope degrades to suggest-only rather than
   falling back across the privacy boundary. See §6.2.1.
2a. Specific local model for Personal-scope Soft Gate. Deferred — the spec
    requires a local-capable runtime; the owner picks the actual model
    (Llama 3.1 8B, Qwen 2.5 14B, a quantized 30B+, etc.) at install time
    based on available hardware.
3. RESOLVED — Default biometric bands match Whoop's own bands (0-33 Red,
   34-66 Yellow, 67-100 Green) for v0.1, on the basis that they are at
   least the numbers the owner already sees in their Whoop app rather than
   freshly invented placeholders. A 28-day calibration period (§7.2) logs
   recovery score against owner responses and proposes personalized
   thresholds via the `solomon-calibrate-biometrics` skill. Until the owner
   approves a personalized pair, Whoop defaults stand. Re-calibration can
   be run on demand.
4. RESOLVED — The `condition` field on `rules_of_thumb` is JSONLogic
   (https://jsonlogic.com), stored as a JSON string. Chosen over Python
   expressions (unsafe to eval LLM-authored code in the Hard Gate, which is
   the trust layer) and over a custom mini-DSL (maintenance burden not
   justified). JSONLogic is safe by construction, LLM-friendly, and mature.
   Cases JSONLogic cannot express (cross-table joins, fuzzy matching,
   time-window aggregates) leave `condition` null and route through the
   Soft Gate. See §9.3 for the language contract and `var` whitelist.
5. RESOLVED — Promotion thresholds are per-scope, not global. Admin: 15,
   Operational: 20 (kept as default), Personal: 10, Strategic: never auto
   (mentoring-only). The usefulness check (≥75% approved/edited) scales
   with the threshold rather than using a fixed window of 20. The 60-day
   `last_seen` recency check applies to all scopes. See §8.2.
6. RESOLVED — Demotion uses two triggers, not just consecutive rejections.
   Hard trigger: 3 rejections within the last 5 invocations → immediate
   suspend (catches sudden breakage). Drift trigger: approval rate over
   the last 20 invocations falls below 60% → mentoring proposal, not auto
   suspend (catches slow rot). Suspended skills revert their signature to
   ephemeral sub-agents until reactivated. Owner can reactivate (resets
   window) or retire (permanent) during mentoring. See §8.3.
7. RESOLVED — The Soft Gate sees a hybrid retrieval over the decision log,
   not a flat "last 20" window. Three SQL streams, ~18 rows total: 10 most
   recent in the same scope, 5 most recent matching the same subscope or
   counterparty, and 3 most recent scope-matched cases in the last 90 days
   where the owner overrode the Soft Gate. Deduped with priority
   correction > relevant > recent. Rows are grouped under labelled headers
   in the prompt so the LLM weights correction signals correctly. SQL only,
   no embeddings dependency. See §6.2.2.
8. RESOLVED — Backup is a documented JSON export bundle produced by the
   `solomon-export` skill (DB tables as JSONL, profile YAML copied as-is,
   Hermes Memory dumped via the Memory API, promoted skills copied).
   `manifest.json` carries schema version for migration-aware import via
   `solomon-import`. Plaintext by default; owner encrypts offsite backups
   themselves. Weekly cron + on-demand. See §12.
9. RESOLVED — v0.1 is single-source (Plaud) with no dedup logic. v0.2 adds
   multi-device dedup via 10-minute time window + normalized hash of the
   first 200 chars; source priority configurable (default plaud > phone >
   manual_upload). Paraphrase-heavy overlaps will not dedup by design — a
   duplicate is preferable to a silent merge. See §4.3.
10. RESOLVED — Schema migrations use a dedicated `solomon-migrate` skill,
    not `solomon-setup` re-run. Versioned migration files (`NNN_to_MMM.sql`
    or `.py`) in the repo. Solomon detects version mismatch on every cron
    run, auto-writes an export bundle, and prompts the owner via Telegram
    to invoke the migration. No silent auto-migrate. DB-ahead-of-code is
    refused at startup. See §12.6.
11. RESOLVED — Profile YAML wins for enforcement: when an `inferred` rule
    contradicts an `onboarding`/`mentoring` rule on the same scope/subscope,
    the inferred rule is auto-suspended. A `rule_conflicts` row is logged
    and surfaced at the next mentoring session, where the owner picks
    keep-declared / update-declared / keep-both / defer. Profile-wins is
    preserved; the disagreement is never silenced. See §9.4.
12. RESOLVED — Personal scope never leaves the owner's machine. The Soft
    Gate for Personal-scope decisions runs on a locally-hosted model, with
    no hosted-LLM fallback. See §6.2.1.

---

End of specification.
