# KnowledgeHub AI - Project Status

## Current milestone

Automated tests for the PDF ingestion API.

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

## Current limitations

- Uploaded files are read fully into memory
- Files are stored on the local filesystem
- Only PDF files are supported
- Extracted text is not persisted
- No database
- No background processing
- No embeddings or retrieval
- `starlette.testclient` emits a deprecation warning about `httpx` in favor
  of an `httpx2` package in the currently installed Starlette version; not
  addressed yet, tests are unaffected

## Next likely milestone

Persist extracted text (e.g. to a database or structured file) instead of
discarding it after the upload response is returned. This is the natural
next step toward chunking and embeddings in Phase 2/3 of the roadmap.
