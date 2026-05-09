# Decision Log

Append-only. Canonical format per §2.11 of SOLOMON-PLAN.md:

```markdown
## YYYY-MM-DD — Title (max 60 chars)

**Decision**: one sentence.
**Why**: 1–3 sentences (the reasoning that survives even when the context fades).
**Alternatives considered**: bullets (2–4 lines).
**Owner**: name or initials.
```

Each entry is mirrored to `db.decisions` and embedded by Sleep-Cycle Job 11. Vector ID: `decision:<sha256-of-entry-body>:0`.

The 12 v1 resolved decisions (ported from `archives/12-DECISIONS-RESOLVED.md` via LLM rewrite) are appended below. Original prose preserved under `<details>` blocks; embedding uses the canonical body only.

---

<!-- v1 ported decisions land below this line at first install via `solomon-setup` -->
