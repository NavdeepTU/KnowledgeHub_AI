---
description: Generate a random, top-tech-company-level interview question from this project and answer it concisely
---

This produces mock-interview practice material grounded in what's
actually been built in this project so far - never invent a capability,
decision, or number that doesn't exist in the code or `docs/`.

1. Read `docs/DECISIONS.md`, `docs/ARCHITECTURE.md`, and
   `docs/PROJECT_STATUS.md` to see the full set of things that have
   actually been built and decided so far.
2. Pick ONE topic at random from across the whole project - a design
   decision, a piece of validation logic, a tradeoff, an architectural
   choice. Vary the pick each time this runs; don't default to the most
   recent or most obvious topic every time.
3. Read the actual source file(s) behind that topic before writing
   anything, so every technical claim is verifiable against real code.
4. Write ONE realistic, challenging interview question a senior/staff
   engineer at a top tech company would plausibly ask about it - not a
   softball, and not generic ("tell me about a project you built").
   Phrase it the way an interviewer actually would, e.g. "Why did you
   choose X over Y here?", "What's the first thing that breaks if this
   had to handle 10,000 requests a second?", "Walk me through exactly
   what happens when...".
5. Answer it the way a strong candidate would say it OUT LOUD in an
   interview, not the way it would be written in a design doc. Keep the
   whole answer to roughly 100-150 words (about 45-60 seconds spoken) -
   short enough to actually say, not a transcript to read from. In that
   space, hit only:
   - What was built, in one or two sentences.
   - Why this approach over the real alternative (cite
     `docs/DECISIONS.md` if an entry exists) - one sentence, in
     engineering terms, not "it was simpler."
   - How it works, mechanically - one or two sentences, no restating
     the feature name.
   Skip the follow-up question entirely; one sharp, complete answer is
   the goal, not a full Q&A transcript.
6. Do not modify any files - this is read-only, output-only.

Keep the tone like a strong candidate's real spoken answer: precise,
confident, and honest about tradeoffs - dense with substance, not long.
If the answer would take more than a minute to say out loud, cut it, not
the technical accuracy.
