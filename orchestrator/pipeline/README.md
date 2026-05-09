# Decision-phase Orchestrator Pipeline

10 stages, deterministic order, per §2.2.5 of SOLOMON-PLAN.md.

```
Capture → Salience → Classification → Hard-rule check → Working memory + 5-lane retrieval
       → System 1 (Sonnet) → System 2 (Opus) → Audit gate (Opus) → Owner-state gate → Action
```

## How an event flows

1. The `pipeline-tick` worker (or a manual `hermes` invocation) fetches a `db.events` row with `status = pending`.
2. `runner.py` is invoked with the event_id.
3. Stages execute in order. Each stage updates `db.events.<stage_field>` and records timing in `stage_timings_ms`.
4. Failure of any stage stops the pipeline; row records `status = failed`.
5. On `status = complete`, an entry is appended to `decisions/log.md` (canonical four-field format) and a row inserted into `db.decisions`.

## Files

- `runner.py` — entry point that walks the 10 stages.
- `stage_capture.py` … `stage_action.py` — one file per stage.
- `_helpers.py` — shared helpers (db connection with WAL pragmas, LLM dispatch).

## Stages 7b — divergence check

Implemented in `stage_system2.py` after the System 2 LLM call. Token-Jaccard, NOT embeddings (§2.2.5 Stage 7b).
