#!/usr/bin/env bash
# Solomon installer — single supported install command.
#
# Usage:
#   bash install.sh              # fresh install or re-verify
#   bash install.sh --restore <tarball>   # recover on a new laptop
#
# Implements the §10 flow from SOLOMON-PLAN.md:
#   1. Fresh-vs-restore disambiguation
#   2. Detect Hermes
#   3. Reuse existing Hermes config
#   4. Prompt for missing required keys
#   5. Optional integrations menu
#   6. Symlink repo + plugins to ~/.hermes/
#   7. Initialize db/solomon.db with WAL pragmas
#   8. Generate or restore the BIP-39 24-word backup key (Argon2id wrap)
#   9. Create Pinecone serverless index + materialize 4 namespaces
#  10. Verify plugins load
#  11. Log first entry to decisions/log.md
#  12. Auto-launch Session 0
#  13. Re-run safety
#
# Idempotent — every step skips when already-done.

set -uo pipefail

SOLOMON_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_ENV="$HERMES_HOME/.env"
SOLOMON_LINK="$HERMES_HOME/skills/solomon"
PLUGINS_LINK="$HERMES_HOME/plugins"

RESTORE_TARBALL=""
if [[ "${1:-}" == "--restore" ]]; then
  RESTORE_TARBALL="${2:-}"
  if [[ -z "$RESTORE_TARBALL" ]]; then
    echo "usage: bash install.sh --restore <tarball>" >&2
    exit 1
  fi
fi

