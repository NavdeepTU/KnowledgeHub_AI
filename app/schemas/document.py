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
    status: IngestionStatus


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
    status: IngestionStatus
