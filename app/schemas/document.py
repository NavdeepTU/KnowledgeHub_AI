from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class IngestionStatus(str, Enum):
    completed = "completed"
    failed = "failed"


class DocumentMetadata(BaseModel):
    """Format-intrinsic metadata pulled from the file itself.

    All fields are optional: plain-text formats (TXT, Markdown, HTML)
    have no metadata standard to extract from, and even formats that do
    (PDF, DOCX, PPTX) don't guarantee any field is actually set.
    """

    title: str | None = None
    author: str | None = None
    created_at: datetime | None = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    character_count: int
    chunk_count: int
    metadata: DocumentMetadata
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
    metadata: DocumentMetadata
    status: IngestionStatus
