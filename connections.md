# Connections

Solomon's external integrations. 13 rows. Pinecone, Telegram, Google Workspace are required; everything else is optional.

| # | Domain | Tool | Mechanism | Auth | Required | Last Checked |
|---|---|---|---|---|---|---|
| 1 | Vector memory | Pinecone (4 namespaces: `solomon-corpus-wiki`, `solomon-corpus-raw`, `solomon-captured-items`, `solomon-decision-log`) | `hermes-plugins/pinecone-bridge/` | `PINECONE_API_KEY` + `OPENAI_API_KEY` + `EMBEDDING_MODEL` + `EMBEDDING_DIM` + `PINECONE_INDEX_NAME` + `PINECONE_REGION` | **required** | — |
| 2 | Owner interface | Telegram | Hermes gateway adapter (built-in, configured via `hermes gateway setup`) | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | **required** | — |
| 3 | Email + Calendar + Docs/Drive/Sheets | Google Workspace | `hermes-plugins/google-workspace/` (Google MCP) | OAuth + `GOOGLE_MCP_SERVER_URL` | **required** | — |
| 4 | Workflow orchestrator | n8n or make.com | `hermes-plugins/workflow-bridge/` | `WORKFLOW_WEBHOOK_URL` + scenario IDs | optional | — |
| 5 | Voice capture | Plaud | `workers/plaud-ingest/` (IMAP IDLE + 60s poller) | `PLAUD_IMAP_HOST` + `PLAUD_IMAP_USER` + `PLAUD_IMAP_PASS` (Gmail: app-password required) + `PLAUD_SENDER` | optional | — |
| 6 | Owner state | Whoop | `hermes-plugins/whoop-bridge/` | OAuth (`WHOOP_CLIENT_ID` + `WHOOP_CLIENT_SECRET`) | optional | — |
| 7 | Decision store | SQLite | local file `db/solomon.db` (WAL mode) | none | **required (auto)** | — |
| 8 | Sub-agents (v2) | Hermes parallel reasoners via `delegate_task` | n/a | n/a | **deferred to v2 (see EXPANSIONS.md section 6)**; v1 runs all reasoning in the main Hermes agent. Distinct from Solomon's `workers/` (§2.4.6.5), which are real v1 components. | — |
| 9 | Host runtime | Hermes | `~/.hermes/` (gateway daemon supervised by launchd/systemd) | n/a | **required** | — |
| 10 | LLM | OpenRouter / Anthropic | Hermes-managed | OAuth or `OPENROUTER_API_KEY` | **required** | — |
| 11 | Cloud worker host (future) | Render / Railway | future expansion | n/a | optional | — |
| 12 | Corpus auto-ingest | File watcher (watchdog) | `workers/corpus-inbox-watcher/` (separate Python service, not a Hermes plugin) | none | optional (recommended; default ON) | — |
| 13 | Backup destination | Local path (default) or Google Drive folder (optional secondary) | sleep-cycle Job 10 (`corpus-backup`) | none for local; OAuth for Drive | optional (recommended) | — |

## Adding a custom integration

Copy `hermes-plugins/_template-hermes-plugin/` (for plugins that expose tools to skills) or `workers/_template-worker/` (for long-lived background services). Edit `plugin.yaml` / `worker.yaml`, implement `register(ctx)` or `__main__.py`, and append a row to this table. Pattern documented in `references/integrations-pattern.md`.
