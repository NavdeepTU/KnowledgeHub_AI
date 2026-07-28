---
description: Generate an interview question and concise technical answer about the most recently added feature
---

Same purpose and rules as `/interview-question`, but scoped to only the
most recently added feature instead of the whole project.

1. Check `git status` first. If there are uncommitted changes to
   application code (`app/` or `tests/`), that's the recent feature -
   it's more recent than anything already committed. Only if the
   working tree is clean, fall back to `git log` to find the most
   recent commit(s) that changed `app/` or `tests/` (not
   documentation-only commits).
2. Read the real diff/files for that work so every claim is grounded in
   actual code, not assumption.
3. Check `docs/DECISIONS.md` for any decision entry tied to this
   feature, and use it if one exists.
4. Write ONE realistic, challenging interview question a senior/staff
   engineer at a top tech company would ask specifically about this
   feature - not a softball, phrased the way a real interviewer would.
5. Answer it the way a strong candidate would say it OUT LOUD in an
   interview, not the way it would be written in a design doc. Keep the
   whole answer to roughly 100-150 words (about 45-60 seconds spoken) -
   short enough to actually say, not a transcript to read from. In that
   space, hit only:
   - What was built, in one or two sentences.
   - Why this approach over the real alternative - one sentence, in
     engineering terms.
   - How it works, mechanically - one or two sentences.
   Skip the follow-up question entirely; one sharp, complete answer is
   the goal, not a full Q&A transcript.
6. Do not modify any files - this is read-only, output-only.

If no application code has changed (committed or not) since the last
documented milestone, say so rather than reaching further back to
manufacture a "recent" feature.
