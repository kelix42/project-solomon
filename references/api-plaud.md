# Plaud — voice transcript ingress (worker, not plugin)

`workers/plaud-ingest/` — long-lived Python service. Plaud sends transcripts as emails with `.txt` attachments to the owner's configured email address from `no-reply@plaud.ai` via Plaud's AutoFlow feature.

## Required env vars

- `PLAUD_IMAP_HOST` — e.g., `imap.gmail.com`
- `PLAUD_IMAP_USER` — the email address Plaud sends to
- `PLAUD_IMAP_PASS` — IMAP password. **Gmail requires an app-password** (regular password rejected).
- `PLAUD_SENDER` — `no-reply@plaud.ai` by default

## Architecture

Two background threads:

1. **IDLE listener** — IMAP IDLE; grabs new mail the instant it arrives.
2. **60s backup poller** — checks every 60s in case IDLE missed one.

Both threads search with `mail.search(None, f'(UNSEEN FROM "{PLAUD_SENDER}")')` so Gmail only returns unread mail; old emails read before the plugin started never match.

After downloading an attachment:
- Plugin marks the email as read via `mail.store(eid, "+FLAGS", "\\Seen")` so next search skips it.
- In-memory `_downloaded_email_ids` set holds IDs already grabbed during the current run so IDLE and the 60s poller can't double-download.
- Each `.txt` attachment is renamed with an ISO timestamp prefix (`YYYY-MM-DDTHH-MM-SS--plaud--<email-id>.txt`) and saved to `corpus/inbox/messages/`.

From there `corpus-inbox-watcher` worker picks it up via the standard 30-second debounce + 3-second file-stable check, then invokes `solomon-corpus-ingest`, which routes to `corpus/raw/messages/`, redacts PII, generates wiki entries, embeds into Pinecone, and logs.

## Persistent state

`db.plaud_state` (singleton row): `last_seen_uid`, `recent_email_ids` (7-day ring buffer for crash-recovery dedup), `last_idle_at`, `last_poll_at`, `consecutive_fails`.

## Failure handling

Per §2.4.7: auth-failed → sleep 5 min, retry. After 3 failures, Telegram alert: "check `PLAUD_IMAP_PASS` — Gmail may need an app-password." Plugin keeps retrying.
