# Day 12 - Phase 4 kickoff: RAG, conversation history, and a provider switch

## What was built

- Added `AnswerService` and `POST /documents/ask`: retrieves chunks the
  same way `/search` does, then asks an LLM to answer using only that
  context, citing block numbers. Built first against Claude Haiku 4.5
  via the official `anthropic` SDK - the key authenticated, but the
  Anthropic account had no billing configured, so no real answer could
  be generated yet.
- Added conversation history: `ConversationService` persists each turn
  (question + answer text only, not the grounding chunks) as a JSON
  sidecar per `conversation_id`, same pattern as document records - no
  database. History replays into the LLM call as alternating
  user/assistant messages, since chat completions are stateless.
- Had an explicit, honest conversation about cost: already paying for
  Claude Pro/Code, so does adding Anthropic API billing on top make
  sense? Confirmed directly that subscription usage and API billing are
  completely separate products at Anthropic (same split as ChatGPT Plus
  vs. the OpenAI API) - there's no way around paying for API access
  specifically if staying with Claude.
- Explored real free alternatives instead of paying twice: local LLMs
  via Ollama (rejected for this step specifically - local models are
  bigger than the embedding model that already strained this machine's
  disk, and grounded-answer quality matters more here than it did for
  embeddings) versus Groq's genuinely free hosted tier for open-source
  models. Chose Groq.
- Rewrote `AnswerService` around Groq's actual SDK shape, verified
  directly rather than assumed: OpenAI-style `chat.completions.create`,
  system prompt inside `messages` (no top-level `system` param),
  `max_completion_tokens`, response at `choices[0].message.content`, no
  Anthropic-style `refusal` stop reason. Removed `anthropic` and its
  orphaned transitive deps entirely.
- Found and fixed a real bug while verifying against the real app: an
  empty-string API key (exactly what an unfilled `.env` placeholder
  produces) slipped past Groq's own "key not set" check and failed
  later with a confusing connection error instead of a clear one.
  Diagnosed by testing three inputs directly (`None`, `""`, a real bad
  key) rather than guessing from the stack trace.
- 70 tests total, all passing at end of session.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Persist conversation history as question/answer text only, not the
   grounding chunks.
2. Switch `AnswerService` from Claude (Anthropic) to Groq.
3. Normalize an empty-string API key to `None` in `AnswerService`.

## What did NOT happen this session

- No real successful answer has been generated and observed yet at the
  time these docs were written - a `GROQ_API_KEY` was added right at
  the end of the session, verification of an actual successful answer
  is the immediate next step.
- No streaming responses - `/documents/ask` still waits for the full
  answer before returning.
- No real database yet - JSON sidecars are still the only persistence,
  now used for two different things (documents and conversations).

## Reflection (fill in yourself)

- This session included a real "wait, do I actually need to pay for
  this" conversation before writing more code, rather than just
  reaching for a credit card. Did stepping back to ask that question
  change your instinct about when a paid dependency is actually
  justified versus when it's just convenient?
-
- Building the Claude version first, fully testing it, and then
  discovering the real reason to switch (a candid cost conversation,
  not a technical failure) is a different kind of pivot than the
  OpenAI-to-local-embeddings switch, which was forced by a billing
  error. Does a deliberately-chosen pivot feel different to have made
  than a forced one, looking back?
-
- The empty-string API key bug was found by verifying against the real
  running app, not by a unit test - none of the 70 automated tests
  would have caught it, since none of them pass an actual empty string
  through to a real SDK call. What's your take on where the line should
  be between "worth a unit test" and "worth manual verification" for
  bugs like this?
-
