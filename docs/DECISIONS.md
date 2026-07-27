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
