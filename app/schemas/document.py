from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, gt=0, le=50)


class SearchResult(BaseModel):
    """One chunk found to be similar to a search query.

    Carries enough to cite its source (document_id, filename, offsets)
    since that's the whole point of returning a chunk instead of just a
    raw similarity score. `citation` is the same offsets formatted as a
    human-readable reference, e.g. "notes.txt (chunk 0, characters 0-27)".
    """

    document_id: str
    filename: str
    chunk_index: int
    text: str
    start_offset: int
    end_offset: int
    distance: float
    citation: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, gt=0, le=50)
    # Omit to start a new conversation - the response returns the ID to
    # reuse for follow-up questions.
    conversation_id: str | None = None


class AskResponse(BaseModel):
    """The generated answer, plus the exact chunks it was grounded in.

    `sources` reuses SearchResult (including its `citation` field) so a
    caller can verify the answer against the same chunks the model saw,
    not just trust the generated text.
    """

    conversation_id: str
    question: str
    answer: str
    sources: list[SearchResult]


class ConversationTurn(BaseModel):
    """One question/answer pair from a past turn in a conversation.

    Only the question text and final answer are kept - not the retrieved
    chunks that grounded that answer - so replaying history into later
    Claude calls doesn't re-send every past turn's full context.
    """

    question: str
    answer: str


class ConversationRecord(BaseModel):
    """The full persisted history for one conversation."""

    conversation_id: str
    turns: list[ConversationTurn]


class AskStreamMeta(BaseModel):
    """First line of a `/documents/ask/stream` response - everything the
    client needs before any answer text arrives."""

    conversation_id: str
    sources: list[SearchResult]


class AskStreamDelta(BaseModel):
    """One incremental piece of the answer, as it's generated."""

    delta: str


class AskStreamError(BaseModel):
    """Terminal line if generation fails partway through streaming.

    Retrieval failures (embedding, vector store) still surface as a
    normal HTTP error before streaming starts - this only covers
    failures once the HTTP response has already begun, when the status
    code can no longer change.
    """

    error: str
