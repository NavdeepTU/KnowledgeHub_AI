import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.schemas.document import DocumentRecord


logger = logging.getLogger(__name__)


class DocumentService:
    async def save_pdf(
        self,
        file: UploadFile,
        upload_directory: Path,
    ) -> Path:
        """
        Save the uploaded PDF using a generated ID.

        We do not use the original filename because:
        - multiple users may upload files with the same name,
        - filenames may contain unsafe characters,
        - generated IDs make documents easier to track.
        """
        document_id = str(uuid4())
        destination = upload_directory / f"{document_id}.pdf"

        content = await file.read()
        destination.write_bytes(content)

        logger.info(
            "File saved successfully | document_id=%s | path=%s",
            document_id,
            destination,
        )

        return destination

    def extract_text(self, file_path: Path) -> tuple[str, int]:
        """
        Extract text from every page of the PDF.

        Returns:
            A tuple containing:
            - combined text from all pages,
            - total number of pages.
        """
        try:
            reader = PdfReader(file_path)

            # Encrypted PDFs require special handling.
            # For now, we reject them instead of attempting decryption.
            if reader.is_encrypted:
                raise ValueError("Encrypted PDF files are not supported.")

            page_texts: list[str] = []

            for page_number, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                page_texts.append(page_text)

                logger.info(
                    "Page processed | page_number=%s | characters=%s",
                    page_number,
                    len(page_text),
                )

            extracted_text = "\n\n".join(page_texts)

            logger.info(
                "Text extraction completed | pages=%s | characters=%s",
                len(reader.pages),
                len(extracted_text),
            )

            return extracted_text, len(reader.pages)

        except PdfReadError as exc:
            logger.exception("PDF parsing failed | path=%s", file_path)
            raise ValueError("The uploaded file is not a readable PDF.") from exc

    def persist_metadata(
        self,
        record: DocumentRecord,
        upload_directory: Path,
    ) -> Path:
        """
        Persist a document's extracted text and metadata as a JSON sidecar
        file next to its saved PDF, named after the same document ID.
        """
        destination = upload_directory / f"{record.document_id}.json"
        destination.write_text(record.model_dump_json(indent=2))

        logger.info(
            "Metadata persisted | document_id=%s | path=%s",
            record.document_id,
            destination,
        )

        return destination
