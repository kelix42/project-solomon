# OCR — image → text

Owner-configurable backend in `corpus/schema.md`:

```yaml
ocr:
  backend: pytesseract
  skip_if_pdf_text_layer: true
```

## pytesseract (default)

Local-only, privacy default. Owner installs Tesseract (`brew install tesseract` on macOS, `apt install tesseract-ocr` on Linux) plus the `pytesseract` Python package. `corpus-ingest` runs it on `.png / .jpg / .heic` and on PDFs that lack a text layer.

## Google Vision API (alternative)

Set `ocr.backend: google_vision_api`. Reuses the Google Workspace OAuth credentials (`hermes-plugins/google-workspace/`). Per-page pricing — see https://cloud.google.com/vision/pricing.

## PDF text layer

If a PDF already has an extractable text layer (most modern PDFs do), `corpus-ingest` skips OCR entirely and uses the embedded text. Saves cost and time.
