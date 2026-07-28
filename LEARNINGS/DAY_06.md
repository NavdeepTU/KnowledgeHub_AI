# Day 6 - PPTX and HTML support: format roadmap complete

## What was built

- Added PPTX support through the existing dispatcher: one new
  `SUPPORTED_FORMATS` entry (same ZIP signature as DOCX) and one new
  extractor using `python-pptx`. Unlike every other format, PPTX's
  `page_count` reflects the real slide count instead of being hardcoded
  to 1, since slides are a genuine pagination concept.
- Caught and fixed a real bug via testing: `python-pptx` raises its own
  `PackageNotFoundError` when reading from a file path, not
  `zipfile.BadZipFile`/`KeyError` as it does from `BytesIO` - the
  corrupted-PPTX test failed with an unhandled 500 until this was fixed.
- Added HTML support with **no new dependency** - a small `HTMLParser`
  subclass (stdlib `html.parser`) that collects visible text while
  skipping `<script>`/`<style>` content. Verified against malformed
  markup (unclosed tags) before committing to the approach.
- This completes every format on `docs/ROADMAP.md`'s Phase 2 list:
  PDF, TXT, Markdown, DOCX, PPTX, HTML - all through the same registry
  and dispatcher, with zero router changes needed since DOCX.
- 22 tests total, all passing.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Use stdlib `html.parser` instead of a dependency (BeautifulSoup) for
   HTML text extraction.

(Also noted as an update to the earlier format-registry decision: the
`page_count` simplification it predicted would need revisiting for a
paginated format turned out to be exactly right - PPTX was that format.)

## What did NOT happen this session

- Chunking (the next roadmap item) was not started.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- The PPTX exception-handling bug only surfaced because a test exercised
  the real file-path code path instead of just the library in isolation
  - does that change how you'd approach verifying a new dependency next
  time, before writing the "happy path" code first?
-
- Six formats in, the dispatcher pattern has held up without changes to
  the router since DOCX. If you were asked "what would finally force you
  to change this design," what's your honest answer?
-
- Chunking is next. Before starting it, do you have a clear enough
  mental model of what a "chunk" should contain (size, overlap, metadata
  per chunk) to explain the design before writing code?
-
