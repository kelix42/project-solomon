"""Shared helpers for the orchestrator pipeline."""
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

SOLOMON_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = SOLOMON_ROOT / "db" / "solomon.db"

LOG = logging.getLogger("orchestrator.pipeline")


def db_connect():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def update_event(event_id: str, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [event_id]
    conn = db_connect()
    try:
        conn.execute(f"UPDATE events SET {sets} WHERE event_id = ?", vals)
    finally:
        conn.close()


def stage_timer(event_id: str, stage_name: str):
    """Context manager that records elapsed_ms into events.stage_timings_ms."""
    return _StageTimer(event_id, stage_name)


class _StageTimer:
    def __init__(self, event_id, stage_name):
        self.event_id = event_id
        self.stage_name = stage_name
        self.start = 0.0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc, tb):
        elapsed_ms = int((time.time() - self.start) * 1000)
        conn = db_connect()
        try:
            row = conn.execute(
                "SELECT stage_timings_ms FROM events WHERE event_id = ?", (self.event_id,)
            ).fetchone()
            d = json.loads(row[0]) if row and row[0] else {}
            d[self.stage_name] = elapsed_ms
            conn.execute(
                "UPDATE events SET stage_timings_ms = ? WHERE event_id = ?",
                (json.dumps(d), self.event_id),
            )
        finally:
            conn.close()


def llm_dispatch(model_env: str, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    """Dispatch an LLM call. Reads SOLOMON_MODEL_<STAGE> from env.

    Stub: returns a mock response. Real implementation calls Hermes' built-in tool
    `dispatch_tool('llm_call', {...})` or directly uses Anthropic / OpenRouter SDK.
    """
    model = os.getenv(model_env, "claude-sonnet-4-6")
    LOG.info("llm_dispatch model=%s tokens=%d", model, max_tokens)
    # Stub — wire to real LLM at runtime
    return "(stub LLM response — wire orchestrator/pipeline/_helpers.py llm_dispatch)"
