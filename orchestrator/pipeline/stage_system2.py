"""Stage 7 — System 2 reasoner (Opus, chain-of-thought) + Stage 7b — token-Jaccard divergence."""
import re
from ._helpers import llm_dispatch, update_event, stage_timer

SYSTEM2_PROMPT = """You are Solomon's System 2. Reason carefully. You may explore alternatives.
Return: <reasoning paragraph(s)> followed by <final answer in 1-2 sentences>.
"""

STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in", "on", "at", "for", "and", "or"}


def _tokenize(text: str) -> set:
    return {w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS}


def jaccard(a: str, b: str) -> float:
    sa, sb = _tokenize(a), _tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def length_ratio(a: str, b: str) -> float:
    la, lb = len(a), len(b)
    if max(la, lb) == 0:
        return 0.0
    return min(la, lb) / max(la, lb)


def run(event_id: str, capture: dict, retrieval: dict, system1_output: str) -> str:
    with stage_timer(event_id, "system2"):
        result = llm_dispatch(
            "SOLOMON_MODEL_SYSTEM2",
            prompt=f"Event: {capture['payload']}\nContext: {retrieval}",
            system=SYSTEM2_PROMPT,
            max_tokens=2000,
        )
        update_event(event_id, system2_output=result)

    # Stage 7b: divergence check — token-Jaccard, NO embeddings (§2.2.5 Stage 7b).
    with stage_timer(event_id, "divergence"):
        score = 0.6 * jaccard(system1_output, result) + 0.4 * length_ratio(system1_output, result)
        update_event(event_id, divergence_score=score)
        # Caller: if score < 0.7, write mentoring_queue row priority 4 source=surprise.
    return result
