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

## "Walk me through how you set up your git workflow with an AI coding assistant."

*(from: Auto-push committed work via a Stop hook, never auto-commit)*

I use Claude Code with a session-based workflow — small, scoped commits
that I review and explicitly approve. I wanted pushes to happen without
me remembering to run `git push` every time, so I added a hook that fires
after each turn and pushes to `origin` if there are local commits ahead
of the remote. Critically, the hook only pushes — it never commits.
Committing still requires me to explicitly ask for it, so there's no risk
of half-finished or unreviewed work silently landing on GitHub.

**Follow-up to expect:** "What stops it from pushing broken code?" —
Nothing automatic; the safety net is that nothing gets committed without
my review in the first place. The hook operates strictly downstream of
that human checkpoint, and a CI gate would be the next layer if this were
a team project.

---

## "How do you persist data before you have a database?"

*(from: Persist extracted text as a JSON sidecar file, not a database)*

I didn't reach for a database the moment I needed to persist something -
I asked what actually needed to be true right now, which was just "look
up one document's own extracted text by its ID." So I wrote a JSON
sidecar file next to each saved PDF instead. It's the smallest change
that removes "extracted text is discarded" as a limitation, and it gives
me something concrete to migrate into a real database later, once
retrieval actually needs to query *across* documents instead of looking
up one at a time.

**Follow-up to expect:** "What breaks first as this scales?" — Concurrent
writes (no locking) and the inability to search across documents without
scanning every file; both are exactly the signals that would tell me it's
time for the database migration, not a reason to build it preemptively.

---

## "You went from PDF-only to supporting multiple formats — how did you design that extension point?"

*(from: Use a format registry + dispatcher instead of if/elif for multi-format uploads)*

I pulled the per-format details — allowed extension, accepted MIME
types, an optional signature — into a small registry, and extraction
into a dict mapping extension to handler method. Both the router's
validation and the service's extraction now read from the same source of
truth instead of branching separately. I did this now rather than
earlier because the roadmap already commits to three more formats next;
with just PDF, a simple if-statement would've been the right call — the
registry earns its keep specifically because the branch count was about
to grow in three places at once.

**Follow-up to expect:** "What's a gap in this design?" — Text formats
have no signature check, because plain text has no reliable magic bytes.
A renamed binary file that happens to decode as valid UTF-8 would be
silently accepted today — a known, accepted gap, not an oversight.

---

## "Why didn't you use BeautifulSoup for HTML parsing?"

*(from: Use stdlib html.parser instead of a dependency for HTML text extraction)*

Because the actual requirement was narrow — strip tags, skip script and
style content, keep the visible text — and Python's standard library
already covers that with `html.parser`. I wrote a small `HTMLParser`
subclass that tracks whether it's inside a script or style tag and
collects text nodes otherwise. I tested it against malformed markup
first — unclosed tags — to confirm it wouldn't crash before committing
to the approach, since that's the realistic case for HTML found in the
wild.

**Follow-up to expect:** "What do you lose by not using a real HTML
library?" — No DOM traversal or CSS selectors, and no whitespace
normalization beyond a final strip. More importantly, there's no
"invalid HTML" failure mode at all — almost any UTF-8 text parses to
*something* — which is a real, acknowledged gap in this format's
validation, not something BeautifulSoup would have fixed either.

---

## "You're chunking text for future embeddings — why character count instead of tokens?"

*(from: Chunk by character count, not tokens, in a dedicated ChunkingService)*

Because token-based sizing is only meaningful once I've actually picked
an embedding model — token counts depend on that model's tokenizer, and
I haven't chosen one yet. Adding a tokenizer dependency to size chunks
for a model that doesn't exist would be the exact kind of premature
infrastructure I've been avoiding all through this project. So chunking
lives in its own `ChunkingService`, splitting on character count with
configurable size and overlap, and every chunk keeps its original
start and end offsets — so when I do add token-based sizing, or need
citations, that migration has something solid to verify against.

**Follow-up to expect:** "Isn't character count a bad proxy for tokens?"
— Yes, roughly 4 characters per token as a rule of thumb, so a
1000-character chunk is a rough size, not a precise one. That's an
accepted, temporary approximation, not a design I'd defend as final.

---

## "Your metadata extraction is the only place in your codebase with a bare `except Exception` — why?"

*(from: Extract metadata as a separate, best-effort pass rather than extending extract_text)*

