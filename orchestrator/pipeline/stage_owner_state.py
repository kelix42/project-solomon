"""Stage 9 — Owner-state gate. Reads latest db.biometrics row; modulates autonomy ceiling.

Green (recovery > 60% AND sleep > 7h): full scope autonomy
Yellow (recovery 33-60% OR sleep 5-7h): downgrade to L2 ceiling
Red (recovery < 33% OR explicit stress flag): downgrade to L1 ceiling
Missing (plugin disabled or stale > 24h): default Green; one-time warning logged
"""
from ._helpers import db_connect, update_event, stage_timer


def run(event_id: str) -> str:
    with stage_timer(event_id, "owner_state"):
        conn = db_connect()
        try:
            row = conn.execute(
                "SELECT recovery_pct, sleep_hours, stress_flag, captured_at FROM biometrics ORDER BY captured_at DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        if not row:
            update_event(event_id, owner_state="unknown")
            return "green"  # default Green on missing (per spec)
        recovery, sleep, stress, _captured = row
        if (recovery or 0) < 33 or stress:
            state = "red"
        elif (recovery or 0) < 60 or (sleep or 0) < 7:
            state = "yellow"
        else:
            state = "green"
        update_event(event_id, owner_state=state)
    return state
