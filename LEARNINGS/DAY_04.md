# Day 4 - Multi-format uploads and interview-prep commands

## What was built

- Refactored `DocumentService` from PDF-only into a per-format
  dispatcher: a `SUPPORTED_FORMATS` registry (extension, allowed MIME
  types, optional signature) backs both the router's validation and the
  service's extraction, replacing hardcoded `.pdf` checks in three
  places.
- Added TXT and Markdown support through that dispatcher - no new
  dependencies, since both just decode bytes as UTF-8.
- Fixed a latent bug found during the refactor: the file-saving method
  always wrote `.pdf` as the saved extension regardless of what was
  actually uploaded. Renamed `save_pdf` to `save_document` and made the
  extension explicit.
- 3 new tests (TXT success, Markdown success, non-UTF-8 rejection); 2
  existing tests updated because their premise broke (`.txt` is no
  longer an invalid extension; PDF error message casing changed).
  13 tests total, all passing.
- Added a project-level communication rule to `CLAUDE.md`: terminal
  output defaults to simple, plain language; technical depth only on
  request.
- Added `/interview-question` and `/interview-question-recent`:
  generate a random (or most-recent-feature) interview question grounded
  in the real project, with a concise (~100-150 word) spoken-style
  technical answer. Iterated once already - first version's answers
  were too long, tightened to an actual spoken-length format.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Use a format registry + dispatcher instead of if/elif for
   multi-format uploads.

## What did NOT happen this session

- DOCX support (the next roadmap item) was not started - the dispatcher
  groundwork is now in place for it, but the actual implementation is
  still pending.
- The frontend/enterprise-scope conversation from earlier remains
  undecided.

## Reflection (fill in yourself)

- The first draft of `/interview-question`'s answers were noticeably
  too long for a real spoken interview answer - was that predictable
  from how the command was originally worded, or only obvious once you
  saw it in practice?
-
- If asked "why does `.txt` get no signature check when `.pdf` does,"
  could you give the one-sentence version without checking
  `docs/INTERVIEW_NOTES.md`?
-
- Given DOCX is next and now genuinely small in scope (per today's
  `/next-task` recommendation), does that match your own sense of how
  much work is actually left for it?
-
