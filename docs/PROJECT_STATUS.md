# KnowledgeHub AI - Project Status

## Current milestone

Phase 3 complete: chunks are embedded locally (`sentence-transformers`)
and stored in ChromaDB during upload, `POST /documents/search` reads
them back, and each result carries a human-readable citation. The full
pipeline - upload, extract, chunk, embed, store, retrieve, cite - has
been verified end-to-end against the real running app with no external
API dependency. Every item on `docs/ROADMAP.md` Phase 3 is done.

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
- Added DOCX support through the existing dispatcher: one new
  `SUPPORTED_FORMATS` entry (ZIP signature `PK\x03\x04`), one new
  extractor using `python-docx` (paragraph text only, tables not yet
  extracted). Required zero changes to the router - the dispatcher
  absorbed the new format entirely in `DocumentService`. 3 new tests
  (success, missing ZIP signature, corrupted DOCX) - 16 tests total,
  all passing
- Added PPTX support the same way: one new `SUPPORTED_FORMATS` entry
  (same ZIP signature as DOCX) and one new extractor using
  `python-pptx`. Unlike the other formats, `page_count` reflects the
  real slide count instead of being hardcoded to 1. A test caught a
  real bug: `python-pptx` raises its own `PackageNotFoundError` when
  reading from a file path, not `zipfile.BadZipFile`/`KeyError` as it
  does from `BytesIO` - fixed before merging. 3 new tests - 19 total
- Added HTML support with **no new dependency** - stdlib `html.parser`
  via a small `HTMLParser` subclass that collects visible text while
  skipping `<script>`/`<style>` content. HTML has no reliable magic
  bytes, so (like TXT/MD) there's no signature check and no "corrupted
  HTML" failure mode - any valid UTF-8 text produces some result. 3 new
  tests (success, script/style stripping verified via the sidecar,
  non-UTF-8 rejection) - 22 tests total, all passing
- This completes every format on `docs/ROADMAP.md`'s Phase 2 list
- Added chunking: `ChunkingService.chunk_text` splits extracted text
  into overlapping, character-bounded chunks (`chunk_size_chars=1000`,
  `chunk_overlap_chars=200`, both configurable via `Settings`).
  Character-based, not token-based - no tokenizer dependency added
  since there's no embedding model yet to make token counts meaningful.
  Chunks (with `start_offset`/`end_offset` for future citations) are
  persisted in the same JSON sidecar as a new `chunks` field, and
  `chunk_count` is now in the API response. 5 direct unit tests on the
  chunking algorithm plus 2 integration tests through the real upload
  flow - 28 tests total, all passing
- Added metadata extraction: `DocumentService.extract_metadata` pulls
  title, author, and creation date from PDF (`pypdf`'s `reader.metadata`)
  and DOCX/PPTX (`core_properties`); TXT/Markdown/HTML have no metadata
  standard and get an empty `DocumentMetadata` by design. Best-effort by
  design - a metadata-extraction failure degrades to empty metadata
  rather than failing the whole upload, since the file already parsed
  successfully once for text extraction. New `metadata` field on both
  the API response and the JSON sidecar. 4 new tests (PDF, DOCX, PPTX
  extraction, TXT's empty case) - 32 tests total, all passing
- This closes out every item on `docs/ROADMAP.md` Phase 2
- Decided Phase 3 scope explicitly: OpenAI (`text-embedding-3-small`)
  for embeddings, ChromaDB (local, embedded, no server) for the vector
  store
- Added `EmbeddingService` (OpenAI client, lazily constructed so a
  missing API key never breaks app startup or test collection - only
  the first real embedding call) and `VectorStoreService` (wraps a
  local `chromadb.PersistentClient`). Wired into the upload flow after
  chunking: embedding/storage failures are treated as real failures
  (500, cleaned up), not best-effort like metadata, since making a
  document searchable is the actual point of this step
- Tests use a fake OpenAI client and an isolated Chroma directory -
  the full suite makes zero real network calls and costs nothing to
  run. 8 new tests (embedding service, vector store service, 2
  integration tests through the real upload flow) - 40 tests total,
  all passing
- Verified the OpenAI-based pipeline against the real app with a real
  (but quota-exceeded) OpenAI key: confirmed a clean 500 on failure,
  automatic cleanup of the partial upload, and that the server itself
  didn't crash
- Added `POST /documents/search`: embeds the query string with
  `EmbeddingService` and returns the nearest chunks from
  `VectorStoreService`, via new `SearchRequest`/`SearchResponse`
  schemas. No new service - the router composes two already-tested
  service methods directly. 5 new tests (results returned, limit
  respected, empty store, empty query rejected, out-of-range limit
  rejected) - 45 tests total, all passing
- Switched `EmbeddingService` from OpenAI to a local
  `sentence-transformers` model (`all-MiniLM-L6-v2`, 384-dim), because
  the OpenAI account had no billing configured and every real embedding
  call failed with a 429. Removed `openai` and `openai_api_key`
  entirely; `EmbeddingService` now takes an optional `encoder` callable
  for test injection instead of a fake HTTP client. The project now
  runs fully offline with zero external API cost. 4 embedding-service
  tests rewritten for the new interface - 50 tests total, all passing
- Verified the new local pipeline end-to-end against the real running
  app: uploaded a real text file, confirmed embeddings were generated
  and stored in ChromaDB, and confirmed `/documents/search` correctly
  retrieved it - the first time this pipeline has actually succeeded
  end-to-end, since every prior OpenAI attempt was blocked by billing
- Added citations: `SearchResult` now has a `citation` field (e.g.
  `"notes.txt (chunk 0, characters 0-26)"`), formatted by a small
  `_format_citation` helper in `VectorStoreService` from data that was
  already being stored - no new service, no new dependency. 1 new unit
  test plus an existing search test extended to assert the format - 51
  tests total, all passing. This closes out every item on
  `docs/ROADMAP.md` Phase 3

## Work in progress

Nothing in progress - Phase 3 is fully complete and verified. See
"Next likely milestone" below.

## Current limitations

- Uploaded files are read fully into memory
- Files are stored on the local filesystem
- DOCX extraction only reads paragraph text - tables and embedded
  objects are not extracted
- Text-based formats (TXT, Markdown, HTML) have no signature check
  (none exist reliably for plain text) - a mislabeled binary file that
  happens to decode as UTF-8 would be silently accepted
- Persisted as flat JSON files, not a queryable database - fine for one
  document at a time, but there's no way to list across documents yet
  (search across their embedded content does work)
- No background processing
- Embeddings are generated synchronously during the upload request -
  adds latency (model load on first use, then fast) to every upload,
  no async/background queue
- DOCX/PPTX `created_at` may reflect the authoring tool's default
  template timestamp rather than a real authorship date, if the
  document never set one explicitly - a real quirk of those formats,
  not a bug in extraction
- `all-MiniLM-L6-v2` is a smaller, less accurate embedding model than
  OpenAI's `text-embedding-3-small` - retrieval quality is a step down
  in exchange for zero cost and no network dependency
- Citations are a formatted string only (filename, chunk index,
  character offsets) - there is no snippet highlighting or link back
  to view the source document
- `starlette.testclient` emits a deprecation warning about `httpx` in favor
  of an `httpx2` package in the currently installed Starlette version; not
  addressed yet, tests are unaffected

## Next likely milestone

Phase 3 (Retrieval) is done. The natural next milestone is Phase 4
(AI Chat): use an LLM to generate an actual answer from the chunks
`/documents/search` already returns, with citations attached - the
first real RAG loop, on top of retrieval infrastructure that's now
fully built and verified.
