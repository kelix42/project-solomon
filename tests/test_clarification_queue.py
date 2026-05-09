"""Stub for clarification_queue end-to-end flow.

Smoke test: contradiction-check inserts a row -> interview-engine reads it BEFORE
the next probe. The actual interview-engine is a markdown skill; this test just
verifies the schema + CRUD contract.
"""
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "db" / "schemas"


def _setup_db(td: Path) -> sqlite3.Connection:
    db = td / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=WAL;")
    for sql in sorted(SCHEMAS.glob("*.sql")):
        conn.executescript(sql.read_text())
    return conn


def test_clarification_queue_lifecycle():
    with tempfile.TemporaryDirectory() as td:
        conn = _setup_db(Path(td))
        sid = "onboarding-03-2026-05-09"
        conn.execute(
            """INSERT INTO clarification_queue
            (session_id, captured_id_a, captured_id_b, suggested_probe, status, created_at)
            VALUES (?, ?, ?, ?, 'queued', ?)""",
            (sid, "01HA", "01HB", "Earlier you said X; just now Y. Which wins?", "2026-05-09T00:00:00Z"),
        )

        # Interview-engine reads queued items for this session
        rows = conn.execute(
            "SELECT id, suggested_probe FROM clarification_queue WHERE session_id = ? AND status = 'queued'",
            (sid,),
        ).fetchall()
        assert len(rows) == 1

        # Mark as asked, then resolved
        cid = rows[0][0]
        conn.execute("UPDATE clarification_queue SET status='asked' WHERE id=?", (cid,))
        conn.execute(
            "UPDATE clarification_queue SET status='resolved', resolved_at=?, resolution_id=? WHERE id=?",
            ("2026-05-09T00:01:00Z", "01HC", cid),
        )

        row = conn.execute("SELECT status, resolution_id FROM clarification_queue WHERE id=?", (cid,)).fetchone()
        assert row == ("resolved", "01HC")
        conn.close()
