"""Stage 4 — Hard-rule check. Deterministic Python eval, no LLM.

Reads foundation/05-non-negotiables.yaml and evaluates each rule's `condition`
as JSON-logic against the event payload + classification. Violations halt the pipeline.

captured_items.conditions is PROSE only; not evaluated here (see §2.2.5 + §1).
"""
import json
from pathlib import Path

import yaml

from ._helpers import db_connect, update_event, stage_timer

SOLOMON_ROOT = Path(__file__).resolve().parents[2]
NON_NEG = SOLOMON_ROOT / "foundation" / "05-non-negotiables.yaml"


def _eval_jsonlogic(condition, data):
    """Minimal JSON-logic interpreter. Production: use the json-logic-py package."""
    try:
        from json_logic import jsonLogic
        return jsonLogic(condition, data)
    except ImportError:
        return False  # fail-open is wrong for hard rules — but at install-time package is required


def run(event_id: str, capture: dict, classification: dict):
    with stage_timer(event_id, "hard_rule"):
        if not NON_NEG.exists():
            return None
        rules = yaml.safe_load(NON_NEG.read_text()).get("rules") or []
        data = {"event": {"payload": json.loads(capture["payload"]), "classification": classification}}
        for rule in rules:
            if _eval_jsonlogic(rule.get("condition"), data):
                update_event(event_id, status="blocked_by_hard_rule", hard_rule_blocked=rule.get("id"))
                return rule  # caller halts pipeline
    return None
