import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.document import DocumentRecord, DocumentUploadResponse, IngestionStatus
from app.services.chunking_service import ChunkingService
from app.services.document_service import SUPPORTED_FORMATS, DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

document_service = DocumentService()
chunking_service = ChunkingService()
embedding_service = EmbeddingService(api_key=settings.openai_api_key)
vector_store_service = VectorStoreService(
    persist_directory=settings.chroma_persist_directory,
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload and process a document.

    Current flow:
    1. Validate filename and file type against the supported formats.
    2. Read the file into memory.
    3. Validate its size and (where the format defines one) its signature.
    4. Save it locally.
    5. Extract text.
    6. Split the extracted text into overlapping chunks.
    7. Embed each chunk and store the vectors for retrieval.
    8. Extract format-intrinsic metadata (title, author, creation date).
    9. Persist extracted text, chunks, and metadata.
    10. Return processing details.
    """
    logger.info(
        "Upload request received | filename=%s | content_type=%s",
        file.filename,
        file.content_type,
    )

    # A missing filename usually means the upload request is malformed.
    if not file.filename:
        logger.warning("Upload rejected because filename is missing")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    # Validate the extension against the set of formats we know how to
    # handle before looking at anything else about the file.
    extension = Path(file.filename).suffix.lower()
    document_format = SUPPORTED_FORMATS.get(extension)

    if document_format is None:
        logger.warning(
            "Upload rejected because extension is unsupported | filename=%s",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Unsupported file extension. Supported extensions: "
                f"{', '.join(sorted(SUPPORTED_FORMATS))}."
            ),
        )

    # MIME type is useful but cannot be fully trusted because it is
    # supplied by the client.
    if file.content_type not in document_format.allowed_content_types:
        logger.warning(
            "Upload rejected because MIME type is invalid | content_type=%s",
            file.content_type,
        )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported content type for {extension} uploads. "
                f"Expected one of: {', '.join(sorted(document_format.allowed_content_types))}."
            ),
        )

    # The current implementation reads the full file into memory.
    # This is acceptable for our small first version, but later we will
    # replace it with streamed file handling.
    content = await file.read()

    if not content:
        logger.warning(
            "Upload rejected because file is empty | filename=%s",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    if len(content) > max_size_bytes:
        logger.warning(
            "Upload rejected because file is too large | filename=%s | size=%s",
            file.filename,
            len(content),
        )

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File must be smaller than "
                f"{settings.max_upload_size_mb} MB."
            ),
        )

    # Only some formats have magic bytes reliable enough to check (PDF
    # does; plain text formats don't, so this is skipped for them).
    if document_format.signature is not None and not content.startswith(
        document_format.signature
    ):
        logger.warning(
            "Upload rejected because file signature is invalid | filename=%s",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"The uploaded file does not appear to be a valid {extension} file.",
        )

    # Reset the internal file pointer because the file has already been read.
    await file.seek(0)

    saved_path: Path | None = None

    try:
        saved_path = await document_service.save_document(
            file=file,
            upload_directory=settings.upload_directory,
            extension=extension,
        )

        extracted_text, page_count = document_service.extract_text(
            saved_path,
        )

        chunks = chunking_service.chunk_text(
            extracted_text,
            chunk_size=settings.chunk_size_chars,
            overlap=settings.chunk_overlap_chars,
        )

        # Unlike metadata extraction, embedding failures are not treated
        # as best-effort: making a document searchable is the actual
        # point of this step, so a failure here (bad API key, no
        # billing, rate limit) should surface as a real upload failure
        # rather than silently producing a document nothing can find.
        embeddings = embedding_service.embed_texts(
            [chunk.text for chunk in chunks],
            model=settings.embedding_model,
        )

        vector_store_service.upsert_chunks(
            document_id=saved_path.stem,
            filename=file.filename,
            chunks=chunks,
            embeddings=embeddings,
        )

        metadata = document_service.extract_metadata(saved_path)

        record = DocumentRecord(
            document_id=saved_path.stem,
            filename=file.filename,
            page_count=page_count,
            character_count=len(extracted_text),
            extracted_text=extracted_text,
            chunks=chunks,
            metadata=metadata,
            status=IngestionStatus.completed,
        )

        document_service.persist_metadata(
            record=record,
            upload_directory=settings.upload_directory,
        )

        logger.info(
            "Upload completed successfully | document_id=%s | filename=%s | chunks=%s",
            record.document_id,
            file.filename,
            len(record.chunks),
        )

        return DocumentUploadResponse(
            document_id=record.document_id,
            filename=record.filename,
            page_count=record.page_count,
            character_count=record.character_count,
            chunk_count=len(record.chunks),
            metadata=record.metadata,
            status=record.status,
        )

    except ValueError as exc:
        logger.warning(
            "Document processing failed | filename=%s | reason=%s",
            file.filename,
            str(exc),
        )

        # Remove the saved file when processing fails so that invalid
        # or partial files do not remain in storage.
        if saved_path and saved_path.exists():
            saved_path.unlink()
            logger.info(
                "Failed upload removed | path=%s",
                saved_path,
            )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected upload failure | filename=%s",
            file.filename,
        )

        if saved_path and saved_path.exists():
            saved_path.unlink()
            logger.info(
                "Failed upload removed | path=%s",
                saved_path,
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the file.",
        ) from exc
