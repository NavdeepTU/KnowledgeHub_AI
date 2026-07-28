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
