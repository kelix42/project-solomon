"""Pipeline runner — walks the 10 stages in order for one event.

Invoked by the pipeline-tick worker (subprocess) or directly via `python -m solomon.orchestrator.pipeline.runner <event_id>`.
"""
import json
import logging
import sys
from pathlib import Path

from . import (
    stage_action,
    stage_audit,
    stage_capture,
    stage_classification,
    stage_hard_rule,
    stage_owner_state,
    stage_retrieval,
    stage_salience,
    stage_system1,
    stage_system2,
)
from ._helpers import db_connect, update_event

LOG = logging.getLogger("orchestrator.runner")


def run(event_id: str):
    LOG.info("pipeline start: event=%s", event_id)

    capture = stage_capture.run(event_id)

    salience = stage_salience.run(event_id, capture)
    if salience < 0.30:
        update_event(event_id, status="skipped")
        LOG.info("pipeline skip (low salience): event=%s score=%.2f", event_id, salience)
        return

    classification = stage_classification.run(event_id, capture)

    blocked = stage_hard_rule.run(event_id, capture, classification)
    if blocked:
        LOG.info("pipeline blocked_by_hard_rule: event=%s rule=%s", event_id, blocked.get("id"))
        return

    retrieval = stage_retrieval.run(event_id, classification)
    s1 = stage_system1.run(event_id, capture, retrieval)
    s2 = stage_system2.run(event_id, capture, retrieval, s1)
    verdict = stage_audit.run(event_id, capture, s1, s2)
    state = stage_owner_state.run(event_id)
    action = stage_action.run(event_id, classification, verdict, state)

    LOG.info("pipeline complete: event=%s action=%s", event_id, action)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if len(sys.argv) < 2:
        print("usage: python -m solomon.orchestrator.pipeline.runner <event_id>")
        sys.exit(1)
    run(sys.argv[1])


if __name__ == "__main__":
    main()
