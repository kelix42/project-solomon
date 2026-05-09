# Google Workspace — Gmail + Calendar + Drive (via Google MCP)

Single integration covers Gmail + Calendar + Drive (Docs, Sheets). Implemented as `hermes-plugins/google-workspace/`.

## Required env vars

- `GOOGLE_MCP_SERVER_URL` — the Google MCP server endpoint. OAuth alone is NOT sufficient.
- Google OAuth tokens (handled by Hermes' OAuth manager).

## Tools exposed to skills

(via the Google MCP server — `dispatch_tool` from the agent)

- `gmail.list_messages`, `gmail.read_message`, `gmail.send_message`
- `calendar.list_events`, `calendar.create_event`, `calendar.update_event`
- `drive.search_files`, `drive.read_file_content`, `drive.create_file`

## v1 status

Plugin scaffold ships with `_TODO_SPEC.md`. Gmail watch + 60s backup poller, Calendar events watch, and Drive `changes.watch` API integration are deferred to v2.1 pending owner sign-off (§2.4.5).

## Optional secondary backup destination

If enabled, Sleep-Cycle Job 10 (`corpus-backup`) writes a second copy of each encrypted tarball to a Drive folder. Default backup destination is `BACKUP_DEST_LOCAL` (local path) to avoid the chicken-and-egg recovery problem.
