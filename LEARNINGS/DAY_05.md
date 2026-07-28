# Day 5 - DOCX support

## What was built

- Added DOCX support through the format dispatcher built in the
  previous session: one new `SUPPORTED_FORMATS` entry (ZIP signature
  `PK\x03\x04`, matching DOCX's real file structure) and one new
  `_extract_docx` method using `python-docx`.
- Confirmed the dispatcher design actually works as intended: adding a
  third format required **zero changes** to `app/api/documents.py` -
  the router's validation logic is entirely driven by the registry.
- Added `python-docx` and its `lxml` dependency to `requirements.txt`.
- 3 new tests (successful upload, missing ZIP signature, corrupted
  DOCX), using a DOCX generated at test time via `python-docx` rather
  than a committed binary fixture - same pattern as the PDF fixtures.
- Manually verified against the real running app with a generated
  `.docx` file; noticed two of your own real uploads already sitting in
  `uploads/` from independent testing (a PDF and a TXT) - left both
  untouched.

## Decisions made

None new - this session applied the format-registry decision from Day 4
rather than making a new one.

## What did NOT happen this session

- PPTX and HTML support (the next roadmap items) were not started.
- The frontend/enterprise-scope conversation remains undecided.

## Reflection (fill in yourself)

- DOCX only extracts paragraph text, not tables - if an interviewer
  asked "what happens to a table in an uploaded Word doc," what would
  you say happens today, honestly?
-
- Now that PDF, TXT, MD, and DOCX all go through the same dispatcher,
  does the registry still feel like the right level of abstraction, or
  is anything about it already straining?
-
