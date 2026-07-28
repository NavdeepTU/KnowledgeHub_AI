from pathlib import Path

import pytest

from app.schemas.document import DocumentChunk
from app.services.vector_store_service import VectorStoreService


@pytest.fixture()
def vector_store(tmp_path: Path) -> VectorStoreService:
    return VectorStoreService(persist_directory=tmp_path / "chroma_test")


def _make_chunk(index: int, text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_index=index,
        text=text,
        start_offset=index * 10,
        end_offset=index * 10 + len(text),
        character_count=len(text),
    )


def test_upsert_chunks_with_empty_list_is_noop(vector_store: VectorStoreService) -> None:
    # Should not raise even with no chunks/embeddings to store.
    vector_store.upsert_chunks(
        document_id="doc-1",
        filename="empty.txt",
        chunks=[],
        embeddings=[],
    )


def test_upsert_chunks_stores_correct_count_and_ids(
    vector_store: VectorStoreService,
) -> None:
    chunks = [_make_chunk(0, "first chunk"), _make_chunk(1, "second chunk")]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    vector_store.upsert_chunks(
        document_id="doc-1",
        filename="notes.txt",
        chunks=chunks,
        embeddings=embeddings,
    )

    result = vector_store._collection.get(ids=["doc-1:0", "doc-1:1"])
    assert set(result["ids"]) == {"doc-1:0", "doc-1:1"}


def test_upsert_chunks_stores_locating_metadata(
    vector_store: VectorStoreService,
) -> None:
    chunks = [_make_chunk(0, "only chunk")]
    embeddings = [[0.5, 0.6]]

    vector_store.upsert_chunks(
        document_id="doc-2",
        filename="report.pdf",
        chunks=chunks,
        embeddings=embeddings,
    )

    result = vector_store._collection.get(ids=["doc-2:0"])
    metadata = result["metadatas"][0]

    assert metadata["document_id"] == "doc-2"
    assert metadata["filename"] == "report.pdf"
    assert metadata["chunk_index"] == 0
    assert metadata["start_offset"] == 0
    assert metadata["end_offset"] == len("only chunk")
    assert result["documents"][0] == "only chunk"


def test_query_similar_chunks_on_empty_store_returns_empty_list(
    vector_store: VectorStoreService,
) -> None:
    results = vector_store.query_similar_chunks([0.1, 0.2], limit=5)

    assert results == []


def test_query_similar_chunks_returns_stored_chunks(
    vector_store: VectorStoreService,
) -> None:
    chunks = [_make_chunk(0, "first chunk"), _make_chunk(1, "second chunk")]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    vector_store.upsert_chunks(
        document_id="doc-1",
        filename="notes.txt",
        chunks=chunks,
        embeddings=embeddings,
    )

    results = vector_store.query_similar_chunks([0.1, 0.2], limit=5)

    assert len(results) == 2
    assert {result.text for result in results} == {"first chunk", "second chunk"}
    assert all(result.document_id == "doc-1" for result in results)
    assert all(result.filename == "notes.txt" for result in results)


def test_query_similar_chunks_respects_limit(vector_store: VectorStoreService) -> None:
    chunks = [_make_chunk(i, f"chunk {i}") for i in range(5)]
    embeddings = [[float(i), 0.0] for i in range(5)]

    vector_store.upsert_chunks(
        document_id="doc-1",
        filename="notes.txt",
        chunks=chunks,
        embeddings=embeddings,
    )

    results = vector_store.query_similar_chunks([0.0, 0.0], limit=2)

    assert len(results) == 2


def test_query_similar_chunks_orders_nearest_first(
    vector_store: VectorStoreService,
) -> None:
    chunks = [_make_chunk(0, "far chunk"), _make_chunk(1, "near chunk")]
    # Chunk 1's embedding is identical to the query - it should come first.
    embeddings = [[10.0, 10.0], [1.0, 1.0]]

    vector_store.upsert_chunks(
        document_id="doc-1",
        filename="notes.txt",
        chunks=chunks,
        embeddings=embeddings,
    )

    results = vector_store.query_similar_chunks([1.0, 1.0], limit=2)

    assert results[0].text == "near chunk"
    assert results[0].distance < results[1].distance
