import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_valid_pdf_succeeds(client: TestClient, valid_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", valid_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "document.pdf"
    assert body["page_count"] == 1
    assert body["status"] == "completed"
    assert body["document_id"]


def test_upload_persists_metadata_sidecar(
    client: TestClient,
    valid_pdf_bytes: bytes,
    isolated_upload_directory: Path,
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", valid_pdf_bytes, "application/pdf")},
    )

    document_id = response.json()["document_id"]
    sidecar_path = isolated_upload_directory / f"{document_id}.json"
    assert sidecar_path.exists()

    record = json.loads(sidecar_path.read_text())
    assert record["document_id"] == document_id
    assert record["filename"] == "document.pdf"
    assert record["page_count"] == 1
    assert record["status"] == "completed"
    assert record["character_count"] == len(record["extracted_text"])


def test_upload_failure_does_not_persist_metadata(
    client: TestClient,
    encrypted_pdf_bytes: bytes,
    isolated_upload_directory: Path,
) -> None:
    client.post(
        "/documents/upload",
        files={"file": ("document.pdf", encrypted_pdf_bytes, "application/pdf")},
    )

    assert list(isolated_upload_directory.glob("*.json")) == []


def test_upload_rejects_invalid_extension(client: TestClient, valid_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.exe", valid_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 415
    assert "extension" in response.json()["detail"]


def test_upload_rejects_invalid_mime_type(client: TestClient, valid_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", valid_pdf_bytes, "text/plain")},
    )

    assert response.status_code == 415
    assert "pdf" in response.json()["detail"].lower()


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_upload_rejects_fake_pdf_signature(client: TestClient) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert "valid .pdf file" in response.json()["detail"]


def test_upload_rejects_corrupted_pdf(client: TestClient, corrupted_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", corrupted_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 422


def test_upload_rejects_encrypted_pdf(client: TestClient, encrypted_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", encrypted_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 422
    assert "Encrypted" in response.json()["detail"]


def test_upload_accepts_txt_file(client: TestClient) -> None:
    content = b"Plain text notes for a knowledge base."

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["page_count"] == 1
    assert body["character_count"] == len(content)
    assert body["status"] == "completed"


def test_upload_accepts_markdown_file(client: TestClient) -> None:
    content = b"# Heading\n\nSome **markdown** content."

    response = client.post(
        "/documents/upload",
        files={"file": ("readme.md", content, "text/markdown")},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "readme.md"
    assert body["page_count"] == 1
    assert body["character_count"] == len(content)
    assert body["status"] == "completed"


def test_upload_rejects_non_utf8_text_file(client: TestClient) -> None:
    invalid_utf8 = b"\xff\xfe\x00\x01not valid utf-8"

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", invalid_utf8, "text/plain")},
    )

    assert response.status_code == 422
    assert "UTF-8" in response.json()["detail"]


def test_upload_accepts_docx_file(client: TestClient, valid_docx_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "report.docx",
                valid_docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "report.docx"
    assert body["page_count"] == 1
    assert body["character_count"] > 0
    assert body["status"] == "completed"


def test_upload_rejects_docx_missing_zip_signature(
    client: TestClient, valid_docx_bytes: bytes
) -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "report.docx",
                b"not a real docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 422
    assert "valid .docx file" in response.json()["detail"]


def test_upload_rejects_corrupted_docx(
    client: TestClient, corrupted_docx_bytes: bytes
) -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "report.docx",
                corrupted_docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 422


def test_upload_accepts_pptx_file(client: TestClient, valid_pptx_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "deck.pptx",
                valid_pptx_bytes,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "deck.pptx"
    # Unlike DOCX/TXT/MD, PPTX page_count reflects the real slide count.
    assert body["page_count"] == 2
    assert body["character_count"] > 0
    assert body["status"] == "completed"


def test_upload_rejects_pptx_missing_zip_signature(
    client: TestClient, valid_pptx_bytes: bytes
) -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "deck.pptx",
                b"not a real pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )

    assert response.status_code == 422
    assert "valid .pptx file" in response.json()["detail"]


def test_upload_rejects_corrupted_pptx(
    client: TestClient, corrupted_pptx_bytes: bytes
) -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "deck.pptx",
                corrupted_pptx_bytes,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )

    assert response.status_code == 422
