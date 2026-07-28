import logging
from pathlib import Path

import chromadb

from app.schemas.document import DocumentChunk, SearchResult


logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(
        self,
        persist_directory: Path,
        collection_name: str = "documents",
    ) -> None:
        # PersistentClient is a local, embedded store - no server process,
        # matching the project's pattern of avoiding new infrastructure
        # until it's actually needed.
        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._collection = self._client.get_or_create_collection(collection_name)

    def upsert_chunks(
        self,
        document_id: str,
        filename: str,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Store each chunk's embedding, text, and locating metadata in the
        vector store, keyed so it can be traced back to its document.
        """
        if not chunks:
            return

        ids = [f"{document_id}:{chunk.chunk_index}" for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk.chunk_index,
                "start_offset": chunk.start_offset,
                "end_offset": chunk.end_offset,
            }
            for chunk in chunks
        ]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            "Chunks upserted into vector store | document_id=%s | count=%s",
            document_id,
            len(chunks),
        )

    def query_similar_chunks(
        self,
        query_embedding: list[float],
        limit: int,
    ) -> list[SearchResult]:
        """
        Return the chunks most similar to a query embedding, nearest
        first. Safe to call on an empty vector store (returns an empty
        list) or with a limit larger than the number of stored chunks
        (Chroma caps it automatically) - both verified directly.
        """
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
        )

        texts = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        return [
            SearchResult(
                document_id=metadata["document_id"],
                filename=metadata["filename"],
                chunk_index=metadata["chunk_index"],
                text=text,
                start_offset=metadata["start_offset"],
                end_offset=metadata["end_offset"],
                distance=distance,
            )
            for text, metadata, distance in zip(texts, metadatas, distances)
        ]
