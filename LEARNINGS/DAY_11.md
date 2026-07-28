# Day 11 - Citations close out Phase 3

## What was built

- Diagnosed a real `ModuleNotFoundError: No module named 'docx'` the
  developer hit running `uvicorn app.main:app --reload` directly - not
  a code bug, but Anaconda's `(base)` environment auto-activating and
  shadowing the project's `.venv`. Confirmed the fix by checking
  `which python` and importing `docx` inside the activated `.venv`.
- Added citations: `SearchResult` now has a `citation` field (e.g.
  `"notes.txt (chunk 0, characters 0-26)"`), formatted by a small
  `_format_citation` helper in `VectorStoreService.query_similar_chunks`
  from data that was already being stored (filename, chunk index,
  offsets) - no new service, no new dependency.
- Considered a Pydantic `@computed_field` on the schema instead of a
  service-level helper, and rejected it to keep `schemas/` holding only
  data contracts, consistent with how every other derived value in this
  project (chunk offsets, extracted metadata) is computed in
  `services/`, not by the schema itself.
- Verified against the real running app: uploaded a document, searched
  it, confirmed the `citation` field renders correctly in the live API
  response, then cleaned up test artifacts.
- 1 new unit test plus an existing search test extended to assert the
  citation format - 51 tests total, all passing.
- This closes out every item on `docs/ROADMAP.md` Phase 3 (Embeddings,
  Vector database, Similarity search, Citations).

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Format citations as a plain string field in `VectorStoreService`,
   not a schema computed field.

## What did NOT happen this session

- No RAG/LLM answer generation yet - citations are returned as raw
  formatted strings, nothing uses them to produce an actual answer.
- No real database yet - JSON sidecars are still the only persistence.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- Phase 3 (Retrieval) is now fully done, several sessions after it
  started. Looking back, does the incremental pace (embeddings, then
  search, then a billing blocker forcing a local-model switch, then
  citations) feel like it built real understanding at each step, or
  would you have wanted to move faster through the more mechanical
  parts (like citations)?
-
- The citation format is a plain f-string with character offsets, not
  page numbers or snippet highlighting. If an interviewer pushed on
  "how would a real product surface this to a user," what's your honest
  answer right now?
-
- This is the first session that started with a real environment bug
  (Anaconda `base` shadowing `.venv`) rather than an application bug.
  Did diagnosing it (checking `which python` first) change how you'd
  debug a similar "works for me but not for you" report in the future?
-
