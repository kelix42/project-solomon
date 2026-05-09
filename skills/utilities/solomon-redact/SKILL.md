---
name: solomon-redact
category: utility
phase: utility
version: 0.1.0
agent: hermes
trigger: ["/solomon-redact"]
inputs: [file_path | text]
outputs: [redacted text/file, quarantined original at corpus/raw/_pre-redaction/<sha256>.bin, corpus/log.md audit line]
reads_only: false
autonomy_level: L0
depends_on: []
portable: true
---

# solomon-redact

Phase-agnostic utility. Callable from interview-phase skills (`solomon-extraction`, `solomon-vocabulary-capture`) AND decision-phase skills (`solomon-corpus-ingest`). Also callable manually as `/solomon-redact <file_path | text>` for owner-initiated audits.

## Pattern detection

1. **Named entities** (PERSON, ORG, LOC, GPE) — spaCy `en_core_web_sm` NER. Tokenized as `[REDACTED:entity]`. spaCy is already a `solomon-vocabulary-capture` dependency, no new install.
2. **Regex-based PII**:
   - SSN
   - US/EU phone with name-context
   - Credit card (Luhn check)
   - API keys (high-entropy 20+ char strings prefixed by `key=`, `token=`, `Bearer `)
   - AWS access keys (`AKIA...`)
   - SSH private keys (PEM markers)
   - Passwords in obvious labeled contexts

## Replacement

In-place tokens: `[REDACTED:ssn]`, `[REDACTED:cc]`, `[REDACTED:key]`, `[REDACTED:phone]`, `[REDACTED:entity]`. Both the raw stored copy and any embedded text are redacted.

## Quarantine

Original bytes (for files) → `corpus/raw/_pre-redaction/<sha256>.bin`, AES-256-GCM with the backup key from §2.10.

## Allowlists

- `corpus/schema.md` `redaction_skip:` — paths matching these globs bypass redaction.
- `corpus/schema.md` `entity_allowlist:` — named entities NOT redacted (owner's own company, owner's own name).

## Audit

Every redaction logged to `corpus/log.md` with file path, type, and offset (NOT the value).

## Test fixtures

`skills/utilities/solomon-redact/fixtures/` — known-PII test files. CI verifies the skill against them on every release.

## Phase enforcement

`phase: utility` — callable from any session phase. Utilities never load other utilities (CI test asserts).
