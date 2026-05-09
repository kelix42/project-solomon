"""corpus-inbox-watcher — Solomon worker (§2.4).

Recursive file watcher on corpus/inbox/. Debounce 30s after last event, capped at
5 resets OR 5 minutes from first event (livelock prevention). 3-second file-stable
size check. Triggers ingest by writing a db.events row with source=file_dropped;
the pipeline-tick worker (or solomon-corpus-ingest invocation) picks up.

If Hermes is killed mid-debounce, the in-memory timer is lost. On restart, the
catch-up scan re-detects the file; SHA256 manifest in db.ingested_files prevents
double-ingest.
"""
import json
import logging
import os
import signal
import sqlite3
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path


SOLOMON_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = SOLOMON_ROOT / "db" / "solomon.db"
INBOX = SOLOMON_ROOT / "corpus" / "inbox"
LOG = logging.getLogger("worker.corpus-inbox-watcher")
RUNNING = True

DEBOUNCE_SECONDS = 30
DEBOUNCE_MAX_RESETS = 5
DEBOUNCE_MAX_TOTAL_SECONDS = 300
FILE_STABLE_SECONDS = 3


def connect_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


class DebounceState:
    def __init__(self):
        self.lock = threading.Lock()
        self.pending: set = set()
        self.first_event_at: float = 0.0
        self.last_event_at: float = 0.0
        self.resets: int = 0


STATE = DebounceState()


def is_file_stable(path: Path) -> bool:
    """Confirm size is unchanged for FILE_STABLE_SECONDS consecutive seconds."""
    try:
        s1 = path.stat().st_size
    except FileNotFoundError:
        return False
    time.sleep(FILE_STABLE_SECONDS)
    try:
        s2 = path.stat().st_size
    except FileNotFoundError:
        return False
    return s1 == s2 and s1 > 0


def queue_for_ingest(paths):
    """Write a db.events row per file; pipeline-tick (or corpus-ingest skill) picks them up."""
    conn = connect_db()
    try:
        for p in paths:
            event_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO events (event_id, source, payload, received_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    "file_dropped",
                    json.dumps({"path": str(p)}),
                    datetime.utcnow().isoformat() + "Z",
                    "pending",
                ),
            )
        LOG.info("queued %d files for ingest", len(paths))
    finally:
        conn.close()


def fire_ingest():
    """Drain pending set; require file-stable; queue to db.events."""
    with STATE.lock:
        candidates = list(STATE.pending)
        STATE.pending.clear()
        STATE.first_event_at = 0.0
        STATE.last_event_at = 0.0
        STATE.resets = 0
    stable = []
    for path in candidates:
        if Path(path).exists() and is_file_stable(Path(path)):
            stable.append(Path(path))
    if stable:
        queue_for_ingest(stable)


def debounce_loop():
    """Background loop: check if the debounce window has expired and fire."""
    while RUNNING:
        time.sleep(1)
        now = time.time()
        with STATE.lock:
            if not STATE.pending:
                continue
            window_age = now - STATE.first_event_at
            since_last = now - STATE.last_event_at
            should_fire = (
                since_last >= DEBOUNCE_SECONDS
                or window_age >= DEBOUNCE_MAX_TOTAL_SECONDS
                or STATE.resets >= DEBOUNCE_MAX_RESETS
            )
        if should_fire:
            fire_ingest()


def on_event(path: str):
    """Handler called by watchdog on any FS event under inbox/."""
    p = Path(path)
    if not p.is_file():
        return
    # Skip parking folders
    if "_oversized" in p.parts or "_unsupported" in p.parts or "_pre-redaction" in p.parts:
        return
    now = time.time()
    with STATE.lock:
        if STATE.first_event_at == 0.0:
            STATE.first_event_at = now
        STATE.last_event_at = now
        STATE.resets = min(STATE.resets + 1, DEBOUNCE_MAX_RESETS + 1)
        STATE.pending.add(str(p))


def catchup_scan():
    """On startup, scan for pre-existing files and queue them."""
    if not INBOX.exists():
        return
    pre = []
    for p in INBOX.rglob("*"):
        if not p.is_file():
            continue
        if "_oversized" in p.parts or "_unsupported" in p.parts or "_pre-redaction" in p.parts:
            continue
        pre.append(p)
    if pre:
        LOG.info("catchup_scan found %d pre-existing files", len(pre))
        queue_for_ingest(pre)


def handle_shutdown(signum, frame):
    global RUNNING
    LOG.info("shutdown signal received")
    RUNNING = False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    INBOX.mkdir(parents=True, exist_ok=True)

    catchup_scan()

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        LOG.error("watchdog not installed; falling back to 5s poll")
        # Polling fallback
        seen = set()
        while RUNNING:
            for p in INBOX.rglob("*"):
                if p.is_file() and "_oversized" not in p.parts and str(p) not in seen:
                    seen.add(str(p))
                    on_event(str(p))
            time.sleep(5)
        return

    class _H(FileSystemEventHandler):
        def on_created(self, event):
            on_event(event.src_path)
        def on_modified(self, event):
            on_event(event.src_path)
        def on_moved(self, event):
            on_event(event.dest_path)

    observer = Observer()
    observer.schedule(_H(), str(INBOX), recursive=True)
    observer.start()
    LOG.info("corpus-inbox-watcher started; recursive watch on %s", INBOX)

    debouncer = threading.Thread(target=debounce_loop, name="debouncer", daemon=True)
    debouncer.start()

    while RUNNING:
        time.sleep(1)

    observer.stop()
    observer.join(timeout=5)
    LOG.info("corpus-inbox-watcher stopped cleanly")


if __name__ == "__main__":
    main()
