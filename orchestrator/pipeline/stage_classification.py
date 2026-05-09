"""Stage 3 — Classification. Sonnet. Returns {scope, domain, decision_type}."""
import json
from ._helpers import llm_dispatch, update_event, stage_timer

CLASSIFICATION_PROMPT = """You are Solomon's classifier. Given an event, return:
- scope: one of [pricing, hiring, ops, customer, vendor, finance, scheduling, communication, none]
- domain: same vocabulary as scope, more specific if applicable
- decision_type: one of [propose, approve, ship, escalate, schedule, archive]

Return JSON only: {"scope": "...", "domain": "...", "decision_type": "..."}
"""


def run(event_id: str, capture: dict) -> dict:
    with stage_timer(event_id, "classification"):
        result = llm_dispatch(
            "SOLOMON_MODEL_CLASSIFICATION",
            prompt=f"Event: {capture['payload']}",
            system=CLASSIFICATION_PROMPT,
            max_tokens=120,
        )
        try:
            parsed = json.loads(result)
        except Exception:
            parsed = {"scope": "none", "domain": "unknown", "decision_type": "escalate"}
        update_event(event_id, classification=json.dumps(parsed))
    return parsed
