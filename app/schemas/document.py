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
