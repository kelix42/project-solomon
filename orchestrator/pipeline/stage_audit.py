"""Stage 8 — Audit gate. Independent Opus call. APPROVE / DOWNGRADE / REJECT / REQUEST_RETHINK."""
from ._helpers import llm_dispatch, update_event, stage_timer

AUDIT_PROMPT = """You are Solomon's independent audit gate. Inspect the proposed action against:
- Hard rules (foundation/05-non-negotiables.yaml)
- Active scope's stated rules from captured_items
- Owner state (Whoop signals)
- Coherence between System 1 (rule-based) and System 2 (reasoned) outputs

Return one verdict only: APPROVE | DOWNGRADE | REJECT | REQUEST_RETHINK
Followed by a brief (1-2 sentence) rationale.
"""


def run(event_id: str, capture: dict, system1: str, system2: str) -> str:
    with stage_timer(event_id, "audit"):
        result = llm_dispatch(
            "SOLOMON_MODEL_AUDIT",
            prompt=f"Event: {capture['payload']}\nSystem1: {system1}\nSystem2: {system2}",
            system=AUDIT_PROMPT,
            max_tokens=300,
        )
        verdict = result.split("\n")[0].strip().upper()
        if verdict not in {"APPROVE", "DOWNGRADE", "REJECT", "REQUEST_RETHINK"}:
            verdict = "REQUEST_RETHINK"
        update_event(event_id, audit_verdict=verdict)
    return verdict
