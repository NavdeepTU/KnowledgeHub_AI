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
