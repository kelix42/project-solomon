# System 1 / System 2

Two parallel reasoners on every decision event.

## System 1 — Sonnet, rules only, no reasoning

Loaded with hot identity (`SOUL.md` + `MEMORY.md` + `USER.md`), active-scope rules from captured_items, retrieved context, owner-state row.

Prompt: "Apply the owner's stated rules. Return the rule-based answer in 1–2 sentences. **No reasoning. No exploration.**"

Fast first take. Pattern-match against the owner's rules.

## System 2 — Opus, chain-of-thought allowed

Same context as System 1, but the model is allowed to reason. Returns full reasoning + answer.

## Divergence check (Stage 7b)

Token-set Jaccard similarity (lowercased, punctuation-stripped, stopwords removed) plus length-ratio. Combined score `0.6 × jaccard + 0.4 × length_ratio`. Below 0.7 → priority-4 `mentoring_queue` row (source = `surprise`).

**No embedding call** on the hot path. Rationale: per-event embedding cost is real on busy timelines (e.g., Telegram chatter), and Jaccard is local + microseconds + deterministic. Embedding-based comparison is deferred to v2.1 if Jaccard proves too coarse — `db.events.divergence_score` collects v1 data to evaluate calibration.

## Audit gate (Stage 8)

Separate Opus call with both System 1 and System 2 outputs in context. Returns APPROVE / DOWNGRADE / REJECT / REQUEST_RETHINK. Independent verdict — not a System 2 self-check.
