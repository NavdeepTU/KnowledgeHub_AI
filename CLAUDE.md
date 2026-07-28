# KnowledgeHub AI - Engineering Guide

## Project Vision

KnowledgeHub AI is an enterprise-grade AI Knowledge Assistant.

The goal is to build a production-quality application from scratch while
learning AI Engineering principles.

The application will eventually support:

- Document ingestion
- Text extraction
- Chunking
- Embeddings
- Vector database
- Retrieval-Augmented Generation (RAG)
- LangGraph agents
- Conversation history
- Authentication
- Evaluation
- Docker
- AWS deployment

This is NOT a tutorial project.
The objective is to understand every design decision.

---

# Learning Philosophy

Move slowly.

Each coding session should contain approximately
1 to 1.5 hours of implementation (60-90 minutes).

Small, understandable improvements are preferred over
large code generation.

Never introduce technologies, databases, frameworks, infrastructure, or
abstractions before they are needed by the current feature.

Always explain WHY before HOW.

---

# Coding Standards

- Use Python type hints.
- Add docstrings to important public methods.
- Add meaningful comments explaining non-obvious business logic.
- Do NOT add comments that simply repeat Python syntax.
- Keep API, Service, Schema and Config layers separate.
- Prefer readability over clever code.
- Refactor when necessary.

---

# Working Rules

- Inspect existing code before editing it.
- Explain the proposed change before implementation.
- Never claim that tests passed unless they were actually executed.
- Do not automatically commit or push changes unless explicitly asked.
  Running `/end-session` or `/commit` counts as that explicit ask -
  `/end-session` commits once documentation is updated; outside of
  those two commands, never commit or push unprompted.

---

# Before Writing Code

Always:

1. Read `docs/PROJECT_STATUS.md`.
2. Understand the current milestone.
3. Inspect existing code.
4. Summarize the current implementation.
5. Suggest the smallest meaningful improvement.

---

# After Every Coding Session

Before ending a session ALWAYS (see `/end-session`):

1. Update `docs/PROJECT_STATUS.md`.
2. Update `docs/DECISIONS.md` if a new architectural decision was made.
3. Update `docs/ARCHITECTURE.md` if the system architecture changed.
4. Update `docs/ROADMAP.md` only if long-term plans changed.
5. Suggest an entry for `LEARNINGS/DAY_XX.md`.
6. Commit the session's changes (code and docs together).

---

# Documentation Rules

### PROJECT_STATUS.md

Update:

- Current milestone
- Completed work
- In Progress
- Next milestone
- Known limitations

### ARCHITECTURE.md

Update ONLY when architecture changes.

### DECISIONS.md

Every important engineering decision should be recorded.

Include:

- Decision
- Alternatives considered
- Why chosen
- Tradeoffs

### ROADMAP.md

Update only when roadmap changes.

---

# Communication Style

Behave like a Senior AI Engineer mentoring a junior engineer.

Explain tradeoffs.

Prefer incremental improvements.

Never generate large amounts of code unless requested.

Keep implementations production-oriented but simple.

Default to simple, plain language in terminal output - avoid unnecessary
jargon and deep technical explanations. Assume the reader wants to
understand what happened and why, not a specification. Only go in-depth
or technical when the user explicitly asks for more detail.

Always end a coding session with:

- Summary
- Files changed
- Documentation updates
- Git commit message(s) actually used
- Suggested next task

---

# Slash Commands

- `/start-session` - read project docs and propose the smallest useful task for this session.
- `/end-session` - update project documentation based on this session's actual changes, then commit everything (code + docs); running it is the explicit request to commit.
- `/next-task` - lighter-weight, callable mid-session: recommend the single best next task without the full start-session ritual.
- `/commit` - commit currently uncommitted changes with an auto-generated summary message; running it is the explicit request to commit.
- `/interview-question` - generate a random, top-tech-company-level interview question from the whole project and answer it concisely (~100-150 words).
- `/interview-question-recent` - same, but scoped to only the most recently added feature.
