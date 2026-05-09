# Four Cs Framework

Adapted from Nate Herkai's AIS-OS one-pager. Solomon uses this as a dependency-ordered architecture lens.

| C | Solomon primitive | Folder |
|---|---|---|
| **Context** | Foundation YAMLs + captured_items + context/ + MEMORY.md + USER.md | `foundation/`, `db/schemas/captured_items.sql`, `context/`, root MEMORY/USER |
| **Connections** | Integrations registry + Hermes plugins + workers | `connections.md`, `hermes-plugins/`, `workers/`, `references/api-*.md` |
| **Capabilities** | Skills + orchestrator pipeline | `skills/`, `orchestrator/pipeline/` |
| **Cadence** | Sleep cycle + mentoring + audit | `orchestrator/sleep-cycle/`, `skills/learning/{solomon-mentoring-session,solomon-audit}/` |

Dependency order: Context first (you can't connect to nothing). Connections second. Capabilities third. Cadence last (only meaningful when the other three are real).

`solomon-audit` scores each C from 0–25; total target 100. See `skills/learning/solomon-audit/SKILL.md`.
