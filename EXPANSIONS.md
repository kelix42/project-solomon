# Expansions

Solomon v1 is intentionally small. This file documents the documented growth paths — when and how to add capabilities beyond v1.

## (1) Portability — non-Hermes paths

Solomon's file-by-file rebinding contract for porting to a different agent runtime (Claude Agent SDK, OpenAI agents, n8n native, etc.):

- **`SOUL.md` / `MEMORY.md` / `USER.md`** → equivalent system-prompt slots in the target. Markdown is the lingua franca.
- **`skills/` (markdown)** → translates to whatever skill format the target uses. The `agentskills.io` standard is portable; YAML front-matter survives.
- **`hermes-plugins/`** → the verified `register(ctx)` API surface (§2.4.6) is Hermes-specific. Equivalent ports use the target's plugin / tool registration API. The work is mechanical — `register_tool` → `add_tool`, etc.
- **`workers/`** → portable as-is. Plain Python services with launchd/systemd units. No agent runtime dependency beyond reading `db/solomon.db`.
- **`db/`** → SQLite is portable. Schema files are SQL standard.
- **Pinecone, OpenAI embeddings, Anthropic LLMs** → portable; provider credentials in `.env`.

The skills carry `portable: true` in front-matter; their bodies reference Hermes primitives only via `dispatch_tool`, not via `ctx.invoke_skill` (which doesn't exist anyway per §2.4.6).

## (2) Security — full BIP-39 backup-key flow + key rotation + redaction allowlist + encryption at rest

**Key flow** (per §2.10):
1. `install.sh` generates a 32-byte AES-256-GCM key.
2. Owner enters a passphrase → Argon2id derives a wrap key.
3. Wrapped key written to `~/.hermes/.env` as `SOLOMON_BACKUP_KEY_WRAPPED`.
4. Raw key shown ONCE as a 24-word BIP-39 mnemonic (24 words = 256 bits + 8-bit checksum; the only BIP-39 length that fully encodes AES-256).
5. Owner saves the mnemonic to a password manager AND on paper.

**Key rotation** (manual):
1. `/solomon-rotate-backup-key` — generates a new key, re-encrypts all backups in retention.
2. New 24-word mnemonic shown once.
3. Old key invalidated.

**Redaction allowlist** (`corpus/schema.md` `redaction_skip:`): paths matching these globs bypass `solomon-redact`. Use for owner-authored SOPs that intentionally include test API keys.

**Entity allowlist** (`corpus/schema.md` `entity_allowlist:`): the owner's own company name, the owner's own name, etc. — NOT redacted in the owner's own SOPs.

**Encryption at rest**: backup tarballs (Job 10) and `corpus/raw/_pre-redaction/<sha256>.bin` quarantined files use AES-256-GCM with the same backup key. SQLite database itself is **not** encrypted at rest in v1 (full-disk encryption on the host is the recommended layer); v2.1 may add SQLCipher.

## (3) Multi-device — three forward paths

v1 is single-device-only. `db/solomon.db` is not network-safe; the workers' file lock is local. Two laptops both running Solomon = undefined behavior.

Forward paths:

1. **Single-VPS (recommended interim)** — Run Solomon on a small cloud VPS. Both laptops connect as Telegram clients (the Hermes gateway adapter handles the routing). Drop files via Drive sync into the VPS's `corpus/inbox/`.
2. **Distributed SQLite** — Turso or LiteFS for distributed reads with one designated writer. Workers stay on the writer machine; laptops are read-only clients. Larger refactor.
3. **Cloud-native deployment** — Hermes gateway hosted on Render / Railway / Fly. Workers as sidecar containers. No laptop dependency. v2 scope.

`install.sh` warns if it detects a previous install with a recent `decisions/log.md` entry from a different machine ID.

## (4) Cloud-native deployment — deferred Hermes-cloud-deployment idea

Run Hermes gateway + workers in a managed cloud environment (Render web service, Railway, Fly.io, or similar). v1 stays on the owner's laptop because that's where Pinecone serverless billing, OAuth tokens, and the owner's data live by default. Cloud is a future expansion when the owner accepts shifting trust to a hosted environment.

## (5) What we considered and rejected

Design graveyard:

- **`hermes skills install` as the primary install path** — Rejected because it skips DB init, plugin symlinks, namespace creation, and the BIP-39 backup-key flow. `bash install.sh` is the only supported entry.
- **Embedding-based System 1 vs System 2 divergence check** — Rejected because per-event embedding cost is real on busy timelines. Replaced with token-Jaccard (§2.2.5 Stage 7b). Embedding-based may return in v2.1 if Jaccard proves too coarse.
- **In-process pubsub between Hermes plugins** — Rejected because Hermes' verified API has no `ctx.subscribe()` (§2.4.6 NOT-PROVIDED list). Replaced with SQLite-backed event queue (`db.events`) read by the `pipeline-tick` worker.
- **Vocabulary embedding into Pinecone** — Rejected because individual phrases have no semantic-search use case. Vocabulary stays SQL-only; queried by frequency/recency.
- **Programmatic skill invocation from plugins** — Rejected because Hermes skills are markdown documents the LLM reads, not Python-callable. Replaced with the two patterns in §2.4.6: (a) plugin registers a tool the skill teaches the LLM to use, or (b) write to `db.events` and let the pipeline-tick worker spawn a Hermes agent session.
- **Redis as the event bus / cache** — Rejected for v1 to keep the dependency surface small. SQLite WAL handles the load. v2.1 may swap if event volume justifies it.

## (6) Hermes sub-agents (v2) — distinct from Solomon's v1 workers

When Solomon needs parallel reasoners (cross-domain audit, deep research with branching paths, multi-customer analysis), spawn them via Hermes' `delegate_task` API. Each sub-agent gets a scoped skill subset and runs in parallel.

**v2 scope**, not v1. v1 runs all reasoning in the main Hermes agent. v2.1 audit should re-check whether any v1 skill became heavy enough to justify offloading.

**Distinct from v1 `workers/`** — Solomon's v1 workers are OS-supervised Python services for IMAP, file watching, and pipeline-tick. Hermes sub-agents are LLM-driven reasoners spawned from within Hermes via `delegate_task`. Both are valid; they solve different problems.

## Out of v1 scope

- Windows support (launchd is macOS, systemd is Linux). v2 may add Windows Service.
- Non-English owners (spaCy `en_core_web_sm` is English-only — also flagged in §2.10 of SOLOMON-PLAN.md).
- v1 `solomon-corpus-query` is read-only. Karpathy's "auto-file synthesized answers as new concept pages" pattern returns in v2.1 with a precise durability rule.
- Multi-chat Telegram allowlist (delegating to assistants). v2.1.
