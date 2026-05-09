# pipeline-tick

Long-lived Python worker. Every 60 seconds, scans `db.events WHERE status='pending'` and dispatches each event to the §2.2.5 orchestrator pipeline.

Concurrency capped at 5 in-flight (configurable in `corpus/schema.md` as `pipeline_max_in_flight`). Atomic claim via `UPDATE … WHERE status='pending'` prevents double-processing.

In v1, the actual pipeline runs by spawning `hermes -s solomon-orchestrator -q "process event <id>"` (subprocess). The orchestrator skill loads `orchestrator/pipeline/` Python modules per stage.
