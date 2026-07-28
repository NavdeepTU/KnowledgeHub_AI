# Day 7 - Chunking

## What was built

- Added `ChunkingService` (`app/services/chunking_service.py`), a new
  peer service to `DocumentService` rather than a method on it, since
  chunking is a distinct responsibility that doesn't care what format
  the text came from.
- `chunk_text` splits text into overlapping, character-bounded chunks
  using a sliding window (`chunk_size_chars=1000`,
  `chunk_overlap_chars=200`, both configurable via `Settings` with
  `Field(gt=0)`/`Field(ge=0)` guards). Deliberately character-based, not
  token-based - no embedding model exists yet to make token counts
  meaningful, so no tokenizer dependency was added.
- New `DocumentChunk` schema (`chunk_index`, `text`, `start_offset`,
  `end_offset`, `character_count`) - offsets are free to compute during
  chunking and are meant for citations once retrieval exists.
- Wired into the upload flow after extraction, before persistence.
  `chunks` added to the JSON sidecar, `chunk_count` added to the API
  response.
- 5 direct unit tests on the chunking algorithm (empty text, short text,
  overlap math, full-coverage reconstruction with no gaps, and a guard
  against overlap >= chunk_size), plus 2 integration tests through the
  real upload flow verifying persisted chunks reconstruct the original
  text exactly. 28 tests total, all passing.
- Manually verified against the real running app with a 5000-character
  file: got exactly 6 chunks with the expected 800-character step and
  200-character overlap.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Chunk by character count, not tokens, in a dedicated ChunkingService.

## What did NOT happen this session

- Metadata extraction (the last unstarted Phase 2 item) was not started.
- Embeddings/retrieval (Phase 3) were not started - that's a bigger
  step needing a real model/provider decision first.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- The chunking algorithm was tested directly (unit tests on
  `ChunkingService`) rather than only through the HTTP endpoint, unlike
  most of the project's testing so far - did that feel like a
  worthwhile difference, or overkill for this size of logic?
-
- `start_offset`/`end_offset` were added "because they're free" even
  though nothing uses them yet - do you agree that's justified, or does
  it cross into building for a hypothetical future?
-
- If an interviewer asked "why 1000 characters and 200 overlap
  specifically," is your honest answer "reasonable-sounding defaults,"
  or do you have a stronger justification?
-
