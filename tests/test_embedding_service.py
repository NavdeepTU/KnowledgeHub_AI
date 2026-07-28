from app.services.embedding_service import EmbeddingService
from tests.fakes import FakeOpenAIClient


def test_embed_texts_returns_empty_list_for_empty_input() -> None:
    service = EmbeddingService(client=FakeOpenAIClient())

    assert service.embed_texts([], model="text-embedding-3-small") == []


def test_embed_texts_returns_one_embedding_per_input_in_order() -> None:
    service = EmbeddingService(client=FakeOpenAIClient())

    embeddings = service.embed_texts(
        ["first chunk", "second chunk", "third chunk"],
        model="text-embedding-3-small",
    )

    assert len(embeddings) == 3
    assert all(isinstance(embedding, list) for embedding in embeddings)
    assert all(len(embedding) > 0 for embedding in embeddings)


def test_embed_texts_passes_model_and_input_to_client() -> None:
    received: dict = {}

    class RecordingEmbeddings:
        def create(self, *, model: str, input: list[str]):
            received["model"] = model
            received["input"] = input
            return FakeOpenAIClient().embeddings.create(model=model, input=input)

    class RecordingClient:
        def __init__(self) -> None:
            self.embeddings = RecordingEmbeddings()

    service = EmbeddingService(client=RecordingClient())
    service.embed_texts(["some text"], model="text-embedding-3-large")

    assert received["model"] == "text-embedding-3-large"
    assert received["input"] == ["some text"]
