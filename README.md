# Solomon — Personal Business Brain

A Hermes-native skill pack that learns its owner well enough to make routine business decisions on their behalf, escalating the rest.

## Install (one command)

```bash
git clone <owner>/solomon && cd solomon && bash install.sh
```

That's the only supported install command. **Do not** use `hermes skills install` against this repo — it skips the database setup, plugin symlinks, Pinecone index creation, and the BIP-39 backup-key flow. See `install/README.md` for details.

After install completes, you're dropped straight into Session 0 of the foundation interview.

## Recovery on a new laptop

```bash
git clone <owner>/solomon && cd solomon && bash install.sh --restore /path/to/backup.tar.gz.enc
```

You'll be prompted for the 24-word BIP-39 mnemonic you saved during the original install. See `install/bootstrap.md`.

## What's inside

- `SOUL.md`, `MEMORY.md`, `USER.md` — Hermes auto-loads these into the system prompt every turn.
- `foundation/` — 7 owner-derived YAMLs (industry, beliefs, why, principles, ideal outcomes, non-negotiables, taxonomy). Derived summaries; canonical store is `db/`.
- `corpus/` — bulk ingestion area. Drop SOPs, emails, transcripts, CSVs into `corpus/inbox/`; the `corpus-inbox-watcher` worker auto-processes within 30 seconds.
- `db/` — SQLite schemas (WAL mode). 17 tables; canonical structured store.
- `decisions/log.md` — append-only decision log.
- `hermes-plugins/` — Hermes plugins (verified-API: `register_tool`, `register_hook`, `register_command`).
- `workers/` — long-lived Python services supervised by launchd/systemd: `plaud-ingest`, `corpus-inbox-watcher`, `pipeline-tick`.
- `orchestrator/` — decision-phase pipeline (10 stages: Capture → … → Action) + 12 sleep-cycle jobs.
- `skills/` — 27 skills in 7 categories (Setup, Onboarding, Interview, Corpus, Runtime, Learning, Utilities).
- `references/` — 22 reference docs: frameworks, API guides, distilled runtime specs.
- `archives/` — original vision docs + ELIZA source + Karpathy LLM Wiki gist for attribution.

## How the world reaches Solomon

| Source | Path |
|---|---|
| Owner messages | Telegram → Hermes gateway adapter → `db.events` → pipeline-tick worker |
| Voice transcripts | Plaud → IMAP → `plaud-ingest` worker → `corpus/inbox/messages/` → corpus-inbox-watcher |
| SOPs / emails / docs | Drop into `corpus/inbox/<category>/` → corpus-inbox-watcher → `solomon-corpus-ingest` |
| Sleep-cycle jobs | Hermes gateway cron, daily at 3am owner-local time |

## Architecture pinned

See [`SOLOMON-PLAN.md`](../SOLOMON-PLAN.md) at the project root for the full v2 spec (1350 lines, every architectural decision pinned).

## Two phases — never co-mingled

- **Interview phase**: ELIZA-style probing, owner-rule extraction, mentoring. Loaded skills carry `phase: interview`.
- **Decision phase**: Real-time on-behalf actions, corpus maintenance, audit. Loaded skills carry `phase: decision`.
- **Utilities**: phase-agnostic (`phase: utility`); only `solomon-redact` in v1.

CI tests assert no skill loads under the wrong phase.

## License

MIT — see `LICENSE`.
