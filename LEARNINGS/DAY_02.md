# Day 2 - GitHub remote and auto-push hook

## What was built

- Connected the local repo to a new GitHub repository
  (`git@github.com:NavdeepTU/KnowledgeHub_AI.git`) over SSH, after
  registering an existing local SSH key with GitHub as an Authentication
  Key.
- Pushed all existing commits to `origin/master`.
- Added `.claude/hooks/auto_push.sh` and `.claude/settings.json`: a
  project-scoped `Stop` hook that automatically pushes already-committed
  work after each turn. It never commits anything itself.
- Tested the hook's push logic against a throwaway sandbox repo (not the
  real project) before wiring it in, to confirm the no-op and push paths
  both behave correctly.
- Confirmed (no code change) that LangGraph agents should come after
  Phase 2/3 (chunking, retrieval) rather than before, per the existing
  Roadmap ordering — a plain RAG chain first, agent orchestration second.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Authenticate to GitHub over SSH rather than installing the `gh` CLI.
2. Auto-push via a `Stop` hook, scoped to push-only (never auto-commit).

## What did NOT happen this session

The previously proposed next milestone (persisting extracted text to a
JSON sidecar file) was not started — the session was redirected to
GitHub/tooling setup instead. It's still the recommended next task.

## Reflection (fill in yourself)

- Was redirecting this session to infrastructure setup (GitHub + hooks)
  the right call, or would you rather have finished the persistence
  feature first and set up git remote/hooks separately?
-
- The auto-push hook fires after every turn, not literally "once per
  session" — does that match what you actually wanted, now that you know
  how it behaves?
-
- If an interviewer asked "why did you automate git push but not git
  commit," could you answer that in one sentence without looking at
  `docs/INTERVIEW_NOTES.md`?
-
