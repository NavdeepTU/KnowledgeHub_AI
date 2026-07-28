---
description: Commit currently uncommitted changes with an auto-generated summary message
---

Running this command IS the explicit request to commit - proceed without
asking again, but still follow the safety steps below.

1. Run `git status` and `git diff` (staged and unstaged) to see exactly
   what changed. If there is nothing uncommitted, say so and stop - never
   create an empty commit.
2. If a fast test suite exists (e.g. `pytest`), run it and note the
   result. Don't block the commit on failure, but report it clearly
   rather than staying silent about it - never claim tests passed without
   having actually run them.
3. Decide whether the changes are one coherent unit of work or several
   unrelated ones (e.g. a doc edit mixed with an unrelated feature
   change):
   - One unit of work: stage the relevant files by name (never `git add
     -A` or `git add .`) and make a single commit.
   - Multiple unrelated units: propose splitting into separate commits
     and confirm before doing so, rather than guessing.
4. Never stage or commit anything that looks like a secret or credential
   (`.env`, private keys, tokens), even if it shows up as modified.
5. Write the commit message in this repo's existing style (check recent
   `git log` for examples):
   - A concise summary line in imperative mood.
   - A short body (1-3 sentences) explaining *why*, not a restatement of
     the diff.
   - End with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
6. After committing, run `git status` to confirm the result.
7. Do not push - the project's auto-push Stop hook handles that
   automatically once this turn ends.
8. Report: the commit message used, the files included, test results,
   and anything intentionally excluded or left for a follow-up commit.
