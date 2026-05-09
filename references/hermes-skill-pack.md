# Hermes Skill Pack — how Solomon binds to Hermes

Solomon is a Hermes skill pack + 3 workers. Hermes provides the agent runtime, the gateway daemon, the cron scheduler, and the Telegram adapter. Solomon provides the skills, plugins, workers, SQL schemas, foundation YAMLs, and orchestrator pipeline.

## Verified Hermes API surface

`ctx.register_tool(name, schema, handler, toolset=None, check_fn=None)`
`ctx.register_command(name, handler, description="")`
`ctx.register_cli_command(name, help, setup_fn, handler_fn)`
`ctx.register_skill(name, path)`
`ctx.register_hook(hook_name, callback)`
`ctx.dispatch_tool(name, arguments)`
`ctx.inject_message(content, role="user")`

## NOT provided (Solomon implements these itself)

- ❌ `ctx.subscribe()` / pubsub — Hermes has no pubsub bus
- ❌ `ctx.schedule()` — cron is gateway-level, registered via Hermes' built-in `/cron add`
- ❌ `ctx.db()` — plugins/workers open their own SQLite (with WAL pragmas)
- ❌ `ctx.pinecone()` / `ctx.telegram()` / `ctx.env()` / `ctx.logger()` — plugins import the Python SDK directly
- ❌ `ctx.invoke_skill()` — skills are markdown documents, not Python-callable. Use `dispatch_tool` to a tool the skill teaches the LLM to call.
- ❌ `ctx.lock()` / `ctx.on_unload()` — plugins are stateless event handlers; long-lived state lives in workers

## Hooks

Plugin hooks (fire within a single agent invocation): `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`, `on_session_finalize`, `on_session_reset`, `subagent_stop`, `pre_gateway_dispatch`.

## Install

`bash install.sh` is the only supported entry. `hermes skills install` is NOT supported (skips DB init). See `install/README.md`.

## Auto-loaded files

Hermes auto-loads `SOUL.md`, `MEMORY.md`, `USER.md` into the system prompt every turn. Solomon writes to these via skills.
