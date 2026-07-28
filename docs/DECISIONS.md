# Engineering Decisions

## Generate PDF test fixtures at test time instead of committing binary files

**Decision:** Build valid, encrypted, and corrupted PDF byte strings inside
`tests/conftest.py` using `pypdf.PdfWriter`, rather than storing `.pdf`
fixture files in the repository.

**Alternatives considered:**

- Commit real `.pdf` files under `tests/fixtures/`.

**Why chosen:** Generated fixtures are readable in the diff, need no binary
files in version control, and stay trivially reproducible.

**Tradeoffs:** Fixture setup code is slightly more verbose than loading a
file. Fixtures also cannot represent PDF edge cases that are hard to produce
programmatically (e.g. specific real-world corruption patterns).

---

## Redirect uploads to a temp directory during tests

**Decision:** Use an autouse `monkeypatch` fixture in `tests/conftest.py`
that overrides `settings.upload_directory` with pytest's `tmp_path` for
every test.

**Alternatives considered:**

- Let tests write into the real `uploads/` directory used by local
  development.
- Introduce a FastAPI dependency-injection override for the upload
  directory.

**Why chosen:** Monkeypatching the existing settings object is a one-line
change that keeps local `uploads/` free of test artifacts, and requires no
new abstraction layer in application code.

**Tradeoffs:** Tests rely on mutating a shared `Settings` instance rather
than an explicit dependency, which is slightly less obvious than passing
configuration directly. Acceptable at this project size.

---

## Rename `HTTP_422_UNPROCESSABLE_ENTITY` to `HTTP_422_UNPROCESSABLE_CONTENT`

**Decision:** Update `app/api/documents.py` to use
`status.HTTP_422_UNPROCESSABLE_CONTENT`.

**Alternatives considered:**

- Leave the deprecated constant in place until it is removed upstream.

**Why chosen:** The installed Starlette version already flags the old name
as deprecated; the new constant resolves to the same status code (422), so
the fix is a safe, zero-risk rename discovered while running the new test
suite.

**Tradeoffs:** None meaningful — purely a naming update.

---

## Authenticate to GitHub over SSH rather than HTTPS + gh CLI

**Decision:** Add the machine's existing SSH key to GitHub and set the
remote as `git@github.com:NavdeepTU/KnowledgeHub_AI.git`.

**Alternatives considered:**

- Install the GitHub CLI (`gh`), authenticate interactively, and use it as
  an HTTPS credential helper.

**Why chosen:** An SSH key pair already existed on the machine but wasn't
registered with GitHub yet (`ssh -T git@github.com` returned `Permission
denied` before setup). Registering it is a one-time step with no new
tooling to install, and SSH pushes never need a token or credential
prompt afterward.

**Tradeoffs:** SSH access is tied to this specific machine's key; a new
machine would need its own key registered. `gh` would have additionally
enabled scripted repo creation, which had to be done manually in the
GitHub UI instead.

---

## Auto-push committed work via a Stop hook, never auto-commit

**Decision:** Add a project-scoped Claude Code `Stop` hook
(`.claude/settings.json` + `.claude/hooks/auto_push.sh`) that pushes the
current branch to `origin` whenever there are local commits ahead of its
upstream. The script never runs `git commit` itself.

**Alternatives considered:**

- Add a `git push` step to the manual `/end-session` command only (push
  happens only when the developer remembers to run it).
- A hook that also auto-commits any working-tree changes at session end.

**Why chosen:** The developer wanted pushes to happen automatically
without relying on remembering to run a command, matching the
"push after every session" ask. Keeping the script push-only preserves
the existing, separate rule that Claude never commits without being
explicitly asked - automation was scoped to the least risky part of the
workflow. The hook silently no-ops when there's nothing to push, no
remote, or no upstream branch, and only prints a message when it actually
pushes or fails, so it doesn't add noise on every turn.

