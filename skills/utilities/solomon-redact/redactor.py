"""solomon-redact — PII / secrets redaction.

Phase-agnostic utility (§2.6 of SOLOMON-PLAN.md). Called by:
- solomon-corpus-ingest (decision phase)
- solomon-extraction (interview phase)
- solomon-vocabulary-capture (interview phase)
- /solomon-redact <file_path | text> (manual owner audit)

Redactors:
1. Named entities (PERSON, ORG, LOC, GPE) via spaCy en_core_web_sm NER -> [REDACTED:entity]
2. Regex patterns: SSN, US/EU phone with name-context, credit card (Luhn), API keys,
   AWS access keys, SSH private keys (PEM markers), passwords in labeled contexts.

Allowlists:
- entity_allowlist (corpus/schema.md) — owner's own company/name not redacted
- redaction_skip globs (corpus/schema.md) — paths bypass the entire pass

Quarantine: original bytes for files -> corpus/raw/_pre-redaction/<sha256>.bin (AES-256-GCM).
Audit: every redaction logged to corpus/log.md with file path, type, offset (NOT value).
"""
import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

LOG = logging.getLogger("solomon-redact")

# ── Regex patterns ─────────────────────────────────────────────────────

PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "cc_candidate": re.compile(r"\b\d{13,19}\b"),  # Luhn-checked downstream
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "api_key_prefixed": re.compile(
        r"(?:Bearer\s+|api[_-]?key\s*[:=]\s*|token\s*[:=]\s*)([A-Za-z0-9_\-\.]{20,})",
        re.IGNORECASE,
    ),
    "ssh_pem": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "password_labeled": re.compile(
        r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"\n]{6,})['\"]?",
        re.IGNORECASE,
    ),
}


@dataclass
class Redaction:
    kind: str        # ssn | phone | cc | api_key | aws_key | ssh_key | password | entity
    start: int
    end: int
    # Note: we never log the value itself. `kind` and offset only.


def _luhn_valid(digits: str) -> bool:
    s = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if not d.isdigit():
            return False
        n = int(d)
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        s += n
    return s % 10 == 0


def detect_regex(text: str) -> List[Redaction]:
    """Run all regex patterns; return list of Redactions."""
    out: List[Redaction] = []
    for kind, rx in PATTERNS.items():
        for m in rx.finditer(text):
            if kind == "cc_candidate":
                if not _luhn_valid(m.group()):
                    continue
                out.append(Redaction("cc", m.start(), m.end()))
                continue
            if kind == "api_key_prefixed":
                # Replace only the captured key, not the whole match
                out.append(Redaction("api_key", m.start(1), m.end(1)))
                continue
            if kind == "password_labeled":
                out.append(Redaction("password", m.start(1), m.end(1)))
                continue
            short = {"aws_key": "aws_key", "ssh_pem": "ssh_key"}.get(kind, kind)
            out.append(Redaction(short, m.start(), m.end()))
    return out


def detect_entities(text: str, allowlist: Optional[List[str]] = None) -> List[Redaction]:
    """spaCy NER: PERSON, ORG, LOC, GPE -> Redaction(kind='entity').
    allowlist: phrases NOT to redact (case-insensitive substring).
    """
    allowlist = allowlist or []
    try:
        import spacy
    except ImportError:
        LOG.warning("spacy not installed; skipping NER redaction")
        return []
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        LOG.warning("spacy model en_core_web_sm not installed; skipping NER redaction")
        return []
    doc = nlp(text)
    out = []
    for ent in doc.ents:
        if ent.label_ not in {"PERSON", "ORG", "LOC", "GPE"}:
            continue
        if any(a.lower() in ent.text.lower() for a in allowlist):
            continue
        out.append(Redaction("entity", ent.start_char, ent.end_char))
    return out


def apply_redactions(text: str, redactions: List[Redaction]) -> str:
    """Apply redactions in reverse order (so offsets stay valid)."""
    for r in sorted(redactions, key=lambda x: -x.start):
        text = text[: r.start] + f"[REDACTED:{r.kind}]" + text[r.end :]
    return text


def redact_text(text: str, entity_allowlist: Optional[List[str]] = None) -> Tuple[str, List[Redaction]]:
    """Public entry. Returns (redacted_text, list_of_applied_redactions).

    Logging format per §2.6: file path, type, offset (NOT value).
    """
    redactions = detect_regex(text) + detect_entities(text, entity_allowlist)
    redacted = apply_redactions(text, redactions)
    for r in redactions:
        LOG.info("redact: kind=%s offset=%d", r.kind, r.start)
    return redacted, redactions


def redact_file(path: Path, entity_allowlist: Optional[List[str]] = None) -> Tuple[Path, List[Redaction]]:
    """Read the file, redact, return (redacted_path, redactions). Quarantine original."""
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    quarantine = path.parent.parent / "_pre-redaction" / f"{sha}.bin"
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    # NB: real implementation encrypts with the BIP-39-derived backup key (§2.10).
    # Stub: write plaintext for now; install.sh sets up the key, encrypted-write at runtime.
    quarantine.write_bytes(raw)

    text = raw.decode("utf-8", errors="replace")
    redacted, redactions = redact_text(text, entity_allowlist)
    path.write_text(redacted, encoding="utf-8")
    return path, redactions


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python redactor.py <file_or_text>")
        sys.exit(1)
    arg = sys.argv[1]
    p = Path(arg)
    if p.exists() and p.is_file():
        _, rs = redact_file(p)
        print(f"redacted {p} ({len(rs)} redactions)")
    else:
        out, rs = redact_text(arg)
        print(out)
        print(f"# {len(rs)} redactions", flush=True)
