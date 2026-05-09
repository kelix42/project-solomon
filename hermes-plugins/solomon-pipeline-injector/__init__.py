"""solomon-pipeline-injector — Hermes plugin.

Hooks `pre_llm_call`. When the gateway receives a Telegram message, this hook fires.
Classifies the message intent (text / one-tap callback / mentoring answer) and writes
a `db.events` row with `status = pending`. The `pipeline-tick` worker (§2.4.6.5)
picks up pending rows every 60s and runs the §2.2.5 pipeline against each.
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


SOLOMON_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = SOLOMON_ROOT / "db" / "solomon.db"


def _connect():
    """Open a WAL-mode connection to db/solomon.db. Hermes does NOT inject this."""
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def register(ctx):
    ctx.register_hook("pre_llm_call", on_pre_llm)


def on_pre_llm(session_id, user_message, conversation_history, is_first_turn, model, platform, **kwargs):
    """Classify and queue, then return None so Hermes proceeds normally."""
    # Only act on the first turn of a Telegram-platform session
    if platform != "telegram" or not is_first_turn:
        return None

    event_id = str(uuid.uuid4())  # ulid in production; uuid for now
    payload = json.dumps({"text": user_message, "session_id": session_id})

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO events (event_id, source, payload, received_at, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, "telegram", payload, datetime.utcnow().isoformat() + "Z", "pending"),
        )
    finally:
        conn.close()

    # Returning None lets Hermes continue with the normal LLM call.
    # The pipeline-tick worker will process this event in parallel.
    return None
