"""Stub for ingest-manifest SHA256 idempotency. Wires to db.ingested_files contract."""
import hashlib
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


def test_sha256_unique_constraint_blocks_duplicate():
    with tempfile.TemporaryDirectory() as td:
        conn = _setup_db(Path(td))
        sha = hashlib.sha256(b"hello world").hexdigest()
        conn.execute(
            """INSERT INTO ingested_files (id, sha256, inbox_path_at_ingest, size_bytes,
            category, ingest_run_id, status, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("01H1", sha, "/tmp/a.txt", 11, "docs", "run1", "success", "2026-05-09T00:00:00Z"),
        )
        # Second insert with the same sha must fail (UNIQUE constraint)
        try:
            conn.execute(
                """INSERT INTO ingested_files (id, sha256, inbox_path_at_ingest, size_bytes,
                category, ingest_run_id, status, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("01H2", sha, "/tmp/b.txt", 11, "docs", "run2", "success", "2026-05-09T00:00:01Z"),
            )
            assert False, "duplicate sha256 should have raised IntegrityError"
        except sqlite3.IntegrityError:
            pass
        conn.close()
