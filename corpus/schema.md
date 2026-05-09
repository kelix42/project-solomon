# Corpus Schema

Configuration for the corpus subsystem. The file is owner-editable. `solomon-corpus-ingest` reads it on every run.

## Routing extension map

The first-tier routing rule is **subfolder hint**: if the inbox path starts with `sops/`, `emails/`, `messages/`, `docs/`, or `data/`, that's the category. The second tier is this extension map; the third is an LLM classifier fallback for ambiguous text.

```yaml
routing:
  emails: [.eml, .mbox]
  data: [.csv, .tsv, .parquet, .json]
  messages: [.wav, .mp3, .m4a, .flac, .opus, .ogg]   # post-transcription
  docs: [.pdf, .docx, .doc, .pptx, .xlsx, .html, .heic, .png, .jpg]
  llm_classifier: [.txt, .md, .rtf]                   # ambiguous → LLM picks
```

## File limits

```yaml
limits:
  max_size_bytes: 104857600    # 100 MB
  oversized_path: corpus/inbox/_oversized/
  unsupported_path: corpus/inbox/_unsupported/
```

Oversized and unsupported files are surfaced to `solomon-audit` weekly and queued to `mentoring_queue` priority 7 by `solomon-corpus-lint`.

## Salience threshold

The decision pipeline (§2.2.5) Stage 2 uses this threshold to skip low-importance events:

```yaml
salience_min: 0.30
```

Events with salience < 0.30 land in `events.status = skipped` and exit the pipeline.

## Concurrency

```yaml
pipeline_max_in_flight: 5     # max parallel agent sessions per pipeline-tick worker run
```

## Redaction allowlist

Paths matching these globs bypass `solomon-redact` (e.g., owner's own SOPs that intentionally include test API keys):

```yaml
redaction_skip:
  - corpus/raw/sops/internal/**
  - corpus/raw/data/test-fixtures/**
```

## Entity allowlist

Named entities (PERSON, ORG, LOC, GPE) NOT redacted in the owner's own writing. Set during onboarding:

```yaml
entity_allowlist:
  - "Solar Roofing Inc."   # owner's own company name (example — replace)
  - "Alex Smith"           # owner's own name (example — replace)
```

## Transcription backend

```yaml
transcription:
  backend: whisper.cpp        # local default; alternative: openai_whisper_api
  model: base.en              # whisper.cpp model name
  fallback_to_plaud: true     # if plaud-ingest worker is enabled, reuse its transcription pipeline
```

## OCR backend

```yaml
ocr:
  backend: pytesseract        # local default; alternative: google_vision_api
  skip_if_pdf_text_layer: true
```

## Wiki page cleanup

```yaml
wiki_orphan_grace_days: 7     # how long an orphan can linger before lint surfaces it
stale_grace_days: 14          # how long a wiki page can lag behind newest related raw before lint flags it
```

## Vocabulary normalization (mirror of §2.11 in SOLOMON-PLAN.md)

```yaml
vocabulary_normalization:
  lowercase: true
  strip_punctuation: true
  collapse_whitespace: true
  strip_articles: [the, a, an]   # leading and trailing
  preserve_hyphens: true
  no_stemming: true
```
