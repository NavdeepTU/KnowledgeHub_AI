import logging
from typing import Iterator

import groq

from app.schemas.document import ConversationTurn, SearchResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are answering questions about a set of documents. For the "
    "current question, use only the numbered context blocks provided "
    "with it, and cite the block number(s) you relied on, like [1] or "
    "[2][3]. Earlier turns in this conversation are provided only so you "
    "understand what's already been discussed - they are not additional "
    "context to cite. If the current context does not contain the "
    "answer, say so plainly instead of guessing."
)

_NO_CONTEXT_ANSWER = "I don't have any relevant documents to answer that question."


class AnswerService:
    def __init__(
        self,
        model_name: str = "llama-3.1-8b-instant",
        api_key: str | None = None,
        client: groq.Groq | None = None,
    ) -> None:
        # Unlike anthropic.Anthropic(), groq.Groq() raises immediately if
        # no key is passed and none is in the environment - verified
        # directly. api_key is still passed explicitly rather than left
        # for the SDK's environment lookup, for the same reason as before:
        # pydantic-settings reads .env for its own Settings object but
        # never exports those values into os.environ.
        #
        # Constructed lazily anyway, for the same reason as
        # EmbeddingService: no SDK overhead at import time for requests
        # that never ask a question, and a missing key only breaks the
        # first real question instead of app startup.
        # An empty string (e.g. an unfilled "" placeholder in .env) is
        # normalized to None rather than passed through as-is: verified
        # directly that groq.Groq(api_key="") does NOT raise the SDK's
        # normal "key not set" error - it constructs fine, then fails at
        # request time with a confusing APIConnectionError instead of a
        # clear authentication error. None gets the SDK's real check.
        self._model_name = model_name
        self._api_key = api_key or None
        self._client = client

    def _get_client(self) -> groq.Groq:
        if self._client is None:
            self._client = groq.Groq(api_key=self._api_key)

        return self._client

    def _build_messages(
        self,
        question: str,
        chunks: list[SearchResult],
        history: list[ConversationTurn] | None,
    ) -> list[dict]:
        context = "\n\n".join(
            f"[{index}] {chunk.citation}\n{chunk.text}"
            for index, chunk in enumerate(chunks, start=1)
        )

        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        for turn in history or []:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})

        messages.append(
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }
        )

        return messages

    def generate_answer(
        self,
        question: str,
        chunks: list[SearchResult],
        history: list[ConversationTurn] | None = None,
    ) -> str:
        """
        Answer a question using only the given chunks as context, via a
        single non-streaming chat completion - no agent loop, no tool use.

        `history` replays prior question/answer text (not the chunks that
        grounded those earlier answers) so the model has conversational
        memory without re-sending every past turn's full context on every
        request. Chat completions are stateless, so this is rebuilt fresh
        on every call.
        """
        if not chunks:
            return _NO_CONTEXT_ANSWER

        client = self._get_client()
        response = client.chat.completions.create(
            model=self._model_name,
            max_completion_tokens=1024,
            messages=self._build_messages(question, chunks, history),
        )

        answer = response.choices[0].message.content

        logger.info(
            "Answer generated | model=%s | chunks_used=%s",
            self._model_name,
            len(chunks),
        )

        return answer

    def generate_answer_stream(
        self,
        question: str,
        chunks: list[SearchResult],
        history: list[ConversationTurn] | None = None,
    ) -> Iterator[str]:
        """
        Same grounding and prompt as generate_answer, but yields the
        answer incrementally as Groq generates it, instead of waiting
        for the full response. Chunks with no text delta (e.g. the
        first chunk, which only carries the role) are skipped.
        """
        if not chunks:
            yield _NO_CONTEXT_ANSWER
            return

        client = self._get_client()
        stream = client.chat.completions.create(
            model=self._model_name,
            max_completion_tokens=1024,
            messages=self._build_messages(question, chunks, history),
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

        logger.info(
            "Answer stream completed | model=%s | chunks_used=%s",
            self._model_name,
            len(chunks),
        )
