---
description: Recommend the single best next task from current project status, without the full start-session ritual
---

This is a lighter-weight companion to `/start-session`, meant to be run
at any point *within* an already-active session (e.g. right after
finishing a task) to get a fresh "what next" recommendation - not a full
recap of where the project stands.

1. Read `docs/PROJECT_STATUS.md` and `docs/ROADMAP.md`.
2. Check `git status` and recent commits for anything not yet reflected
   in `docs/PROJECT_STATUS.md` (uncommitted work, undocumented changes).
   Flag drift if found, but don't fix it here.
3. Cross-reference "Current limitations" and "Next likely milestone" in
   `docs/PROJECT_STATUS.md` against the phase currently in progress in
   `docs/ROADMAP.md`.
4. Recommend exactly ONE task - the smallest one that meaningfully
   advances the current phase, sized for 60-90 minutes. Do not list
   multiple options or a menu; pick one and justify it in a short
   paragraph (why this over other candidates you considered).
5. Do not modify any files.
6. Wait for approval before implementing.

Keep the output tight: the recommendation and its rationale, not a full
project status report. If the developer wants the full picture, they'll
run `/start-session` instead.
