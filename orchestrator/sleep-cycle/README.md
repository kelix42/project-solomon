# Sleep Cycle — 12 Nightly Jobs

Hermes' gateway cron (verified built-in) registers all 12 jobs at install time. Default schedule: `0 3 * * *` owner-local time. Each job runs as a fresh isolated agent session with the corresponding skill attached. Failure of one does not block the others.

## Files

`jobNN_<name>.py` — one file per job, each defining a `run()` entrypoint. Sleep-cycle skills (one per job in `skills/learning/`) call into these via `dispatch_tool`.

## Order

1. hindsight
2. archival
3. surprise-replay
4. stress-test
5. conflict-detection
6. working-memory-cleanup
7. autonomy-reeval
8. mentoring-scheduler
9. corpus-lint
10. corpus-backup
11. embed-pending
12. yaml-reconcile

## Owner overrides

- `/solomon-sleep-now` — runs all 12 in sequence
- `/solomon-sleep-job <name>` — runs one
- `/solomon-sleep-skip <name>` — defers to tomorrow
- `/cron list` — Hermes-built-in
