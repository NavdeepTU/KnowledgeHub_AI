# Day 9 - Phase 3 kickoff: embeddings and vector storage

## What was built

- Explicitly decided Phase 3 scope before writing code: OpenAI
  `text-embedding-3-small` for embeddings, ChromaDB (local, embedded)
  for the vector store - discussed with real alternatives (local
  sentence-transformers, Cohere, FAISS, pgvector) rather than picked
  unilaterally, since it's the first milestone introducing a paid
  external dependency.
- Added `EmbeddingService`, with the real OpenAI client constructed
  *lazily* - verified directly that eager construction with no API key
  raises immediately, which would have broken app startup and test
  collection for anyone without a key configured.
- Added `VectorStoreService` wrapping a local `chromadb.PersistentClient`
  - no server process. Verified its upsert/get/query API directly
  before writing the wrapper.
- Wired both into the upload flow after chunking. Made embedding/
  vector-storage failures **hard failures** (500, file cleaned up),
  explicitly different from metadata's best-effort design - making a
  document searchable is the actual point of this step.
- Built a fake OpenAI client (`tests/fakes.py`) and isolated Chroma
  directories for tests, so the 40-test suite makes zero real network
  calls and costs nothing to run.
- Verified against the real app with a real (but quota-exceeded) OpenAI
  key: confirmed a clean 500 on failure, automatic file cleanup, and
  that the server itself didn't crash - a real, not theoretical, check
  of the failure path.
- Updated `.claude/commands/end-session.md` and `CLAUDE.md` so
  `/end-session` now commits automatically after updating docs (running
  it counts as the explicit commit request), rather than only
  recommending a commit message.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Choose OpenAI embeddings and ChromaDB for Phase 3.
2. Lazily construct the OpenAI client; treat embedding failures as hard
   failures, unlike metadata.

## What did NOT happen this session

- No retrieval/search endpoint yet - chunks are embedded and stored,
  but nothing queries the vector store back. That's the next task.
- The OpenAI account used for testing still has no billing configured -
  needs to be set up on platform.openai.com before real embedding calls
  will succeed.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- This is the first milestone that costs real money to run for real.
  Does the "explicit scoping decision before implementation" process
  feel like it gave you enough control over that, or would you want
  more say next time (e.g. setting a hard spending cap first)?
-
- The embedding/vector-storage failure path was verified against a
  real quota-exceeded account rather than just reasoned about - did
  that change your confidence in the design compared to earlier
  best-effort-vs-hard-failure decisions you only reasoned through?
-
- If an interviewer asked "why is embedding synchronous and blocking
  the upload request," is your honest answer "haven't needed
  background processing yet" or do you have a stronger justification?
-
