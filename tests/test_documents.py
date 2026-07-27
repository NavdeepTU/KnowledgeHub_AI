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


def test_upload_rejects_invalid_extension(client: TestClient, valid_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.txt", valid_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 415
    assert "extension" in response.json()["detail"]


def test_upload_rejects_invalid_mime_type(client: TestClient, valid_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", valid_pdf_bytes, "text/plain")},
    )

    assert response.status_code == 415
    assert "PDF" in response.json()["detail"]


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
    assert "valid PDF" in response.json()["detail"]


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
