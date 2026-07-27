# Day 1 - Automated tests for PDF ingestion

## What was built

- First automated test suite for the ingestion API: 8 tests covering the
  health check and every validation branch in `POST /documents/upload`
  (success, bad extension, bad MIME type, empty file, fake signature,
  corrupted PDF, encrypted PDF).
- Test PDFs (valid / encrypted / corrupted) generated at test time with
  `pypdf.PdfWriter` instead of committing binary fixture files.
- An autouse `monkeypatch` fixture redirects `settings.upload_directory`
  to `tmp_path` so tests never touch the real local `uploads/` folder.
- `pytest` and `httpx` added as dependencies.
- Found and fixed a real deprecation in existing code while running the
  new tests: `status.HTTP_422_UNPROCESSABLE_ENTITY` ->
  `HTTP_422_UNPROCESSABLE_CONTENT`.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Generate PDF fixtures at test time rather than committing binaries.
2. Redirect uploads to a temp directory during tests via `monkeypatch`.
3. Rename the deprecated `HTTP_422_UNPROCESSABLE_ENTITY` constant.

## Reflection (fill in yourself)

- What part of writing these tests took longer than expected, and why?
-
- Did generating PDFs with `pypdf.PdfWriter` feel like the right call, or
  would committing a couple of real fixture files have been simpler in
  hindsight?
-
- If asked in an interview "how did you test file upload validation
  without a real database or S3 bucket," what's your one-sentence answer?
-
- What would you do differently if this test suite had 10x more tests?
-
