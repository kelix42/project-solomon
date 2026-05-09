"""Solomon — solomon-redact tests against fixtures.

Each fixture pair `<name>-input.txt` / `<name>-expected.txt` is checked.
Entity NER fixtures depend on whether spaCy is installed; we check structure not text.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "utilities" / "solomon-redact"))

from redactor import detect_entities, redact_text  # noqa: E402

FIXTURES = ROOT / "skills" / "utilities" / "solomon-redact" / "fixtures"


@pytest.mark.parametrize("name", ["ssn", "cc", "aws-key"])
def test_deterministic_fixtures(name):
    inp = (FIXTURES / f"{name}-input.txt").read_text()
    expected = (FIXTURES / f"{name}-expected.txt").read_text()
    out, _ = redact_text(inp)
    assert out == expected, f"fixture {name} mismatch\n--- got:\n{out}\n--- expected:\n{expected}"


def test_api_key_redacts_value_only():
    inp = (FIXTURES / "api-key-input.txt").read_text()
    out, redactions = redact_text(inp)
    assert "[REDACTED:api_key]" in out
    assert "sk-proj" not in out
    # The label "api_key=" should remain
    assert "api_key=" in out


def test_ssh_pem_marker():
    inp = (FIXTURES / "ssh-key-input.txt").read_text()
    out, _ = redact_text(inp)
    assert "[REDACTED:ssh_key]" in out


def test_password_labeled():
    inp = (FIXTURES / "password-input.txt").read_text()
    out, _ = redact_text(inp)
    assert "[REDACTED:password]" in out
    assert "hunter2" not in out


def test_entity_ner_or_skip():
    """If spaCy is installed, entity redaction works; otherwise the test skips."""
    try:
        import spacy
        spacy.load("en_core_web_sm")
    except Exception:
        pytest.skip("spaCy en_core_web_sm not installed")

    inp = (FIXTURES / "entity-input.txt").read_text()
    redactions = detect_entities(inp)
    # Should redact at least PERSON or ORG
    assert any(r.kind == "entity" for r in redactions)
