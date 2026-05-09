---
name: solomon-vocabulary-capture
category: interview
phase: interview
version: 0.1.0
agent: hermes
trigger: [post-owner-turn-hook]
inputs: [owner_answer_text, captured_items.id (for first_seen linkage)]
outputs: [db.vocabulary rows (SQL-only, not embedded)]
reads_only: false
autonomy_level: L1
depends_on: [solomon-redact]
portable: true
---

# solomon-vocabulary-capture

Owner's voice as data. Called after every owner turn, in parallel with `solomon-extraction`. Always preceded by `solomon-redact` to avoid capturing entity names as vocabulary.

## Two-pass extractor

1. **Pass 1 — local NLP**: spaCy `en_core_web_sm` POS tagging. Pulls noun phrases (NP chunks) and verb phrases (VP chunks). Fast, deterministic, free.
2. **Pass 2 — LLM extraction**: Sonnet, ~200 tokens out. Prompt: "Extract any idioms, metaphors, or stock expressions from this text. Return JSON: `[{phrase, type}]`." Catches what spaCy misses.

Both passes write to `db.vocabulary`. `type` field marks which extractor produced the row (`np` / `vp` / `idiom` / `metaphor` / `stock_expression`).

## Normalization

Per §2.11 / `db/schemas/vocabulary.sql`: lowercase, strip surrounding punctuation, collapse internal whitespace, strip leading/trailing articles (the/a/an). NO stemming. Hyphens preserved. `aliases` JSON column handles equivalences across spellings.

## Frequency increment

If the normalized phrase already exists, increment `frequency` and update `last_seen`. Otherwise INSERT.

## Vocabulary is NOT embedded

There is no semantic-search use case for individual phrases. The vocabulary table is queried via SQL frequency / recency lookups. This is intentional — see §1 of SOLOMON-PLAN.md.
