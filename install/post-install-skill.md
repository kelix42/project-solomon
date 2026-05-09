# Post-Install Skill — `solomon-setup`

After `install.sh` finishes, the very first Hermes session runs `solomon-setup` automatically. This skill:

1. **Verifies all required connections** (Pinecone reachable, OpenAI key valid, Telegram bot token works, supervisor units running).
2. **Reads `db.proposed_rules`** — if any rows exist (from a corpus pre-load), surfaces them for confirmation.
3. **Routes the owner to the foundation interview**:
   - Either run `intake.md` (paste-once mode) — fast for a returning user with answers ready.
   - Or run the seven `solomon-onboarding-NN-*` skills sequentially (interactive ELIZA mode) — recommended for first-time setup.
4. **Logs the choice** to `decisions/log.md`.

Both modes write to the same target: `db.captured_items` rows → derived `foundation/NN-*.yaml` summaries.

## Manual invocation

`solomon-setup` is also callable any time as `/solomon-setup` to repair, re-onboard, or re-verify. It is NOT the install entry — `install.sh` is. `solomon-setup` assumes the install steps have already run.

## Troubleshooting

If a connection check fails:

- Pinecone unreachable → check `PINECONE_API_KEY` in `~/.hermes/.env`; check the index name + region.
- OpenAI rate-limit → wait, or set `OPENROUTER_API_KEY` for fallback per §2.4.7.
- Telegram bot token invalid → re-create via @BotFather; update `TELEGRAM_BOT_TOKEN` in `~/.hermes/.env`.
- Supervisor unit missing → re-run `bash install.sh`; `solomon-setup` re-installs the missing unit.
