# Install / Bootstrap & Recovery

Detail beyond `install/README.md`. Pinned per §2.10 of SOLOMON-PLAN.md.

## First install — backup-key flow

On the first run of `install.sh`, Solomon generates a **32-byte AES-256-GCM key** for backup encryption and presents it to you in two forms:

1. **Wrapped key** — derived from a passphrase you enter (Argon2id KDF). Stored at `~/.hermes/.env` as `SOLOMON_BACKUP_KEY_WRAPPED`. You'll use the passphrase day-to-day if `~/.hermes/.env` survives.
2. **24-word BIP-39 mnemonic** — the raw key, encoded as 24 English words. **Shown ONCE.** This is your recovery path on a dead laptop.

> **24 words = 256 bits + 8-bit checksum.** A 12-word mnemonic only encodes 128 bits and would silently halve your AES-256 key strength. Solomon refuses to generate a 12-word mnemonic.

**Save the mnemonic in two places**: a password manager AND on paper. Without it, your backups are unrecoverable. There is no "Solomon support" channel that can recover backups — the keys never leave your machine.

## Recovery on a dead laptop

```bash
git clone <owner>/solomon
cd solomon
bash install.sh --restore /path/to/backup.tar.gz.enc
```

Steps the script runs:

1. Hermes-detect, env-prompt, plugin-symlink — same as a normal install.
2. Prompts for the **24-word BIP-39 mnemonic** (or passphrase if `~/.hermes/.env` is available).
3. Decrypts the tarball (AES-256-GCM) into a temp dir.
4. Restores `db/solomon.db` and `corpus/{raw,wiki,index.md,log.md}` to the new install location.
5. **Re-embedding cost/time gate**:
   ```
   Restore plan: 4,231 raw chunks + 318 wiki pages + 612 captured_items + 89 decision-log entries
   Total: 5,250 vectors
   Estimated time at OpenAI's 3,000 RPM rate-limit: ~2 min
   Cost: see https://openai.com/api/pricing for `text-embedding-3-large` × 5,250
   Proceed? [y/N]
   ```
   Default `N`. Idempotent — re-fires if you abort.
6. Re-create the 4 Pinecone namespaces. Three cases:
   - Same Pinecone account, namespaces exist with matching dim → reuse, only re-embed missing vectors.
   - Different account or new namespaces → create them, **clear `embedded_at = NULL`** on every row in `captured_items` and `decisions` (the restore brought their old timestamps in but those vectors don't exist in the new account); re-embed everything.
   - Namespaces exist but `EMBEDDING_DIM` mismatches → fail with explicit message; edit `.env` and retry.
7. Run `solomon-audit` integrity pass.
8. "Welcome back" Telegram message confirming counts.

## Default backup destination — local first

`BACKUP_DEST_LOCAL=$HOME/Backups/solomon` is the default. Reason: **avoids the chicken-and-egg recovery problem**.

If your default were Google Drive, recovery would require you to re-OAuth to Drive on the new laptop AFTER you've supplied the BIP-39 mnemonic but BEFORE you can fetch the tarball. With local default, you just plug your external drive into the new laptop and run `bash install.sh --restore /path/to/backup.tar.gz.enc`.

If you've enabled the optional Google Drive secondary destination, your recovery flow is:

1. Install Hermes on the new laptop.
2. Clone this repo.
3. Run `bash install.sh` (NOT `--restore` yet).
4. When prompted for optional integrations, enable Google Workspace and complete a fresh OAuth flow. (No Solomon files needed for this.)
5. Now run `bash install.sh --restore <gdrive-link-or-path>`.
6. Provide the BIP-39 mnemonic.

## Health check after install

`solomon-setup` skill runs on first invocation:

- macOS: `launchctl list | grep io.solomon` should show 4 services (gateway + 3 workers).
- Linux: `systemctl --user list-units 'solomon-*'` should show 4 services.

Any missing service triggers a re-install of the unit and a Telegram alert.

## Re-running install.sh

Always safe. Use it to:

- Pull new code (`git pull && bash install.sh`).
- Add a newly-locked optional integration.
- Repair broken supervisor units after an OS upgrade.
- Re-symlink plugins after a Hermes upgrade.

Each step skips when already-done. Idempotency is the contract.