Because metadata — title, author, creation date — is genuinely
supplementary information sitting on top of text that's already
extracted successfully. By the time metadata extraction runs, the file
has already parsed once for its actual content, so a corrupted `/Info`
dictionary or similarly narrow metadata quirk shouldn't turn a working
upload into a failed one. It's a deliberate, commented exception to
catching specific exception types everywhere else in the codebase, not
a habit — everything else still fails loudly on purpose.

**Follow-up to expect:** "Doesn't that hide real bugs?" — It's logged
with `logger.exception` before falling back to empty metadata, so
nothing is silent — it just doesn't block the user. I also kept
metadata extraction as its own pass that re-parses the file rather than
folding it into the existing, already-tested text-extraction methods,
so this whole change stayed isolated to new code instead of touching
six working extractors.

---

## "Why OpenAI and ChromaDB for your embeddings and vector store?"

*(from: Choose OpenAI embeddings and ChromaDB for Phase 3)*

I treated this as an explicit scoping decision rather than picking
unilaterally, because it's the first milestone in the project that
introduces a paid external dependency. OpenAI's `text-embedding-3-small`
is the default choice most interviewers would expect and is cheap per
token; ChromaDB is embedded — no server to run — and gives me
persistence and metadata filtering for free instead of hand-rolling an
ID-to-chunk mapping on top of something like FAISS. The real cost is
dependency weight: ChromaDB alone pulled in onnxruntime, a Kubernetes
client, and OpenTelemetry.

**Follow-up to expect:** "What would you reconsider at scale?" — Both
choices are reasonable defaults for a project this size, not a claim
they're right at production scale — a managed vector store or a
self-hosted open embedding model would be the next things I'd
evaluate under real load or cost pressure.

---

## "Your embedding client is constructed lazily — what does that actually protect against?"

*(from: Lazily construct the OpenAI client; treat embedding failures as hard failures unlike metadata)*

I tested this directly: constructing the OpenAI client with no API key
anywhere raises immediately, not on first request. Since the service is
instantiated once at import time, doing that eagerly would have broken
the entire app — including the test suite — for anyone without a key
configured, even for requests that never touch embeddings. So the real
client only gets built on the first actual `embed_texts` call. I also
made embedding failures hard failures, unlike metadata, because making
a document searchable is the actual point of this step — a silent
"uploaded but never indexed" would be worse than a clear error.

**Follow-up to expect:** "Did you verify that, or is it theoretical?" —
Verified against a real account with no billing configured: got a clean
500, confirmed the saved file was deleted, and confirmed the server
kept serving other requests afterward.

---

## "Why doesn't your search endpoint have its own service class?"

*(from: Add `POST /documents/search` as a thin router endpoint)*

Because it doesn't do anything beyond calling two methods that already
exist and are already tested — embed the query string, then query the
vector store for the nearest chunks. Wrapping that in a `SearchService`
would just be a pass-through with no logic of its own, which is exactly
the kind of abstraction I try not to add before it earns its place. If
retrieval later grows real logic — re-ranking, query rewriting, hybrid
search — that's when it'd justify its own service.

**Follow-up to expect:** "Where does query validation happen?" — At the
schema layer: `SearchRequest` enforces a non-empty query and a limit
between 1 and 50 with Pydantic `Field` constraints, so the router never
has to hand-check them.

---

## "You picked OpenAI for embeddings, then switched. What happened?"

*(from: Switch embeddings from OpenAI to a local sentence-transformers model)*

The OpenAI account I was using had no billing configured, so every real
embedding call — including a real upload I tried through Swagger UI —
failed with a 429 quota error. Rather than block the project on a
billing fix, I switched `EmbeddingService` to a local
`sentence-transformers` model, `all-MiniLM-L6-v2`, loaded lazily the
same way the OpenAI client was. That removes the last paid, networked
dependency from the whole app — anyone can clone it and run it
end-to-end for free, no API key needed, which matters a lot for a
portfolio project an interviewer might actually run.

**Follow-up to expect:** "What did you give up?" — Retrieval quality:
`all-MiniLM-L6-v2` is smaller and less accurate than
`text-embedding-3-small`, and it also pulled in a much heavier
dependency tree — `torch` and `transformers` — trading a network
dependency for real disk footprint, which actually ran my dev machine
out of disk space mid-install.

---

## How to extend this file

After a session that adds an entry to `docs/DECISIONS.md`, add a matching
entry here: the question an interviewer would plausibly ask, a short
spoken answer, and the honest follow-up. If a decision doesn't map to a
question someone would actually ask in an interview, it probably doesn't
need an entry here yet.
