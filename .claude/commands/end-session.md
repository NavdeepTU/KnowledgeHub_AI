---
description: Update project documentation based on this session's actual changes, then commit
---

Running this command IS the explicit request to commit once documentation
is updated - proceed through the commit step without asking again, but
still follow its safety rules below.

Review the actual code changes made during this session.

Then:

1. Update `docs/PROJECT_STATUS.md` with:
   - current milestone,
   - completed work,
   - work still in progress,
   - next recommended task,
   - current limitations.

2. Update `docs/ARCHITECTURE.md` only when system components,
   responsibilities, or data flow changed.

3. Update `docs/DECISIONS.md` only when an important technical or
   architectural decision was made. Include:
   - decision,
   - context,
   - alternatives,
   - reason chosen,
   - trade-offs.

   If a new entry was added, also add a matching entry to
   `docs/INTERVIEW_NOTES.md`: the question an interviewer would plausibly
   ask about it, a short spoken-form answer (30-60 seconds), and the
   honest follow-up question it invites. Skip this only if the decision
   is too minor to plausibly come up in an interview.

4. Update `docs/ROADMAP.md` only when the long-term plan changed.

5. Create or update today's file under `LEARNINGS/`.
   Do not invent personal learnings. Add prompts for the developer to
   complete where personal reflection is required.

6. Run relevant tests or validation commands.

7. Commit everything from this session (the code changes and the
   documentation updates together), following the same rules as
   `/commit`:
   - Decide whether the changes are one coherent unit of work or
     several unrelated ones. One unit: stage by name and make a single
     commit. Multiple unrelated units: propose splitting into separate
     commits and confirm before doing so, rather than guessing.
   - Never stage or commit anything that looks like a secret or
     credential (`.env`, private keys, tokens), even if modified.
   - Write commit message(s) in this repo's existing style: a concise
     summary line in imperative mood, a short body (1-3 sentences)
     explaining *why*, ending with
     `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
   - Do not push - the project's auto-push Stop hook handles that
     automatically once this turn ends.
   - If there is truly nothing uncommitted after the documentation
     updates, say so rather than creating an empty commit.

8. Provide:
   - session summary,
   - files changed,
   - test results,
   - documentation updates,
   - the commit message(s) actually used,
   - next task requiring no more than 90 minutes.
