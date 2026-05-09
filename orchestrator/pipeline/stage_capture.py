"""Stage 1 — Capture. Already done by ingress workers (telegram via solomon-pipeline-injector,
plaud via plaud-ingest, file_dropped via corpus-inbox-watcher). This module just validates the
event row exists and is well-formed.
"""
from ._helpers import db_connect


def run(event_id: str) -> dict:
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT source, payload, received_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise RuntimeError(f"event {event_id} missing from db.events")
    source, payload, received_at = row
    return {"source": source, "payload": payload, "received_at": received_at}
