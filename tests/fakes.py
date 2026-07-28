"""Shared test doubles, kept separate from conftest.py so they can be
imported directly by tests that want to construct them explicitly."""


class _FakeEmbeddingItem:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding


class _FakeEmbeddingResponse:
    def __init__(self, data: list[_FakeEmbeddingItem]) -> None:
        self.data = data


class _FakeEmbeddings:
    """Stands in for the real OpenAI client's .embeddings - no network,
    no cost, no API key required."""

    def create(self, *, model: str, input: list[str]) -> _FakeEmbeddingResponse:
        return _FakeEmbeddingResponse(
            [_FakeEmbeddingItem([0.1, 0.2, 0.3]) for _ in input]
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddings()
