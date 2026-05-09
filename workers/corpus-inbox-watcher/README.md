# corpus-inbox-watcher

Long-lived Python worker. Recursive file watcher on `corpus/inbox/`. Auto-queues new files to `db.events` for the `solomon-corpus-ingest` skill (§2.4).

## Behaviour

- 30-second debounce after last file event.
- Cap: 5 resets OR 5 minutes from the first event (livelock prevention).
- 3-second file-stable size check before triggering.
- Recursive watch (catches nested folder drops).
- Catch-up scan on startup picks up pre-existing files.
- Skips parking folders (`_oversized`, `_unsupported`, `_pre-redaction`).

## Known behaviour

If Hermes is killed mid-debounce, the in-memory timer is lost. On restart, the catch-up scan re-detects the file; the SHA256 manifest in `db.ingested_files` prevents double-ingest.
