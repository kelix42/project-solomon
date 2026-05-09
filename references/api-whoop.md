# Whoop — owner-state biometrics

`hermes-plugins/whoop-bridge/` — exposes Whoop metrics for Pipeline Stage 9 (owner-state gate).

## Required env vars

- `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET` — OAuth credentials
- Refresh token managed by Hermes' OAuth manager

## Tool exposed

`whoop.get_today()` — returns `{recovery_pct, sleep_hours, strain, stress_flag, captured_at}` for today.

## Owner-state gate

Reads latest `db.biometrics` row:

- Green: recovery > 60% AND sleep > 7h → full scope autonomy
- Yellow: recovery 33–60% OR sleep 5–7h → downgrade to L2
- Red: recovery < 33% OR explicit stress flag → downgrade to L1
- Missing (plugin disabled or row > 24h stale): default Green; one-time warning logged

## Polling cadence

5-min REST poller writes `db.biometrics` rows. v2.1 may switch to push if Whoop adds webhooks.

## v1 status

Plugin scaffold + `_TODO_SPEC.md`. Owner provides OAuth credentials.
