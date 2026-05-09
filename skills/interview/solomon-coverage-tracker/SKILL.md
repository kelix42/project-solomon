---
name: solomon-coverage-tracker
category: interview
phase: interview
version: 0.1.0
agent: hermes
trigger: [pre-probe-selection]
inputs: [active_domain, db.coverage]
outputs: [target_sub_topic, gap_score, suggested_keyword, session_complete_flag]
reads_only: true
autonomy_level: L1
depends_on: []
portable: true
---

# solomon-coverage-tracker

Reads `db.coverage` for the active domain. Returns the lowest-coverage sub-topic with `gap_score > 0.4` for `solomon-interview-engine` to target.

## Session-complete rule

A session is **complete** when EITHER condition holds:

- **Saturation**: every sub-topic for the active domain has `gap_score < 0.4` AND `probe_count >= 5`.
- **Diminishing returns**: total session `probe_count >= 8` AND `turns_since_last_capture >= 4`.

The wrapper `solomon-onboarding-NN-*` checks this after every owner turn. On positive: print "Session N complete — moving on" and advance to the next session. Owner overrides: `/solomon-onboarding-end` (force complete) or `/solomon-onboarding-keep-going` (extend).

## Probe-library version migration check

On launch (called once per session start), compare `coverage.library_version_seen` against each domain's `probe_library/<domain>.yaml::version`. If a domain's library has bumped, write a `mentoring_queue` row (source = `probe_library_update`, priority 7).
