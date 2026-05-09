"""Stage 6 — System 1 predictor. Sonnet. Rules-only, no reasoning."""
from ._helpers import llm_dispatch, update_event, stage_timer

SYSTEM1_PROMPT = """You are Solomon's System 1. Apply the owner's stated rules.
Return the rule-based answer in 1-2 sentences. NO reasoning. NO exploration.
"""


def run(event_id: str, capture: dict, retrieval: dict) -> str:
    with stage_timer(event_id, "system1"):
        result = llm_dispatch(
            "SOLOMON_MODEL_SYSTEM1",
            prompt=f"Event: {capture['payload']}\nContext: {retrieval}",
            system=SYSTEM1_PROMPT,
            max_tokens=200,
        )
        update_event(event_id, system1_output=result)
    return result
