"""Stage 10 — Action. Routes per (effective_autonomy, audit_verdict).

Routes:
- L4 + APPROVE → ship silently; daily digest mention
- L3 + APPROVE → ship for routine; one-tap for novel
- L2 / L3 + DOWNGRADE → one-tap to Telegram (approve/edit/discuss)
- L1 + APPROVE / L0 → suggestion only, queued for next digest
- REJECT / REQUEST_RETHINK after retry → escalate to mentoring_queue priority 2
"""
from ._helpers import db_connect, update_event, stage_timer


def effective_autonomy(scope_level: int, owner_state: str) -> int:
    """Owner-state caps the per-scope level."""
    ceil_by_state = {"green": 4, "yellow": 2, "red": 1, "unknown": 4}
    return min(scope_level, ceil_by_state.get(owner_state, 4))


def run(event_id: str, classification: dict, audit_verdict: str, owner_state: str):
    with stage_timer(event_id, "action"):
        scope = classification.get("scope", "none")
        # Look up scope autonomy
        conn = db_connect()
        try:
            row = conn.execute(
                "SELECT level FROM scope_autonomy WHERE scope = ?", (scope,)
            ).fetchone()
        finally:
            conn.close()
        scope_level = row[0] if row else 0  # default L0 if scope unknown
        eff = effective_autonomy(scope_level, owner_state)

        # Route
        if audit_verdict in {"REJECT", "REQUEST_RETHINK"}:
            action = f"escalate (mentoring_queue priority 2; scope={scope}, eff_level=L{eff})"
        elif eff == 4 and audit_verdict == "APPROVE":
            action = f"ship silently (scope={scope}, L{eff})"
        elif eff in (2, 3) or audit_verdict == "DOWNGRADE":
            action = f"one-tap to Telegram (scope={scope}, eff_level=L{eff})"
        else:
            action = f"suggestion only (scope={scope}, eff_level=L{eff})"

        update_event(event_id, action_taken=action, status="complete")
    return action