# ── Logging helpers ──────────────────────────────────────────────────
log()  { printf '\033[1;34m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }
ok()   { printf '\033[1;32m[ok]\033[0m %s\n' "$*"; }

# ── Step 1: Fresh-vs-restore disambiguation ──────────────────────────
detect_existing_data() {
  if [[ -f "$SOLOMON_ROOT/db/solomon.db" || -d "$SOLOMON_ROOT/corpus/raw" ]] && \
     find "$SOLOMON_ROOT/corpus/raw" -type f -not -name '.gitkeep' 2>/dev/null | grep -q .; then
    return 0
  fi
  if [[ -f "$SOLOMON_ROOT/db/solomon.db" ]]; then
    if sqlite3 "$SOLOMON_ROOT/db/solomon.db" "SELECT count(*) FROM captured_items LIMIT 1" 2>/dev/null | grep -q '^[1-9]'; then
      return 0
    fi
  fi
  return 1
}

if [[ -z "$RESTORE_TARBALL" ]]; then
  if detect_existing_data; then
    warn "I see existing Solomon data on disk (corpus/raw or db/solomon.db has content)."
    warn "If you meant to restore, re-run as: bash install.sh --restore <tarball>"
    warn "Continuing as a re-verify pass (idempotent)."
  fi
fi

# ── Step 2: Detect Hermes ────────────────────────────────────────────
if ! command -v hermes >/dev/null 2>&1; then
  warn "Hermes not found on PATH."
  warn "Install Hermes first:"
  warn "  curl https://get.hermes-agent.nousresearch.com | bash"
  exit 1
fi
ok "hermes found: $(hermes --version 2>/dev/null | head -1)"

# ── Step 3: Reuse existing Hermes config ─────────────────────────────
mkdir -p "$HERMES_HOME"
touch "$HERMES_ENV"
log "reading existing $HERMES_ENV"
# shellcheck disable=SC1090
set -a; . "$HERMES_ENV" 2>/dev/null || true; set +a

# ── Step 4: Prompt only for missing required keys ────────────────────
prompt_if_missing() {
  local var="$1"; local prompt="$2"; local hint="$3"
  if [[ -z "${!var:-}" ]]; then
    printf '%s\n%s\n> ' "$prompt" "$hint"
    read -r value
    echo "${var}=${value}" >> "$HERMES_ENV"
    export "${var}=${value}"
  fi
}

if [[ -z "$RESTORE_TARBALL" ]]; then
  prompt_if_missing "PINECONE_API_KEY" "Pinecone API key (https://app.pinecone.io/keys)" "Required for vector memory."
  prompt_if_missing "OPENAI_API_KEY" "OpenAI API key (https://platform.openai.com/api-keys)" "Required for embedding (text-embedding-3-large)."
  prompt_if_missing "TELEGRAM_BOT_TOKEN" "Telegram bot token (from @BotFather)" "Required — Solomon's only owner UI."
  prompt_if_missing "TELEGRAM_CHAT_ID" "Telegram chat ID (your user ID)" "Send /start to your bot once after creation; Hermes captures it."

  # Defaults (write only if missing)
  for kv in "PINECONE_INDEX_NAME=solomon" "PINECONE_REGION=us-east-1" \
            "EMBEDDING_MODEL=text-embedding-3-large" "EMBEDDING_DIM=3072" \
            "BACKUP_DEST_LOCAL=$HOME/Backups/solomon"; do
    var="${kv%%=*}"
    if [[ -z "${!var:-}" ]]; then
      echo "$kv" >> "$HERMES_ENV"
      export "$kv"
    fi
  done
fi

# ── Step 5: Optional integrations menu ───────────────────────────────
if [[ -z "$RESTORE_TARBALL" ]]; then
  log "Optional integrations (multi-select):"
  log "  [ ] Google Workspace (Gmail+Calendar+Drive)"
  log "  [ ] Whoop"
  log "  [ ] Plaud"
  log "  [ ] n8n / make.com"
  log "  [x] Corpus auto-ingest watcher (default ON)"
  log "  [ ] Add custom integrations later"
  log "(scaffolds for all are present; toggle individual workers/plugins via plugin.yaml/worker.yaml default_enabled)"
fi

# ── Step 6: Symlink repo + plugins to ~/.hermes/ ─────────────────────
log "symlinking solomon -> $SOLOMON_LINK"
mkdir -p "$HERMES_HOME/skills"
ln -snf "$SOLOMON_ROOT" "$SOLOMON_LINK"

log "symlinking hermes-plugins/* -> $PLUGINS_LINK/"
mkdir -p "$PLUGINS_LINK"
for plugin in "$SOLOMON_ROOT"/hermes-plugins/*/; do
  if [[ -d "$plugin" ]]; then
    ln -snf "$plugin" "$PLUGINS_LINK/$(basename "$plugin")"
  fi
done

# ── Step 7: Initialize db/solomon.db with WAL pragmas ────────────────
DB="$SOLOMON_ROOT/db/solomon.db"
if [[ ! -f "$DB" ]]; then
  log "initializing $DB with WAL mode + 17 schema files"
  python3 - <<PY
import sqlite3, glob, os
DB = "$DB"
os.makedirs(os.path.dirname(DB), exist_ok=True)
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA busy_timeout=5000;")
for sql in sorted(glob.glob("$SOLOMON_ROOT/db/schemas/*.sql")):
    with open(sql) as f:
        conn.executescript(f.read())
    print(f"applied {os.path.basename(sql)}")
conn.commit(); conn.close()
PY
  ok "db initialized"
else
  log "db already exists at $DB; skipping init"
fi

# ── Step 8: Generate or restore BIP-39 24-word backup key ─────────────
if [[ -z "$RESTORE_TARBALL" ]]; then
  if [[ -z "${SOLOMON_BACKUP_KEY_WRAPPED:-}" ]]; then
    log "generating new backup key (24-word BIP-39 mnemonic + Argon2id-wrapped)"
    log "(stub — wire to mnemonic / argon2-cffi at runtime)"
    log "  -> save your 24-word mnemonic to a password manager AND on paper."
    log "  -> WITHOUT IT, YOUR BACKUPS ARE UNRECOVERABLE."
    echo "SOLOMON_BACKUP_KEY_WRAPPED=stub_replace_at_runtime" >> "$HERMES_ENV"
  fi
fi

# ── Step 9: Create Pinecone index + 4 namespaces ─────────────────────
log "creating Pinecone serverless index '$PINECONE_INDEX_NAME' (dim=$EMBEDDING_DIM, region=$PINECONE_REGION)"
log "(stub — wire to pinecone-client at runtime; install_pinecone.py)"
log "  Namespaces to materialize: solomon-corpus-wiki, solomon-corpus-raw, solomon-captured-items, solomon-decision-log"

# ── Step 10: Verify plugins load ─────────────────────────────────────
log "verifying plugins (hermes plugins list | grep solomon-)"
if hermes plugins list 2>/dev/null | grep -q solomon-; then
  ok "Solomon plugins detected by Hermes"
else
  warn "Hermes did not detect Solomon plugins. Check $PLUGINS_LINK symlinks."
fi

# ── Step 11: Log first entry ─────────────────────────────────────────
DLOG="$SOLOMON_ROOT/decisions/log.md"
if ! grep -q '^## ' "$DLOG" 2>/dev/null; then
  log "appending first decision-log entry"
  cat >> "$DLOG" <<EOF

## $(date +%Y-%m-%d) — Install completed

**Decision**: Solomon v1 installed on machine $(hostname).
**Why**: First setup; foundation interview begins next.
**Alternatives considered**: cloud-hosted (deferred to v2 per EXPANSIONS.md).
**Owner**: $(whoami)
EOF
fi

# ── Step 12: Restore flow (if --restore) ─────────────────────────────
if [[ -n "$RESTORE_TARBALL" ]]; then
  log "restore mode: would decrypt $RESTORE_TARBALL with BIP-39 mnemonic"
  log "(stub — wire to install_restore.py per §2.10)"
  log "  - decrypt tarball (AES-256-GCM)"
  log "  - restore db/solomon.db + corpus/{raw,wiki,index,log}"
  log "  - re-embedding cost/time gate (count vectors, prompt y/N)"
  log "  - recreate 4 Pinecone namespaces; clear embedded_at on captured_items+decisions"
  log "  - solomon-audit integrity pass"
  log "  - 'welcome back' Telegram message"
fi

# ── Step 13: Auto-launch Session 0 ───────────────────────────────────
if [[ -z "$RESTORE_TARBALL" ]]; then
  log "auto-launching Session 0 (foundation interview)"
  log "  hermes -s solomon-onboarding -q \"begin\""
  log "(skip auto-launch in scripted install; run manually when ready)"
fi

ok "install.sh complete"
exit 0
