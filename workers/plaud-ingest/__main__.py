"""plaud-ingest — Solomon worker (§2.4.5).

Plaud sends transcripts as emails with .txt attachments via AutoFlow. This worker
watches the inbox over IMAP with two threads:

1. IDLE listener — grabs new mail the instant it arrives.
2. 60s backup poller — checks every 60s in case IDLE missed one.

Both threads search with UNSEEN+FROM so Gmail only returns unread mail. After
download, the email is marked \\Seen and the email-id is added to an in-memory
dedup set so IDLE and the poller can't double-process. Files are renamed with
ISO timestamps and saved to corpus/inbox/messages/. The corpus-inbox-watcher
worker picks them up from there.

Persistent state lives in db.plaud_state (last_seen_uid, recent_email_ids 7-day
ring buffer, last_idle_at, last_poll_at, consecutive_fails).

Gmail note: PLAUD_IMAP_PASS must be an app-password if PLAUD_IMAP_HOST is
imap.gmail.com. Regular passwords are rejected on IMAP.
"""
import email
import json
import logging
import os
import signal
import sqlite3
import sys
import threading
import time
from datetime import datetime, timedelta
from email.message import Message
from pathlib import Path


SOLOMON_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = SOLOMON_ROOT / "db" / "solomon.db"
INBOX_MESSAGES = SOLOMON_ROOT / "corpus" / "inbox" / "messages"
LOG = logging.getLogger("worker.plaud-ingest")
RUNNING = True
DOWNLOADED_EMAIL_IDS: set = set()  # in-memory dedup; persisted to db.plaud_state.recent_email_ids
DEDUP_LOCK = threading.Lock()


def connect_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def load_state():
    """Read recent_email_ids from db.plaud_state into the in-memory dedup set."""
    conn = connect_db()
    try:
        row = conn.execute("SELECT recent_email_ids FROM plaud_state WHERE id = 1").fetchone()
        if row and row[0]:
            global DOWNLOADED_EMAIL_IDS
            DOWNLOADED_EMAIL_IDS = set(json.loads(row[0]))
            LOG.info("loaded %d recent_email_ids from db.plaud_state", len(DOWNLOADED_EMAIL_IDS))
    finally:
        conn.close()


def save_state(uid: int = None, source: str = "idle"):
    """Persist the dedup set + last-seen UID + timestamp to db.plaud_state."""
    cutoff_iso = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    with DEDUP_LOCK:
        ids = list(DOWNLOADED_EMAIL_IDS)[-2000:]  # bounded
    conn = connect_db()
    try:
        ts = datetime.utcnow().isoformat() + "Z"
        col = "last_idle_at" if source == "idle" else "last_poll_at"
        sql = f"UPDATE plaud_state SET recent_email_ids = ?, {col} = ?"
        params = [json.dumps(ids), ts]
        if uid is not None:
            sql += ", last_seen_uid = ?"
            params.append(uid)
        sql += ", consecutive_fails = 0 WHERE id = 1"
        conn.execute(sql, params)
    finally:
        conn.close()


def record_failure(err: Exception):
    conn = connect_db()
    try:
        conn.execute(
            "UPDATE plaud_state SET consecutive_fails = consecutive_fails + 1 WHERE id = 1"
        )
        row = conn.execute("SELECT consecutive_fails FROM plaud_state WHERE id = 1").fetchone()
        fails = row[0] if row else 0
    finally:
        conn.close()
    LOG.error("plaud-ingest failure (#%d): %s", fails, err)
    if fails == 3:
        LOG.error("3 consecutive failures — would alert via Telegram. Check PLAUD_IMAP_PASS (Gmail needs an app-password).")


def save_attachment(part: Message, email_id: str) -> Path:
    """Save .txt attachment to corpus/inbox/messages/ with ISO timestamp prefix."""
    INBOX_MESSAGES.mkdir(parents=True, exist_ok=True)
    fname_orig = part.get_filename() or f"plaud-{email_id}.txt"
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    safe_email_id = email_id.replace("<", "").replace(">", "").replace("@", "-at-")
    path = INBOX_MESSAGES / f"{ts}--plaud--{safe_email_id}--{fname_orig}"
    path.write_bytes(part.get_payload(decode=True))
    LOG.info("saved attachment: %s", path.name)
    return path


