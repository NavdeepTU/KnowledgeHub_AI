import logging
from typing import Callable

logger = logging.getLogger(__name__)


Encoder = Callable[[list[str]], list[list[float]]]


class EmbeddingService:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        encoder: Encoder | None = None,
    ) -> None:
        # The real sentence-transformers model is loaded lazily, on first
        # actual use, not here. Loading it takes several seconds (even
        # from a local cache) and needs network access on first-ever run
        # to download the weights - doing that at import time would slow
        # down app startup and every test collection for no benefit to
        # requests that never touch embeddings.
        self._model_name = model_name
        self._encoder = encoder

    def _get_encoder(self) -> Encoder:
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self._model_name)
            self._encoder = lambda texts: model.encode(texts).tolist()

        return self._encoder

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate an embedding vector for each input text, in order, using
        a local sentence-transformers model - no API key, no network
        dependency after the model is first downloaded, no per-call cost.
        """
        if not texts:
            return []

        encoder = self._get_encoder()
        embeddings = encoder(texts)

        logger.info(
            "Embeddings generated | count=%s | model=%s",
            len(embeddings),
            self._model_name,
        )

        return embeddings
