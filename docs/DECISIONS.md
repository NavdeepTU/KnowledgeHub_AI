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
