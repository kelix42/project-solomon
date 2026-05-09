# Transcription — audio → text

Owner-configurable backend in `corpus/schema.md`:

```yaml
transcription:
  backend: whisper.cpp        # local default
  model: base.en
  fallback_to_plaud: true     # if plaud-ingest worker is enabled, reuse its pipeline
```

## whisper.cpp (default)

Local-only, privacy default. Owner installs `whisper.cpp` (`brew install whisper-cpp` on macOS). `corpus-ingest` shells out to the binary for `.wav / .mp3 / .m4a / .flac / .opus / .ogg` files.

## OpenAI Whisper API (alternative)

Set `transcription.backend: openai_whisper_api` and `OPENAI_API_KEY`. `corpus-ingest` POSTs to `https://api.openai.com/v1/audio/transcriptions`. Per-minute pricing — see https://openai.com/api/pricing.

## Plaud reuse

If `workers/plaud-ingest/` is installed, audio that arrives via Plaud is already transcribed before it lands in `corpus/inbox/messages/` (Plaud's AutoFlow does the transcription). `corpus-ingest` skips the transcription step for those files.

## Non-English

`whisper.cpp` supports many models; the default `base.en` is English-only. For other languages, set `transcription.model: base` (multilingual). spaCy POS tagging in `solomon-vocabulary-capture` is still English-only — flagged in `EXPANSIONS.md`.
