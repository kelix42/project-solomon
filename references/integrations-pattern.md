# Integrations Pattern — how to add a new tool the owner uses

Solomon has two integration shapes:

## Hermes plugin (provides tools to skills)

When the integration exposes capabilities the agent's reasoning loop should use (read Gmail, search Drive, push to a workflow), it's a Hermes plugin.

1. Copy `hermes-plugins/_template-hermes-plugin/` to `hermes-plugins/<your-slug>/`.
2. Edit `plugin.yaml`: name, version, description, `requires_env`, `requires_python`.
3. Edit `__init__.py`: implement `register(ctx)` using only the verified API surface (§2.4.6 of SOLOMON-PLAN.md).
4. Add a row to `connections.md`.
5. Restart the Hermes gateway service: `launchctl kickstart -k gui/$UID/io.solomon.hermes-gateway` (macOS) or `systemctl --user restart solomon-hermes-gateway` (Linux).

## Worker (long-lived background service)

When the integration polls, watches files, or maintains a stateful connection (IMAP IDLE, file watcher, REST poller), it's a worker.

1. Copy `workers/_template-worker/` to `workers/<your-slug>/`.
2. Edit `worker.yaml`: name, version, description, `requires_env`, `requires_python`, `supervisor` field (`launchd` / `systemd` / `both`).
3. Edit `__main__.py`: long-running loop, opens `db/solomon.db` with WAL pragmas, writes events / files as appropriate.
4. Add a per-worker state table to `db/schemas/<slug>_state.sql` if you need persistent state.
5. `install.sh` writes the launchd/systemd unit on next run; or run `bash install.sh --add-worker <slug>` for a hot install.
6. Add a row to `connections.md`.

## Per-source ingress spec template

Every ingress integration must reach Plaud-equivalent depth (§2.4.5):

- Idempotency token (provider-side message ID, ETag, IMAP UID)
- Dedup mechanism (in-memory set + persistent state table)
- ISO-timestamped filename convention: `YYYY-MM-DDTHH-MM-SS--<source>--<provider-id>.<ext>`
- Target subfolder under `corpus/inbox/<category>/` (or direct `db.events` write for real-time-only sources)
- Mark source-side as read/processed
- Logging convention: `corpus/log.md` with the slug as prefix
- Required env vars list
- Persistent state table schema

The "Spec TBD" integrations in `connections.md` (Telegram-as-ingress, Gmail watch, Drive watch, Calendar watch, Whoop poller, n8n/make webhook) need this spec before their workers can be implemented.
