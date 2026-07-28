import logging

from app.schemas.document import DocumentChunk


logger = logging.getLogger(__name__)


class ChunkingService:
    def chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> list[DocumentChunk]:
        """
        Split text into overlapping, character-bounded chunks.

        Character-based chunking (not token-based) is deliberate: there's
        no embedding model wired up yet to make token counts meaningful,
        so this avoids a tokenizer dependency before it's actually needed.
        """
        if overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap_chars must be smaller than chunk_size_chars."
            )

        if not text:
            return []

        step = chunk_size - overlap
        chunks: list[DocumentChunk] = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]

            chunks.append(
                DocumentChunk(
                    chunk_index=len(chunks),
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    character_count=len(chunk_text),
                )
            )

            if end == len(text):
                break

            start += step

        logger.info(
            "Chunking completed | chunks=%s | chunk_size=%s | overlap=%s",
            len(chunks),
            chunk_size,
            overlap,
        )

        return chunks
