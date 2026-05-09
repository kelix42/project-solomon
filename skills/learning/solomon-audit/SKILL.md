---
name: solomon-audit
category: learning
phase: decision
version: 0.1.0
agent: hermes
trigger: ["/solomon-audit", "score my AIOS", "Four Cs check"]
inputs: [foundation/, connections.md, decisions/log.md, db, skills/, plugins/, workers/]
outputs: [scoreboard report, decisions/log.md append entry, optional Telegram digest]
reads_only: true
autonomy_level: L1
depends_on: [solomon-profile-loader]
portable: true
---

# solomon-audit

Four-Cs scoreboard adapted from AIS-OS `/audit`. Read-only. Run weekly (or on demand).

## What it scores (target 100/100)

- **Context** (0–25): foundation YAMLs filled? db.captured_items count? `context/` populated?
- **Connections** (0–25): connections.md rows live? plugin loads succeed? worker processes running (launchd/systemd `list-units`)?
- **Capabilities** (0–25): all 27 skills present with valid front-matter? phase rule passes for each?
- **Cadence** (0–25): all 12 sleep-cycle jobs registered? last run within 26h? last mentoring within 7d?

Plus the §11 audit-test sweep — runs each verification question and times the answer. The pass threshold is the count of audit rows in `references/orchestrator-pipeline.md` (currently 45/45).

## Corpus health section

- Wiki pages count by type.
- Raw files count by category, total size.
- Pinecone vectors per namespace (no dollar estimate; see §2.11).
- captured_items count by domain, breakdown by confidence tier.
- Vocabulary count, top 20 phrases by frequency.
- Last ingest, lint, mentoring, backup timestamps.

Owner can ask `/solomon-audit corpus` for just that section.

## Output

Markdown scoreboard. Append to `decisions/log.md`. Optionally send to Telegram (weekly digest at 8am owner-local time).

## Weekly Telegram digest

Includes: "X files awaiting attention in inbox/_unsupported/, Y in inbox/_oversized/." (Default ON.)
