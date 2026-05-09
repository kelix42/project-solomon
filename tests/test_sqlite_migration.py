"""SQLite schema applies cleanly with WAL pragmas. All 17 schema files load without error."""
import glob
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "db" / "schemas"


def test_all_schemas_apply_with_wal():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test.db"
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        for sql in sorted(SCHEMAS.glob("*.sql")):
            conn.executescript(sql.read_text())
        conn.commit()

        # WAL is enabled?
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert mode == "wal"

        # All 17 tables exist
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        expected = {
            "captured_items", "coverage", "vocabulary", "ingested_files",
            "mentoring_queue", "clarification_queue", "sessions", "wiki_vectors",
            "events", "working_memory", "scope_autonomy", "proposed_rules",
            "decisions", "audits", "biometrics", "rules_of_thumb", "mentoring_sessions",
            "plaud_state",
        }
        missing = expected - tables
        assert not missing, f"missing tables: {missing}"
        conn.close()


def test_idempotent_apply_twice():
    """Applying the schema twice (e.g., a re-run of install.sh) should not error."""
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test.db"
        for _ in range(2):
            conn = sqlite3.connect(db)
            for sql in sorted(SCHEMAS.glob("*.sql")):
                conn.executescript(sql.read_text())
            conn.close()
