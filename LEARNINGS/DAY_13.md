# Day 13 - Streaming responses close out Phase 4

## What was built

- Added `AnswerService.generate_answer_stream`, using Groq's
  `stream=True` mode. Extracted the shared prompt-construction logic
  (system prompt, replayed history, current question + context) into a
  private `_build_messages` helper first, so the streaming and
  non-streaming methods can't drift apart on how they ground answers.
- Verified Groq's actual streaming chunk shape directly before writing
  any code: `ChatCompletionChunk.choices[0].delta.content`, which can
  be `None` on chunks that carry no text (e.g. the leading role-only
  chunk) - confirmed via `stream=True`'s real return type,
  `Stream[ChatCompletionChunk]`.
- Added `POST /documents/ask/stream`, returning newline-delimited JSON:
  one `AskStreamMeta` line (conversation_id + sources) first, then one
  `AskStreamDelta` line per generated chunk. Retrieval (embedding,
  vector search) happens before the stream starts, so those failures
  are still normal HTTP errors; a failure once streaming has begun is
  signaled as a final `AskStreamError` line instead, since the HTTP
  status is already committed by then.
- The conversation turn is only persisted after the full answer is
  reassembled from every streamed delta - preserves the existing
  "never persist a failed turn" guarantee through a structurally
  different code path.
- Chose newline-delimited JSON over Server-Sent Events deliberately -
  no frontend exists yet to justify SSE's extra framing, and NDJSON
  still carries structured metadata (a full list of source chunks)
  cleanly, which a plain-text-plus-headers approach would not have.
- Extended `FakeGroqClient` to handle `stream=True`, including a
  role-only leading chunk with no content, to make sure the real
  service correctly skips empty deltas rather than producing spurious
  blank chunks.
- 10 new tests (4 `AnswerService` streaming tests, 6 endpoint
  integration tests) - 80 tests total, all passing.
- Verified genuinely incremental streaming against the real running app
  and the real Groq API: 13 separate delta chunks arrived for one
  answer (not one buffered response chunked after the fact), correctly
  grounded with a citation, and the full reassembled answer was
  persisted to the conversation file exactly as expected.

## Decisions made

See `docs/DECISIONS.md` for full detail:

1. Stream `/documents/ask/stream` as newline-delimited JSON, not
   Server-Sent Events.

## What did NOT happen this session

- No real frontend/browser client exists yet to actually consume the
  streamed response - verification was via `curl` and the test suite
  only.
- No real database yet - JSON sidecars are still the only persistence.
- Phase 5 (PostgreSQL, Authentication, Docker, AWS, Monitoring) hasn't
  been started or scoped yet.

## Reflection (fill in yourself)

- This closes out Phase 4 entirely - RAG, conversation history, and
  streaming all built and verified with real API calls in the span of
  two sessions. Looking back at the whole phase, what part took longer
  than you expected, and what part was easier than you expected?
-
- The NDJSON-vs-SSE decision was made explicitly because there's no
  frontend yet, rather than defaulting to "do what everyone else does."
  Does deferring a standards-compliance decision until you actually
  need it feel like the right call here, or would you rather have built
  toward the standard from the start even without a consumer yet?
-
- Verifying against the real Groq API and literally counting 13
  separate delta chunks arrive was what actually proved this was real
  streaming, not just a differently-shaped response. What's your
  instinct now about how much manual, real-API verification a feature
  like this needs before you'd trust it, versus trusting the automated
  test suite alone?
-
