"""Shared test doubles, kept separate from conftest.py so they can be
imported directly by tests that want to construct them explicitly."""


def fake_encoder(texts: list[str]) -> list[list[float]]:
    """Stands in for a real sentence-transformers model - no model
    download, no multi-second load time, deterministic output."""
    return [[0.1, 0.2, 0.3] for _ in texts]


class _FakeGroqMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeGroqChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeGroqMessage(content)
        self.finish_reason = "stop"


class _FakeGroqCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeGroqChoice(content)]


class _FakeGroqStreamDelta:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeGroqStreamChoice:
    def __init__(self, content: str | None) -> None:
        self.delta = _FakeGroqStreamDelta(content)


class _FakeGroqStreamChunk:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeGroqStreamChoice(content)]


class FakeGroqClient:
    """Stands in for a real groq.Groq client - no network call, no API
    key, no cost. `last_call` records the kwargs passed to
    chat.completions.create() so tests can inspect the prompt that was
    sent. `chat` and `completions` both resolve back to this same object
    so `client.chat.completions.create(...)` works without a separate
    class per attribute level.

    `stream_chunks` defaults to a single chunk equal to `response_text`;
    pass an explicit list of pieces to test that multi-chunk streaming
    is handled and reassembled correctly."""

    def __init__(
        self,
        response_text: str = "fake answer",
        stream_chunks: list[str] | None = None,
    ) -> None:
        self._response_text = response_text
        self._stream_chunks = stream_chunks if stream_chunks is not None else [response_text]
        self.last_call: dict | None = None
        self.chat = self
        self.completions = self

    def create(self, **kwargs: object):
        self.last_call = kwargs
        if kwargs.get("stream"):
            # A real leading chunk carries only the role, no content -
            # included here so tests also exercise skipping empty deltas.
            return iter(
                [_FakeGroqStreamChunk(None)]
                + [_FakeGroqStreamChunk(piece) for piece in self._stream_chunks]
            )
        return _FakeGroqCompletion(self._response_text)
