# KnowledgeHub AI

An enterprise-style AI Knowledge Assistant, built incrementally from a bare
FastAPI service toward a full Retrieval-Augmented Generation (RAG) platform:
document ingestion, chunking, embeddings, vector search, LangGraph agents,
conversation history, auth, evaluation, and AWS deployment.

This is not a tutorial clone. Every dependency and abstraction was added
only when the current feature needed it, and every non-trivial decision is
recorded in [`docs/DECISIONS.md`](docs/DECISIONS.md) with the alternatives
considered and the tradeoffs accepted.

## Current status

**Milestone:** Automated tests for the PDF ingestion API.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for exactly what's
built, what's known-limited, and what's next. See
[`docs/ROADMAP.md`](docs/ROADMAP.md) for the long-term plan.

## Tech stack (so far)

| Concern         | Choice                          |
|-----------------|----------------------------------|
| API framework   | FastAPI + Starlette               |
| Validation      | Pydantic v2 / `pydantic-settings` |
| PDF parsing     | `pypdf`                           |
| Testing         | `pytest` + FastAPI `TestClient`   |
| Server          | `uvicorn`                         |

Nothing beyond this is in the codebase yet — no database, no vector store,
no LLM calls. Those arrive when the corresponding roadmap phase starts, so
the stack table stays honest rather than aspirational.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the layering (API /
schemas / services / core) and the current request flow through the PDF
upload endpoint.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`, with interactive docs
at `http://127.0.0.1:8000/docs`.

### Run the tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## Project layout

```
app/
  api/         # FastAPI routers - request/response wiring only
  schemas/     # Pydantic models for request/response contracts
  services/    # Business logic (PDF saving, text extraction)
  core/        # Cross-cutting concerns (settings, logging)
  main.py      # App assembly and startup

tests/         # pytest suite, in-memory fixtures, no committed binaries
docs/          # Living documentation (status, architecture, decisions, roadmap)
LEARNINGS/     # Per-session developer journal
```

## Documentation index

- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - what's done, what's next
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - system design and data flow
- [`docs/DECISIONS.md`](docs/DECISIONS.md) - engineering decision log
- [`docs/ROADMAP.md`](docs/ROADMAP.md) - long-term phased plan
- [`docs/INTERVIEW_NOTES.md`](docs/INTERVIEW_NOTES.md) - talking points for
  discussing this project in interviews