def process_email(eid_bytes, mail):
    """Fetch one email by IMAP UID; download .txt attachments; mark Seen."""
    typ, msg_data = mail.fetch(eid_bytes, "(RFC822)")
    if typ != "OK":
        return
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)
    email_id = msg.get("Message-ID", "").strip()

    with DEDUP_LOCK:
        if email_id in DOWNLOADED_EMAIL_IDS:
            return
        DOWNLOADED_EMAIL_IDS.add(email_id)

    saved = 0
    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            fname = part.get_filename() or ""
            if fname.lower().endswith(".txt"):
                save_attachment(part, email_id)
                saved += 1

    if saved:
        mail.store(eid_bytes, "+FLAGS", "\\Seen")


def search_unseen(mail):
    """mail.search(None, '(UNSEEN FROM <PLAUD_SENDER>)') — Gmail only returns unread."""
    sender = os.getenv("PLAUD_SENDER", "no-reply@plaud.ai")
    typ, data = mail.search(None, f'(UNSEEN FROM "{sender}")')
    if typ != "OK" or not data or not data[0]:
        return []
    return data[0].split()


def poller_loop():
    """60-second backup poller."""
    import imaplib
    while RUNNING:
        try:
            mail = imaplib.IMAP4_SSL(os.getenv("PLAUD_IMAP_HOST"))
            mail.login(os.getenv("PLAUD_IMAP_USER"), os.getenv("PLAUD_IMAP_PASS"))
            mail.select("INBOX")
            for eid in search_unseen(mail):
                process_email(eid, mail)
            mail.logout()
            save_state(source="poll")
        except Exception as exc:
            record_failure(exc)
            time.sleep(300)  # 5 min cooldown after failure
            continue
        for _ in range(60):
            if not RUNNING:
                return
            time.sleep(1)


def idle_loop():
    """IMAP IDLE listener via imapclient."""
    try:
        from imapclient import IMAPClient
    except ImportError:
        LOG.warning("imapclient not installed; IDLE listener disabled, only 60s poller will run")
        return

    while RUNNING:
        try:
            with IMAPClient(os.getenv("PLAUD_IMAP_HOST"), use_uid=True, ssl=True) as mail:
                mail.login(os.getenv("PLAUD_IMAP_USER"), os.getenv("PLAUD_IMAP_PASS"))
                mail.select_folder("INBOX")
                while RUNNING:
                    mail.idle()
                    responses = mail.idle_check(timeout=290)  # IMAP IDLE max 29 min; refresh
                    mail.idle_done()
                    if responses:
                        sender = os.getenv("PLAUD_SENDER", "no-reply@plaud.ai")
                        uids = mail.search(['UNSEEN', 'FROM', sender])
                        for uid in uids:
                            process_email(str(uid).encode(), mail)
                        save_state(source="idle")
        except Exception as exc:
            record_failure(exc)
            time.sleep(300)


def handle_shutdown(signum, frame):
    global RUNNING
    LOG.info("shutdown signal received")
    RUNNING = False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    if not all(os.getenv(k) for k in ["PLAUD_IMAP_HOST", "PLAUD_IMAP_USER", "PLAUD_IMAP_PASS"]):
        LOG.error("plaud-ingest: missing required env vars; exiting (worker.yaml requires them).")
        sys.exit(1)

    load_state()
    LOG.info("plaud-ingest started; idle + 60s poller threads launching")

    poller = threading.Thread(target=poller_loop, name="plaud-poller", daemon=True)
    idle = threading.Thread(target=idle_loop, name="plaud-idle", daemon=True)
    poller.start()
    idle.start()

    while RUNNING:
        time.sleep(1)

    LOG.info("plaud-ingest stopped cleanly")


if __name__ == "__main__":
    main()
