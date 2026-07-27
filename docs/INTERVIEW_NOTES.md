# Interview Notes

This file turns `docs/DECISIONS.md` into spoken-answer form. Every entry
here should trace back to a real decision recorded there — nothing
invented, nothing aspirational. When `end-session` records a new decision,
it also prompts adding the matching entry here.

Each entry: the likely question, a short spoken answer (aim for
30-60 seconds out loud), and the deeper follow-up an interviewer might
push into.

---

## "Walk me through this project."

KnowledgeHub AI is an AI knowledge assistant I'm building end-to-end and
incrementally — right now it's a FastAPI service that ingests PDFs,
validates them defensively, and extracts text. It's structured in layers
(API / schemas / services / core) so business logic isn't tangled into
route handlers, and every non-trivial decision is written down with the
alternatives I rejected and why. The roadmap goes from ingestion to
chunking, embeddings, a vector store, RAG, and eventually deployment on
AWS — but nothing is added before the current milestone actually needs it.

**Follow-up to expect:** "What's the hardest part so far?" — Answer
honestly from `LEARNINGS/`, not from this file.

---

## "How did you test file upload without a real database or S3?"

*(from: Generate PDF test fixtures at test time)*

I generate the PDFs in the test suite itself using `pypdf.PdfWriter` —
a valid one, an encrypted one, and a corrupted one — instead of committing
binary fixture files. That keeps the fixtures readable in a diff and
means there's nothing to accidentally go stale in version control. The
tradeoff is I can't easily reproduce very specific real-world corruption
patterns that way, only representative ones.

**Follow-up to expect:** "What would you do if you needed to test against
a real-world malformed PDF you can't generate programmatically?" — Commit
that one specific file as a named exception, don't generalize the
approach.

---

## "How do you keep tests from polluting your local dev environment?"

*(from: Redirect uploads to a temp directory during tests)*

The app's upload directory lives on a single `Settings` object. In tests,
an autouse fixture monkeypatches that path to pytest's `tmp_path` for
every test, so nothing ever gets written to the real `uploads/` folder a
developer is using locally. I chose that over adding a dependency-injection
override because it's a one-line change and doesn't require a new
abstraction the app doesn't need yet.

**Follow-up to expect:** "Isn't monkeypatching shared state a smell?" —
Yes in a larger app; at this size, an explicit DI seam would be premature
abstraction for a single settings value.

---

## "How do you handle upstream deprecations?"

*(from: Rename HTTP_422_UNPROCESSABLE_ENTITY)*

Running the new test suite surfaced a `StarletteDeprecationWarning` on a
status constant I was already using. I confirmed the replacement resolved
to the same status code, fixed both call sites, and re-ran the suite
before moving on — a small example of tests paying for themselves beyond
just catching regressions.

---

## "Why this layering (api / schemas / services / core)?"

*(from: docs/ARCHITECTURE.md)*

Route handlers only translate HTTP in and out; business logic like saving
a file or extracting text lives in a service so it can be tested without
spinning up HTTP; schemas keep the public response contract independent
of internal types; core holds cross-cutting stuff like settings and
logging that every layer needs. It's a small-scale controller/service
split, adopted because the validation logic already didn't belong in a
route handler — not because "layered architecture" was a goal on its own.

---

## How to extend this file

After a session that adds an entry to `docs/DECISIONS.md`, add a matching
entry here: the question an interviewer would plausibly ask, a short
spoken answer, and the honest follow-up. If a decision doesn't map to a
question someone would actually ask in an interview, it probably doesn't
need an entry here yet.
