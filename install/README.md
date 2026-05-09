# Install

The single supported install command:

```bash
bash install.sh
```

**Do not** use `hermes skills install` against this repo. It skips:

- DB init (the 17 SQL schemas with WAL pragmas)
- Plugin symlinks (Hermes won't find `hermes-plugins/`)
- Pinecone index creation (you'll get errors when the agent tries to query)
- BIP-39 backup-key flow (no recovery path on a dead laptop)

`bash install.sh` is the one entry point. It's idempotent — re-running just verifies and exits "all good."

## What you'll be prompted for

1. **Pinecone API key** — required. Get one at https://app.pinecone.io/keys.
2. **OpenAI API key** — required (for `text-embedding-3-large`). Get one at https://platform.openai.com/api-keys.
3. **Telegram bot token** — required. Make a bot via [@BotFather](https://t.me/BotFather).
4. **Telegram chat ID** — your user ID. Send `/start` to your bot once after creation; Hermes captures it.
5. **Optional integrations menu** — multi-select. Corpus auto-ingest watcher is default ON; the rest are off until their per-source spec is locked.
6. **Backup passphrase** — used to derive the Argon2id wrap key. You'll also be shown a 24-word BIP-39 mnemonic ONCE — save it to a password manager AND on paper.

## What it does

1. Detects existing Hermes config in `~/.hermes/.env` and reuses anything already set.
2. Symlinks this repo to `~/.hermes/skills/solomon/`.
3. Symlinks `hermes-plugins/*/` to `~/.hermes/plugins/`.
4. Initializes `db/solomon.db` from `db/schemas/*.sql` with WAL pragmas (17 tables).
5. Generates the BIP-39 24-word backup key (only on first install).
6. Creates the `solomon` Pinecone serverless index with `dimension=3072`, materializes 4 namespaces.
7. Verifies plugins load via `hermes plugins list | grep solomon-`.
8. Appends a first entry to `decisions/log.md`.
9. Auto-launches `hermes -s solomon-onboarding -q "begin"` — Session 0 of the foundation interview.

## Recovery on a new laptop

```bash
bash install.sh --restore /path/to/backup.tar.gz.enc
```

You'll be prompted for the 24-word BIP-39 mnemonic (or the passphrase if `~/.hermes/.env` happens to be available). See `install/bootstrap.md`.

## Re-running

`bash install.sh` is safe to re-run. Every step skips when already-done. Use it after editing `.env`, after pulling new code, or to repair a broken supervisor unit.