**Tradeoffs:** A `Stop` hook fires after every assistant turn, not just
"end of session," so it runs far more often than the mental model of
"once per session" suggests (harmless here since a no-op push is cheap).
It also depends on `CLAUDE_PROJECT_DIR` being set correctly by the Claude
Code harness, with a hardcoded absolute-path fallback that would break if
the project directory ever moves.

---

## Persist extracted text as a JSON sidecar file, not a database

**Decision:** Add a `DocumentRecord` schema and
`DocumentService.persist_metadata` that writes a JSON file
(`uploads/<document_id>.json`) containing the extracted text and metadata
next to each saved PDF.

**Alternatives considered:**

- Introduce SQLite or PostgreSQL now and store records there instead.
- Leave extracted text unpersisted until Phase 3 (retrieval) actually
  needs it.

**Why chosen:** A database brings schema/migration/session-management
overhead this milestone doesn't need yet - nothing in the app currently
needs to query *across* documents, only look up one document's own text
by its ID. A JSON sidecar is the smallest change that actually removes
"extracted text is discarded" as a limitation, while still giving a
concrete artifact to migrate into a real database once Phase 3 needs
indexed/queryable storage.

**Tradeoffs:** No querying across documents (finding "which documents
mention X" means scanning every JSON file), no concurrent-write safety,
and this will need a genuine migration - not just a refactor - once a
database is introduced.

---

## Use a format registry + dispatcher instead of if/elif for multi-format uploads

**Decision:** Add a `DocumentFormat` dataclass and a `SUPPORTED_FORMATS`
registry (`dict[str, DocumentFormat]`) that both the router (extension,
MIME type, and signature validation) and `DocumentService` (a
`dict[str, Callable]` mapping extension to extractor method) read from,
replacing the PDF-only validation and extraction logic.

**Alternatives considered:**

- Keep adding `if/elif` branches for each new extension directly in the
  router and in `extract_text`.
- A full class-per-format hierarchy (e.g. an abstract `DocumentHandler`
  base class with a subclass per format).

**Why chosen:** With PDF-only, `if/elif` was fine. But `docs/ROADMAP.md`
already commits to DOCX, PPTX, and HTML next, meaning the branch count
in three separate places (extension check, MIME check, extraction) was
only going to grow. A registry turns "add a format" into "add one dict
entry and one method" without touching the router's validation logic at
all. A full class hierarchy was rejected as more structure than three to
five formats justify - a dict of small dataclasses and bound methods
gives the same extensibility without new abstractions to learn.

**Tradeoffs:** Text formats (`.txt`, `.md`) have no signature check,
because plain text has no reliable magic bytes - a mislabeled binary
file that happens to decode as valid UTF-8 would be silently accepted.
`page_count` is hardcoded to 1 for non-paginated formats, which is a
simplification that may need revisiting once a format with a real
pagination concept (e.g. PPTX slides) is added.

*Update:* when PPTX was added, it did turn out to have a real pagination
concept (slides), so its extractor returns the actual slide count
instead of hardcoding 1 - the one exception to this simplification.

---

## Use stdlib `html.parser` instead of a dependency for HTML text extraction

**Decision:** Write a small `HTMLParser` subclass
(`_VisibleTextExtractor`) that collects text nodes while skipping
`<script>`/`<style>` content, rather than adding a library like
BeautifulSoup or `python-magic`-style content sniffing.

**Alternatives considered:**

- `BeautifulSoup4` - more forgiving of malformed markup, richer
  traversal API (`.get_text()`, CSS selectors), but a new dependency.
- A regex-based tag stripper - avoids a dependency too, but regexes are
  well-known to handle nested/malformed HTML incorrectly in edge cases
  that a real parser handles for free.

**Why chosen:** `html.parser.HTMLParser` is in the standard library,
handles malformed markup without crashing (verified directly - it
tolerates unclosed tags), and the only real requirement here is
"strip tags, skip script/style content" - not full DOM traversal or
CSS selector support. Reaching for a dependency for a need the standard
library already covers would go against the project's own rule against
introducing infrastructure before it's needed.

**Tradeoffs:** `HTMLParser` is lower-level than BeautifulSoup - extra
whitespace from HTML formatting isn't collapsed, only a final `.strip()`
is applied. There is also no "malformed HTML" failure mode at all:
unlike PDF/DOCX/PPTX, virtually any UTF-8 text will produce *some*
extracted result, even if it isn't meaningfully HTML - a real limitation
of this format's validation, not a bug.

---

## Chunk by character count, not tokens, in a dedicated ChunkingService

**Decision:** Add a standalone `ChunkingService` (not a method on
`DocumentService`) whose `chunk_text` splits text into overlapping
chunks measured in characters, configurable via
`Settings.chunk_size_chars`/`chunk_overlap_chars` (defaults 1000/200).

**Alternatives considered:**

- Token-based chunking using a tokenizer (e.g. `tiktoken`) so chunk
  sizes map directly to what an embedding model or LLM actually
  consumes.
- Add chunking as a method on `DocumentService` instead of a new
  service.

**Why chosen:** Token-based chunking is the right long-term choice, but
it's only meaningful once a specific embedding model is actually wired
up - token counts vary by model/tokenizer, and there's no model chosen
yet. Adding a tokenizer dependency now to size chunks for a model that
doesn't exist yet would be exactly the kind of premature infrastructure
this project avoids; switching the sizing unit later is a contained
change inside `ChunkingService`, not a rewrite. Chunking got its own
service rather than joining `DocumentService` because it's a genuinely
distinct responsibility - it doesn't care what format the text came
from, has its own configuration, and will likely grow its own
complexity (semantic/paragraph-aware chunking) independently of
extraction logic.

**Tradeoffs:** Character-based chunk sizes are a rough proxy for what an
embedding model will actually see - a 1000-character chunk could be
anywhere from ~150 to ~250 tokens depending on the text and the eventual
tokenizer, so `chunk_size_chars` will need re-tuning (or replacing
entirely) once a real embedding model is chosen. `start_offset`/
`end_offset` are kept on each chunk specifically to make that future
migration easier to verify against the original text.

---

## Extract metadata as a separate, best-effort pass rather than extending extract_text

**Decision:** Add `DocumentService.extract_metadata` as an independent
dispatch that re-parses the file for its own purposes, rather than
changing `extract_text`'s return signature to include metadata in the
same pass. Metadata extraction failures degrade to an empty
`DocumentMetadata` instead of raising and failing the upload.

**Alternatives considered:**

- Extend `extract_text` to return `tuple[str, int, DocumentMetadata]`,
  extracting text and metadata together in one pass per format.
- Let metadata extraction failures propagate and fail the whole upload,
  the same way text extraction failures do.

**Why chosen:** Changing `extract_text`'s signature would touch all six
existing, already-tested extractor methods and the router logic that
consumes them - a large, risky change for a supplementary feature. A
separate dispatch keeps the change isolated to new code. Making it
best-effort follows from what "supplementary" means here: metadata is a
nice-to-have on top of text that already extracted successfully, so a
corrupted `/Info` dictionary or similar shouldn't turn a working upload
into a failed one.

**Tradeoffs:** Files with intrinsic metadata (PDF, DOCX, PPTX) get
parsed twice - once for text, once for metadata - a real, measurable
inefficiency, acceptable at current file-size limits but worth
revisiting if this becomes a hot path. The best-effort `except
Exception` in `extract_metadata` is the one place in the codebase that
catches broadly rather than a specific exception type - a deliberate,
commented exception to that general rule, not a new default.

---

## Choose OpenAI embeddings and ChromaDB for Phase 3

**Decision:** Use OpenAI's `text-embedding-3-small` to embed chunks,
and a local, embedded ChromaDB instance (`chromadb.PersistentClient`)
as the vector store.

**Alternatives considered:**

- A local `sentence-transformers` model instead of OpenAI - free, no
  API key, fully offline, but slower/less accurate and needs to bundle
  or download model weights.
- Cohere embeddings - another hosted option, less commonly expected in
  interviews than OpenAI.
- FAISS instead of ChromaDB - an even lighter dependency, but with no
  built-in persistence or ID/metadata management, meaning a hand-rolled
  mapping from index positions back to document/chunk IDs.
- PostgreSQL + pgvector - would also satisfy the still-pending "replace
  JSON sidecars with a real database" item, but pulls Phase 5's
  Postgres decision forward early and needs a running Postgres instance.

**Why chosen:** OpenAI's embeddings are the default choice most
interviewers will assume, and the small model is inexpensive per
token. ChromaDB is embedded (no server process, no new infrastructure
to run) and gives persistence, upsert, and metadata filtering for free
- exactly what a hand-rolled FAISS setup would otherwise require
building. This was an explicit, discussed decision rather than a
unilateral pick, since it's the first milestone in this project that
introduces both an external paid dependency and a much larger
transitive dependency tree (ChromaDB alone pulls in onnxruntime, a
Kubernetes client, and OpenTelemetry).

**Tradeoffs:** Embedding now requires a funded OpenAI account and
network access - the project is no longer fully offline/free to run
end-to-end. ChromaDB's dependency footprint is large relative to
everything installed so far. Neither choice is validated against scale
yet; both are reasonable defaults for a project at this size, not a
claim that they're the right choice at production scale.

---

## Lazily construct the OpenAI client; treat embedding failures as hard failures unlike metadata

**Decision:** `EmbeddingService` does not construct the real OpenAI
client in `__init__` - only on first actual use, inside `embed_texts`.
Unlike metadata extraction, a failure in embedding or vector storage is
not caught and downgraded - it propagates into the router's existing
generic exception handler (500, saved file cleaned up).

**Alternatives considered:**

- Construct the OpenAI client eagerly at service instantiation (module
  import time), matching how `VectorStoreService`'s Chroma client is
  constructed.
- Make embedding best-effort too, the same as metadata extraction.

**Why chosen:** Verified directly that constructing `OpenAI(api_key=...)`
with no key available anywhere (arg or env var) raises immediately.
Since `EmbeddingService` is instantiated at module import time in
`app/api/documents.py`, eager construction would have broken the entire
app - including test collection - for anyone without an API key
configured, even for requests that never touch embeddings. Making
embedding failures hard failures, unlike metadata, follows from what
this step actually accomplishes: metadata is a nice-to-have, but making
a document searchable *is the point* of this milestone - a silent
"201 success, but never indexed" would be a worse outcome than a clear
error, and much harder to debug later.

**Tradeoffs:** A transient OpenAI outage or rate limit now fails an
otherwise-successful upload entirely, deleting the saved file - there's
no partial state (document saved, chunked, and readable, but not yet
searchable). Verified this behavior directly against a real, but
quota-exceeded, OpenAI account: got a clean 500, confirmed the file was
cleaned up, and confirmed the server itself kept running.

---

## Add `POST /documents/search` as a thin router endpoint, no new service

**Decision:** Add a retrieval endpoint directly in `app/api/documents.py`
that embeds the incoming query string with the existing
`EmbeddingService` and passes it to `VectorStoreService.query_similar_chunks`,
returning the nearest chunks via new `SearchRequest`/`SearchResponse`
schemas. No new service class was introduced.

**Alternatives considered:**

- A dedicated `SearchService` or `RetrievalService` to hold this logic,
  matching the pattern used for chunking/embedding/vector storage.

**Why chosen:** The endpoint's entire job is "embed one string, query
one store, return the result" - both steps already exist as tested
service methods. Wrapping that in a new service would be an empty
pass-through with no logic of its own, the kind of premature
abstraction the project explicitly avoids. `SearchRequest` validates
`query` (non-empty) and `limit` (1-50) at the schema layer so the
router stays focused on orchestration.

**Tradeoffs:** If retrieval grows real logic later (query rewriting,
re-ranking, hybrid search), it will need to be extracted into its own
service at that point - this is a deliberately deferred decision, not
a claim that a router is the right home for retrieval forever.

---

## Switch embeddings from OpenAI to a local `sentence-transformers` model

**Decision:** Replace `EmbeddingService`'s OpenAI client with a locally
run `sentence-transformers` model (`all-MiniLM-L6-v2`, 384-dimensional),
loaded lazily on first use via `SentenceTransformer(model_name)`. Removed
`openai` and `openai_api_key` entirely - the config field is now
`embedding_model_name`, and `EmbeddingService` takes an optional
`encoder: Callable[[list[str]], list[list[float]]]` for test injection
instead of a fake HTTP client.

**Alternatives considered:**

- Fix the OpenAI account's billing (add a payment method) and keep the
  hosted model.
- Use Claude for embeddings - ruled out immediately: Anthropic has no
  embeddings API, and a Claude Pro subscription is a separate product
  from API access entirely, same distinction as ChatGPT Plus vs. the
  OpenAI API.

**Why chosen:** The OpenAI account used for this project has no billing
configured, so every real embedding call failed with a 429
`insufficient_quota` - including a real upload the developer attempted
through Swagger UI. Rather than depend on a billing fix outside the
project's control, switching to a free, offline, local model removes
the last paid/networked dependency from the app entirely: it can now be
cloned and run end-to-end by anyone, including an interviewer, with no
API key and no cost. This directly reverses the tradeoff accepted in
"Choose OpenAI embeddings and ChromaDB for Phase 3" once it actually
bit.

**Tradeoffs:** `all-MiniLM-L6-v2` is a smaller, less accurate model than
`text-embedding-3-small` - retrieval quality is not directly comparable.
The first model load takes several seconds (verified: ~6-11s from a
local cache) and downloads ~90MB of weights on first-ever run, which
OpenAI's embeddings didn't require. `sentence-transformers` pulls in a
much heavier dependency tree than the `openai` client did - `torch`,
`transformers`, `scikit-learn`, and their transitives - trading network
dependency for disk footprint (installing it also surfaced a real disk
space shortage on the dev machine, resolved by clearing a 3.7GB pip
cache). The lazy-construction and hard-failure-on-error design from the
OpenAI version both carried over unchanged, since neither reason for
those choices was specific to OpenAI.

---

## Format citations as a plain string field in `VectorStoreService`, not a schema computed field

**Decision:** Add `citation: str` to `SearchResult`, populated by a
private `_format_citation` function in `vector_store_service.py` at the
point each `SearchResult` is constructed in `query_similar_chunks`.

**Alternatives considered:**

- A Pydantic `@computed_field` property on `SearchResult` itself, so
  the citation is always derived automatically from the other fields
  whenever a `SearchResult` exists.
- A separate `CitationService`.

**Why chosen:** The formatting logic is pure and trivial (interpolate
four already-known values into a string), so it doesn't earn a new
service - it lives right next to the only place `SearchResult` is
built. A schema `computed_field` was rejected to keep `schemas/`
holding only data contracts, consistent with how derived values
elsewhere in the project (chunk offsets, extracted metadata) are always
computed in `services/` and just stored on the schema, not computed
by the schema itself.

**Tradeoffs:** The citation format is a plain f-string
(`"<filename> (chunk <index>, characters <start>-<end>)"`) with no
localization or alternate formats (e.g. page numbers instead of
character offsets) - fine for a single, internal-facing API today, but
would need revisiting if citations are ever rendered directly to an
end user or need format flexibility.
