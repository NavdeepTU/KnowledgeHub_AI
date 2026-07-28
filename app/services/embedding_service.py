import logging
from typing import Protocol

from openai import OpenAI


logger = logging.getLogger(__name__)


class _EmbeddingItem(Protocol):
    embedding: list[float]


class _EmbeddingResponse(Protocol):
    data: list[_EmbeddingItem]


class _Embeddings(Protocol):
    def create(self, *, model: str, input: list[str]) -> _EmbeddingResponse: ...


class EmbeddingClient(Protocol):
    """The subset of the OpenAI client's interface this service needs.

    Lets tests inject a fake client with this same shape instead of
    hitting the real API - no network calls, no cost, no key required.
    """

    embeddings: _Embeddings


class EmbeddingService:
    def __init__(
        self,
        client: EmbeddingClient | None = None,
        api_key: str | None = None,
    ) -> None:
        # The real OpenAI client is constructed lazily, on first actual
        # use, not here. Constructing it eagerly raises immediately if no
        # API key is configured anywhere (env var or explicit arg), which
        # would break app startup - and test collection - for anyone who
        # hasn't set one up yet, even for requests that never touch
        # embeddings at all.
        self._client = client
        self._api_key = api_key

    def _get_client(self) -> EmbeddingClient:
        if self._client is None:
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def embed_texts(self, texts: list[str], model: str) -> list[list[float]]:
        """
        Generate an embedding vector for each input text, in order,
        using the given OpenAI embedding model.
        """
        if not texts:
            return []

        client = self._get_client()
        response = client.embeddings.create(model=model, input=texts)
        embeddings = [item.embedding for item in response.data]

        logger.info(
            "Embeddings generated | count=%s | model=%s",
            len(embeddings),
            model,
        )

        return embeddings
