from app.services.embedding_service import EmbeddingService
from tests.fakes import fake_encoder


def test_embed_texts_returns_empty_list_for_empty_input() -> None:
    service = EmbeddingService(encoder=fake_encoder)

    assert service.embed_texts([]) == []


def test_embed_texts_returns_one_embedding_per_input_in_order() -> None:
    service = EmbeddingService(encoder=fake_encoder)

    embeddings = service.embed_texts(["first chunk", "second chunk", "third chunk"])

    assert len(embeddings) == 3
    assert all(isinstance(embedding, list) for embedding in embeddings)
    assert all(len(embedding) > 0 for embedding in embeddings)


def test_embed_texts_passes_input_to_encoder() -> None:
    received: dict = {}

    def recording_encoder(texts: list[str]) -> list[list[float]]:
        received["input"] = texts
        return fake_encoder(texts)

    service = EmbeddingService(encoder=recording_encoder)
    service.embed_texts(["some text"])

    assert received["input"] == ["some text"]


def test_embed_texts_loads_real_model_only_once() -> None:
    """The encoder is only constructed lazily and cached after first use."""
    calls = []

    class CountingService(EmbeddingService):
        def _get_encoder(self):
            calls.append(1)
            return super()._get_encoder()

    service = CountingService(encoder=fake_encoder)
    service.embed_texts(["a"])
    service.embed_texts(["b"])

    assert len(calls) == 2  # _get_encoder is called each time...
    assert service._encoder is fake_encoder  # ...but never replaces the injected one
