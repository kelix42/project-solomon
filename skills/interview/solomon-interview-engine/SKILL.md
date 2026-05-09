---
name: solomon-interview-engine
category: interview
phase: interview
version: 0.1.0
agent: hermes
trigger: ["/solomon-interview", "begin interview"]
inputs: [active_domain, last_answer, probe_library/<domain>.yaml, db.coverage, db.vocabulary, db.clarification_queue]
outputs: [next_question, db.coverage (probe_count++), db.coverage.last_probed, db.coverage.last_probed_version]
reads_only: false
autonomy_level: L1
depends_on: []
portable: true
---

# solomon-interview-engine

Orchestrator during training. The interview-phase entry point used by every onboarding session wrapper (`solomon-onboarding-00-industry` … `06-taxonomy`) and by `solomon-mentoring-session`.

## Process per turn

1. Read `db.clarification_queue WHERE session_id = ? AND status = 'queued'`. **Pending clarifications jump the queue** — ask the suggested probe verbatim, do not skip.
2. Otherwise, detect keywords in the owner's last answer.
3. Read the active domain's probe library YAML (`skills/interview/solomon-interview-engine/probe_library/<domain>.yaml`).
4. Pick the highest-priority unused probe (lowest priority number wins) for a matched keyword that hasn't yet hit `coverage.probe_count` saturation.
5. Render the template with verbatim phrase substitution: replace `{phrase}` with the owner's exact phrase from the last answer.
6. Ask one question. Never stack.
7. On dry keyword, fall back to a related keyword in the same domain, then to a generic forward prompt from `_generic.yaml`.
8. After asking, increment `coverage.probe_count`, set `coverage.last_probed = NOW()`, set `coverage.last_probed_version = <library_version>`.

## ELIZA discipline

Reuse the owner's verbatim phrases. Never paraphrase. One question at a time. Wait for silence.

## Probe-library version migration

On launch, check if `coverage.library_version_seen < probe_library/<domain>.yaml::version` for any domain. If so, write a `mentoring_queue` row (`source = probe_library_update`, priority 7). Do not auto-mass-re-probe.

## Phase enforcement

This skill carries `phase: interview`. The orchestrator pipeline (decision-phase) cannot load it. CI test asserts.
