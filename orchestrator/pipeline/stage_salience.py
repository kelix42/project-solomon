"""Stage 2 — Salience scorer. Haiku, ~50 tokens out. Returns 0.0-1.0 across stakes/novelty/emotion/owner-involvement."""
import json
from ._helpers import llm_dispatch, update_event, stage_timer

SALIENCE_PROMPT = """You are Solomon's salience scorer. Rate this event 0.0-1.0 across four dimensions:
- stakes: how high are the consequences?
- novelty: how unusual is this for the owner's business?
- emotion: how charged is the language?
- owner_involvement: how much does this require the owner specifically?

Return JSON only: {"stakes": 0.x, "novelty": 0.x, "emotion": 0.x, "owner_involvement": 0.x, "combined": 0.x}
Combined = max of the four.
"""


def run(event_id: str, capture: dict) -> float:
    with stage_timer(event_id, "salience"):
        result = llm_dispatch(
            "SOLOMON_MODEL_SALIENCE",
            prompt=f"Event: {capture['payload']}",
            system=SALIENCE_PROMPT,
            max_tokens=80,
        )
        try:
            parsed = json.loads(result)
            score = float(parsed.get("combined", 0.0))
        except Exception:
            score = 0.0
        update_event(event_id, salience_score=score)
    return score
