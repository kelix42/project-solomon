# solomon-redact test fixtures

Each `<name>-input.txt` is the raw text fed to the redactor; the matching `<name>-expected.txt` is the expected output (where the pattern is deterministic).

For NER fixtures (`entity-*`), the expected output depends on whether spaCy is installed at test time. CI checks for the presence of `[REDACTED:entity]` tokens rather than exact-text equality.

## Running locally

```bash
pytest tests/test_redactor.py
```
