import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.document import DocumentUploadResponse, IngestionStatus
from app.services.document_service import DocumentService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

document_service = DocumentService()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload and process a PDF document.

    Current flow:
    1. Validate filename and file type.
    2. Read the file into memory.
    3. Validate its size and PDF signature.
    4. Save it locally.
    5. Extract text.
    6. Return processing details.
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

    # Validate the extension separately from the MIME type.
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(
            "Upload rejected because extension is invalid | filename=%s",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only files with a .pdf extension are supported.",
        )

    # MIME type is useful but cannot be fully trusted because it is
    # supplied by the client.
    if file.content_type != "application/pdf":
        logger.warning(
            "Upload rejected because MIME type is invalid | content_type=%s",
            file.content_type,
        )

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported.",
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

    # Real PDF files normally begin with the bytes %PDF.
    # This check prevents renamed text or image files from being accepted.
    if not content.startswith(b"%PDF"):
        logger.warning(
            "Upload rejected because PDF signature is missing | filename=%s",
            file.filename,
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded file does not appear to be a valid PDF.",
        )

    # Reset the internal file pointer because the file has already been read.
    await file.seek(0)

    saved_path: Path | None = None

    try:
        saved_path = await document_service.save_pdf(
            file=file,
            upload_directory=settings.upload_directory,
        )

        extracted_text, page_count = document_service.extract_text(
            saved_path,
        )

        logger.info(
            "Upload completed successfully | document_id=%s | filename=%s",
            saved_path.stem,
            file.filename,
        )

        return DocumentUploadResponse(
            document_id=saved_path.stem,
            filename=file.filename,
            page_count=page_count,
            character_count=len(extracted_text),
            status=IngestionStatus.completed,
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
            detail="An unexpected error occurred while processing the PDF.",
        ) from exc
