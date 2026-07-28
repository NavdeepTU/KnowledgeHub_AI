# Day 3 - Persistence, roadmap scope, and new workflow commands

## What was built

- Persisted extracted text and metadata as a JSON sidecar file
  (`uploads/<document_id>.json`) via a new `DocumentRecord` schema and
  `DocumentService.persist_metadata`, kept deliberately separate from a
  database for now.
- 2 new tests: sidecar written correctly on success, no sidecar left
  behind on a failed upload (encrypted PDF).
- Broadened `docs/ROADMAP.md` Phase 2 to target DOCX, TXT/Markdown,
  PPTX, and HTML uploads (a scope decision, not yet implemented).
- Added two new workflow commands: `/next-task` (lightweight "what's
  next" recommendation, callable mid-session without the full
  `/start-session` ritual) and `/commit` (reviews the diff, runs tests,
  splits unrelated changes into separate commits, writes a why-focused
  message).
- Discussed (no code/roadmap change) whether the project should grow
  beyond plain RAG into a multi-capability enterprise app with a richer
  frontend - left genuinely undecided, revisit when ready to commit to
  a specific scope.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Persist extracted text as a JSON sidecar file rather than introducing
   a database now.

## What did NOT happen this session

- No frontend or multi-capability scope was decided - that conversation
  is still open.
- The TXT/Markdown format-dispatcher task (recommended twice now by
  `/next-task`) was not started.
- `docs/PROJECT_STATUS.md` had drifted out of sync with actual commits
  for a while before this `/end-session` pass caught it - worth noticing
  earlier next time.

## Reflection (fill in yourself)

- The docs drifted for two `/next-task` runs before getting fixed here -
  would you rather `/next-task` nag more insistently about stale docs,
  or is "flag once, mention again if still stale" the right level?
-
- If an interviewer asked "why didn't you just use SQLite from the
  start instead of JSON files," could you defend the JSON choice in one
  sentence without checking `docs/INTERVIEW_NOTES.md`?
-
- Was leaving the frontend/enterprise-scope question open the right
  call, or would picking a scope now (even a small one) have been more
  useful than continuing to defer it?
-
