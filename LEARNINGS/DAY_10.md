# Day 10 - Retrieval endpoint, and switching embeddings off OpenAI

## What was built

- Added `POST /documents/search`: embeds the query string with the
  existing `EmbeddingService` and queries `VectorStoreService` for the
  nearest chunks, returning them via new `SearchRequest`/`SearchResponse`
  schemas. Deliberately did not add a new `SearchService` - the
  endpoint composes two already-tested service methods with no logic
  of its own to justify a new class.
- Hit a real 500 uploading a PDF through Swagger UI - traced it to the
  OpenAI account having no billing/payment method configured
  (`insufficient_quota`, a 429). Confirmed a Claude Pro subscription
  can't substitute for this: Anthropic has no embeddings API at all,
  and Claude Pro/API access are entirely separate products.
- Decided to switch to a local model instead of fixing OpenAI billing.
  Rewrote `EmbeddingService` around a lazily-loaded
  `sentence-transformers` model (`all-MiniLM-L6-v2`, 384-dim),
  verifying its real behavior (shape, dtype, load time, `.tolist()`
  requirement) directly before touching production code.
- Hit a real disk-space failure mid-install (`OSError: No space left on
  device`, 289MB free). Investigated read-only first (`df -h`, `du -sh`
  on caches), found the pip cache alone was 3.7GB, got explicit
  scoped approval before clearing only that cache (not the other large
  caches found), then successfully retried the install.
- Removed `openai` and its orphaned transitive deps (`distro`, `jiter`)
  after confirming via `grep` that nothing in the codebase still
  referenced them. Rewrote `tests/fakes.py` (`FakeOpenAIClient` ->
  `fake_encoder`) and `tests/test_embedding_service.py` for the new
  interface. Full suite: 50 tests, all passing.
- Verified the entire pipeline end-to-end against the real running app
  for the first time ever in this project: started uvicorn, uploaded a
  real text file, confirmed it was embedded and stored in ChromaDB with
  no API key or network cost, and confirmed `/documents/search`
  correctly retrieved it. Cleaned up all manual test artifacts
  (`uploads/`, `chroma_db/`) afterward.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Add `POST /documents/search` as a thin router endpoint, no new service.
2. Switch embeddings from OpenAI to a local `sentence-transformers` model.

## What did NOT happen this session

- Citations (formatting search results into a human-readable reference)
  are still just raw offsets in the API response - not built yet.
- No real database yet - JSON sidecars are still the only persistence.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- The OpenAI billing blocker turned into a genuine architecture
  decision (switch to local embeddings) rather than just an annoyance
  to work around. Does that change how you think about depending on a
  paid external service for a portfolio project you want anyone to be
  able to run?
-
- The disk-space incident was handled by investigating read-only first
  and asking for explicit, scoped permission before deleting anything.
  Did that feel like the right amount of caution for a personal dev
  machine, or would you have just let the cache get cleared without
  being asked?
-
- This is the first time the full upload -> embed -> store -> search
  pipeline has actually run successfully end-to-end in this project.
  What's your honest read on retrieval quality with `all-MiniLM-L6-v2`
  now that you can actually test it, versus what you expected?
-
