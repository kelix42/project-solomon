"""Template worker for Solomon.

Long-lived Python service. Supervised by launchd/systemd (§2.4.9).
Shares db/solomon.db with Hermes via WAL mode. Plugins NEVER open their own DB connections,
but workers DO — workers are not Hermes plugins.

Usage:
    python -m solomon.workers._template_worker
"""
import logging
import os
import signal
import sqlite3
import sys
import time
from pathlib import Path


SOLOMON_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = SOLOMON_ROOT / "db" / "solomon.db"
LOG = logging.getLogger("worker._template")
RUNNING = True


def connect_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def handle_shutdown(signum, frame):
    global RUNNING
    LOG.info("shutdown signal received")
    RUNNING = False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    LOG.info("template worker started")

    while RUNNING:
        try:
            # ─── do work here ───
            time.sleep(60)
        except Exception:
            LOG.exception("worker loop error; sleeping 30s")
            time.sleep(30)

    LOG.info("template worker stopped cleanly")


if __name__ == "__main__":
    main()
