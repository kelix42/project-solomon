"""pipeline-tick — Solomon worker (§2.4.6.5).

Every 60 seconds, scan db.events WHERE status='pending'. For each pending event,
spawn a fresh Hermes agent session that runs the orchestrator pipeline (§2.2.5).
Concurrency capped at PIPELINE_MAX_IN_FLIGHT (config in corpus/schema.md, default 5).

This worker is the bridge between Solomon's event queue and Hermes' per-session
agent invocations. It does NOT run the pipeline itself — Hermes does, when invoked
via subprocess. This worker just queues and dispatches.
"""
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


SOLOMON_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = SOLOMON_ROOT / "db" / "solomon.db"
LOG = logging.getLogger("worker.pipeline-tick")
RUNNING = True
MAX_IN_FLIGHT = 5  # config in corpus/schema.md `pipeline_max_in_flight`
TICK_SECONDS = 60
in_flight_lock = threading.Lock()
in_flight_count = 0


def connect_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def claim_event(conn, event_id: str) -> bool:
    """Atomic claim: only one tick can mark an event in_progress."""
    cur = conn.execute(
        """
        UPDATE events
        SET status = 'in_progress', processed_at = ?
        WHERE event_id = ? AND status = 'pending'
        """,
        (datetime.utcnow().isoformat() + "Z", event_id),
    )
    return cur.rowcount == 1


def run_pipeline_for_event(event_id: str):
    """Spawn a Hermes agent session that runs the orchestrator pipeline for this event."""
    global in_flight_count
    try:
        # In production: subprocess.run(["hermes", "-s", "solomon-orchestrator", "-q", f"process event {event_id}"], ...)
        # Stub for v1: log and mark complete. Real wiring lives in orchestrator/pipeline/.
        LOG.info("processing event %s (stub — wire to orchestrator/pipeline/ Python module)", event_id)
        time.sleep(2)  # placeholder
        conn = connect_db()
        try:
            conn.execute(
                "UPDATE events SET status = 'complete', processed_at = ? WHERE event_id = ?",
                (datetime.utcnow().isoformat() + "Z", event_id),
            )
        finally:
            conn.close()
    except Exception:
        LOG.exception("pipeline error for event %s", event_id)
        conn = connect_db()
        try:
            conn.execute("UPDATE events SET status = 'failed' WHERE event_id = ?", (event_id,))
        finally:
            conn.close()
    finally:
        with in_flight_lock:
            in_flight_count -= 1


def tick():
    """One tick: claim up to (MAX_IN_FLIGHT - in_flight_count) pending events and dispatch."""
    global in_flight_count
    with in_flight_lock:
        slots = MAX_IN_FLIGHT - in_flight_count
    if slots <= 0:
        return
    conn = connect_db()
    try:
        rows = conn.execute(
            "SELECT event_id FROM events WHERE status = 'pending' ORDER BY received_at LIMIT ?",
            (slots,),
        ).fetchall()
    finally:
        conn.close()
    for (event_id,) in rows:
        conn = connect_db()
        try:
            if not claim_event(conn, event_id):
                continue
        finally:
            conn.close()
        with in_flight_lock:
            in_flight_count += 1
        threading.Thread(
            target=run_pipeline_for_event, args=(event_id,), daemon=True, name=f"pipeline-{event_id[:8]}"
        ).start()


def handle_shutdown(signum, frame):
    global RUNNING
    LOG.info("shutdown signal received; waiting for in-flight pipelines to finish")
    RUNNING = False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    LOG.info("pipeline-tick started; ticking every %ds, max %d in-flight", TICK_SECONDS, MAX_IN_FLIGHT)

    while RUNNING:
        try:
            tick()
        except Exception:
            LOG.exception("tick error")
        for _ in range(TICK_SECONDS):
            if not RUNNING:
                break
            time.sleep(1)

    # Wait briefly for in-flight to finish
    deadline = time.time() + 30
    while time.time() < deadline:
        with in_flight_lock:
            if in_flight_count == 0:
                break
        time.sleep(1)
    LOG.info("pipeline-tick stopped cleanly")


if __name__ == "__main__":
    main()
