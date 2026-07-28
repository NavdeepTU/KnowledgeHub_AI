# KnowledgeHub AI - Project Status

## Current milestone

Multi-format upload support, phase 1 (complete). PDF, TXT, and Markdown
are all supported through a shared dispatcher. Next milestone (DOCX)
proposed but not yet started - see below.

## Completed

- FastAPI project initialized
- Health endpoint available
- PDF upload endpoint available
- File extension validation
- MIME-type validation
- Empty-file validation
- Maximum-size validation
- PDF signature validation
- PDF text extraction
- Encrypted-PDF rejection
- Structured application logs
- Saved-file cleanup after processing failure
- Automated test suite (`tests/test_documents.py`) covering: health check,
  successful upload, invalid extension, invalid MIME type, empty file, fake
  PDF signature, corrupted PDF, and encrypted PDF
- Test fixtures generate PDFs in-memory via `pypdf` (no binary files in
  the repo); `pytest` + `httpx` added as dev dependencies
- Tests isolated from local dev state via an autouse fixture that redirects
  `settings.upload_directory` to a temp directory
- Renamed deprecated `status.HTTP_422_UNPROCESSABLE_ENTITY` to
  `HTTP_422_UNPROCESSABLE_CONTENT` in `app/api/documents.py`
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/INTERVIEW_NOTES.md` filled
  in (previously blank); `LEARNINGS/DAY_01.md` backfilled
- `end-session` workflow updated to keep `DECISIONS.md` and
  `INTERVIEW_NOTES.md` in sync going forward
- Repository connected to GitHub (`git@github.com:NavdeepTU/KnowledgeHub_AI.git`)
  over SSH; all prior commits pushed
- Added a project-scoped `Stop` hook (`.claude/hooks/auto_push.sh`) that
  pushes already-committed work to `origin` automatically after each turn;
  it never commits anything itself
- Extracted text and metadata are now persisted as a JSON sidecar file
  (`uploads/<document_id>.json`) via a new `DocumentRecord` schema and
  `DocumentService.persist_metadata`; covered by 2 new tests (sidecar
  written on success, no sidecar left behind on failure)
- `docs/ROADMAP.md` Phase 2 broadened to target DOCX, TXT/Markdown, PPTX,
  and HTML uploads
- Added `/next-task` (lightweight "what's next" recommendation, callable
  mid-session) and `/commit` (review-diff-then-commit workflow) commands
- `DocumentService.extract_text` refactored into a per-format dispatcher
  (extension -> validator + extractor); TXT and Markdown are now
  supported alongside PDF, with no new dependencies. `save_pdf` renamed
  to `save_document` and now preserves the real uploaded extension
  instead of hardcoding `.pdf`. 3 new tests (TXT success, Markdown
  success, non-UTF-8 rejection) - 13 tests total, all passing
- `CLAUDE.md` updated: terminal output should default to simple, plain
  language, going technical only when explicitly asked
- Added `/interview-question` and `/interview-question-recent` commands:
  generate a random (or most-recent-feature) interview question grounded
  in the actual project, with a concise (~100-150 word) technical answer

## Work in progress

None.

## Current limitations

- Uploaded files are read fully into memory
- Files are stored on the local filesystem
- PDF, TXT, and Markdown are supported; DOCX/PPTX/HTML are targeted in
  the roadmap but not yet built
- Text-format uploads have no signature check (none exist reliably for
  plain text) - a mislabeled binary file that happens to decode as UTF-8
  would be silently accepted
- Persisted as flat JSON files, not a queryable database - fine for one
  document at a time, but there's no way to search or list across
  documents yet
- No background processing
- No embeddings or retrieval
- `starlette.testclient` emits a deprecation warning about `httpx` in favor
  of an `httpx2` package in the currently installed Starlette version; not
  addressed yet, tests are unaffected

## Next likely milestone

Add DOCX support through the existing dispatcher: one new
`SUPPORTED_FORMATS` entry (content type, ZIP signature `PK\x03\x04`), one
new extractor using `python-docx` (a new dependency), and tests mirroring
the TXT/Markdown pattern. The dispatcher groundwork already exists, so
this should be a small, self-contained addition.
