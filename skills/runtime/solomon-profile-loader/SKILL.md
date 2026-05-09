---
name: solomon-profile-loader
category: runtime
phase: decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-profile-loader", "/solomon-profile", "load profile"]
inputs: [db.captured_items, db.vocabulary, foundation/*.yaml, current scope]
outputs: [structured profile + voice register loaded into hot memory]
reads_only: true
autonomy_level: L1
depends_on: []
portable: true
---

# solomon-profile-loader

Decision-phase entry. Loaded at the start of any decision session — Plaud transcript processing, real-time orchestrator runs, daily reports.

## Replaces solomon-profile (v1)

The v1 `solomon-profile` skill is replaced. Trigger compatibility: this skill responds to both `/solomon-profile-loader` and `/solomon-profile`.

## Process

1. Read all 7 `foundation/NN-*.yaml` files.
2. Read `db.captured_items` filtered by the current scope (or all if no scope).
3. Read top 30 `db.vocabulary` rows by frequency for voice register.
4. Compose a structured profile + voice register and inject into the agent's working context.
5. Apply the owner's verbatim phrasing when generating outputs (per `SOUL.md` Voice register section).

## Does NOT

- Probe.
- Reflect.
- Ask follow-up questions about owner's stated rules.

That's interview phase. This skill is decision phase.
