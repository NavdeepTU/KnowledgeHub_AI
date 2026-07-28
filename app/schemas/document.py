from enum import Enum

from pydantic import BaseModel


class IngestionStatus(str, Enum):
    completed = "completed"
    failed = "failed"


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    character_count: int
    chunk_count: int
    status: IngestionStatus


class DocumentChunk(BaseModel):
    """A size-bounded slice of a document's extracted text.

    start_offset/end_offset point back into the original extracted_text,
    kept now because they're free to compute during chunking and will be
    needed for citations once retrieval exists.
    """

    chunk_index: int
    text: str
    start_offset: int
    end_offset: int
    character_count: int


class DocumentRecord(BaseModel):
    """The full persisted record for a document, including its extracted text.

    Kept separate from DocumentUploadResponse so the API response contract
    doesn't grow to include the full extracted text.
    """

    document_id: str
    filename: str
    page_count: int
    character_count: int
    extracted_text: str
    chunks: list[DocumentChunk]
    status: IngestionStatus
