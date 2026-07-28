# Day 8 - Metadata extraction: Phase 2 complete

## What was built

- Added `DocumentService.extract_metadata`, a new best-effort dispatch
  that pulls title, author, and creation date from PDF (`pypdf`'s
  `reader.metadata`) and DOCX/PPTX (`core_properties`). TXT, Markdown,
  and HTML have no metadata standard and simply get an empty
  `DocumentMetadata` - no entry in the dispatcher, by design.
- Made metadata extraction deliberately separate from `extract_text`
  (re-parses the file) rather than changing the existing, already-tested
  extractor methods' return signature - kept the change isolated.
- Made metadata extraction best-effort: failures degrade to empty
  metadata (logged, not silent) instead of failing the whole upload,
  since the file already parsed successfully once for its actual text.
  This is the one place in the codebase with a bare `except Exception`,
  and it's commented explaining why.
- Found a real library quirk while verifying: `python-docx`/
  `python-pptx`'s default templates carry a baked-in placeholder
  creation timestamp even when a document never sets one explicitly -
  documented rather than trusted blindly.
- Updated the PDF/DOCX/PPTX test fixtures to set explicit title/author
  so metadata tests have real values to check against.
- 4 new tests (PDF, DOCX, PPTX extraction, TXT's empty case) - 32 tests
  total, all passing. Manually verified against the real app with a
  DOCX carrying explicit title/author/creation date.
- This closes out every item on `docs/ROADMAP.md` Phase 2.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Extract metadata as a separate, best-effort pass rather than
   extending `extract_text`.

## What did NOT happen this session

- Phase 3 (embeddings, vector database, retrieval) was not started -
  it needs a model/provider decision first, flagged explicitly in
  `docs/PROJECT_STATUS.md` as the first milestone in this project that
  introduces an external dependency and likely cost.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- This is the first `except Exception` in the codebase - does the
  justification (supplementary data, already-logged, doesn't block a
  successful upload) hold up if you imagine defending it in a code
  review, not just in an interview?
- 
- Metadata gets parsed in a second pass, re-opening files already
  opened once for text extraction - at what point (file size? request
  volume?) would that inefficiency actually start to matter?
-
- Phase 3 is next and it's the first milestone needing a real external
  decision (embedding provider, cost, vector store). Do you already
  have a leaning, or is this genuinely open?
-
