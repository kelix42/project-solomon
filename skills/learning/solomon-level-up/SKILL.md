---
name: solomon-level-up
category: learning
phase: interview
version: 0.1.0
agent: hermes
trigger: ["/solomon-level-up", "find me leverage", "what should I automate next"]
inputs: [decisions/log.md, db.scope_autonomy, db.events trailing 30d]
outputs: [one shipped artifact (e.g., a new captured_item, a new tool the owner approves to automate, or a sleep-cycle adjustment), decisions/log.md entry]
reads_only: false
autonomy_level: L1
depends_on: [solomon-profile-loader]
portable: true
---

# solomon-level-up

Weekly 3Ms ritual adapted from AIS-OS `/level-up`. ONE run = ONE shipped artifact.

## Phase 1 — Mindset (find the candidate)

Walk the owner through the trailing 30 days. What manual work felt repetitive? Where did Solomon defer to one-tap when it could have shipped? Default Shift question: "to what extent could AI be leveraged here?"

## Phase 2 — Method (scope one)

Pick ONE candidate. Walk the 5-step process map: find constraint → entry/action/decision → map process → autonomy level (L0–L4) → KPI. Document in `decisions/log.md` per §2.11 canonical format.

## Phase 3 — Machine (build it)

Route to the right scaffold:
- Prompt-only refinement → update SOUL.md or a SKILL.md.
- Deterministic skill → author or update a skill body.
- AI-assisted skill → tool registration in a Hermes plugin.
- Worker → new worker scaffold under `workers/`.
- Sleep-cycle job adjustment.

Promote scope autonomy if appropriate (L2 → L3 etc.). Confirm with owner.

## Phase enforcement

This is `phase: interview` because Phase 1 asks the owner reflective questions. Phase 3 may invoke decision-phase tools (e.g., editing a SKILL.md) — that's via `dispatch_tool`, allowed across phase boundaries when the agent acts on owner approval.
