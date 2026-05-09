# plaud-ingest

Long-lived Python worker. IMAP IDLE listener + 60s backup poller for Plaud transcript emails.

See `references/api-plaud.md` for the full spec. Persistent state in `db.plaud_state`.

**Gmail authentication**: `PLAUD_IMAP_PASS` must be an app-password if `PLAUD_IMAP_HOST` is `imap.gmail.com`. Generate one at <https://myaccount.google.com/apppasswords>.

## Run manually

```bash
python -m solomon.workers.plaud_ingest
```

In production, the launchd `.plist` (macOS) or systemd `.service` (Linux) supervises this. See `install.sh`.
