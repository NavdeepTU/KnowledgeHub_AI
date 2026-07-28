import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.services.vector_store_service import VectorStoreService
from tests.fakes import FakeGroqClient


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
    # The blank test PDF has no extractable text, so there's nothing to chunk.
    assert body["chunk_count"] == 0


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
    assert record["chunks"] == []


def test_upload_persists_chunks_for_long_text(
    client: TestClient,
    isolated_upload_directory: Path,
) -> None:
    content = ("word " * 1000).encode("utf-8")  # 5000 characters

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )

    document_id = response.json()["document_id"]
    assert response.json()["chunk_count"] > 1

    sidecar_path = isolated_upload_directory / f"{document_id}.json"
    record = json.loads(sidecar_path.read_text())

    chunks = record["chunks"]
    assert len(chunks) == response.json()["chunk_count"]
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    # Concatenating each chunk minus its overlap with the previous one
    # should reconstruct the original text exactly.
    reconstructed = chunks[0]["text"]
    for previous, current in zip(chunks, chunks[1:]):
        overlap_len = previous["end_offset"] - current["start_offset"]
        reconstructed += current["text"][overlap_len:]
    assert reconstructed == content.decode("utf-8")


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


def test_upload_accepts_html_file(client: TestClient) -> None:
    content = b"<html><body><h1>Title</h1><p>Some paragraph text.</p></body></html>"

    response = client.post(
        "/documents/upload",
        files={"file": ("page.html", content, "text/html")},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["filename"] == "page.html"
    assert body["page_count"] == 1
    assert body["character_count"] > 0
    assert body["status"] == "completed"


def test_upload_strips_script_and_style_from_html(
    client: TestClient,
    isolated_upload_directory: Path,
) -> None:
    content = (
        b"<html><head><style>body { color: red; }</style>"
        b"<script>alert('should not appear');</script></head>"
        b"<body><p>Visible paragraph text.</p></body></html>"
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("page.html", content, "text/html")},
    )

    document_id = response.json()["document_id"]
    sidecar_path = isolated_upload_directory / f"{document_id}.json"
    record = json.loads(sidecar_path.read_text())

    assert "Visible paragraph text." in record["extracted_text"]
    assert "should not appear" not in record["extracted_text"]
    assert "color: red" not in record["extracted_text"]


def test_upload_rejects_non_utf8_html_file(client: TestClient) -> None:
    invalid_utf8 = b"\xff\xfe\x00\x01<html>not valid utf-8</html>"

    response = client.post(
        "/documents/upload",
        files={"file": ("page.html", invalid_utf8, "text/html")},
    )

    assert response.status_code == 422
    assert "UTF-8" in response.json()["detail"]


def test_upload_extracts_pdf_metadata(client: TestClient, valid_pdf_bytes: bytes) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("document.pdf", valid_pdf_bytes, "application/pdf")},
    )

    metadata = response.json()["metadata"]
    assert metadata["title"] == "PDF Test Title"
    assert metadata["author"] == "PDF Test Author"
    # Not set in the fixture, so it should come back empty rather than a
    # fabricated value.
    assert metadata["created_at"] is None


def test_upload_extracts_docx_metadata(client: TestClient, valid_docx_bytes: bytes) -> None:
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

    metadata = response.json()["metadata"]
    assert metadata["title"] == "DOCX Test Title"
    assert metadata["author"] == "DOCX Test Author"
    # python-docx's default template always has a creation timestamp,
    # even for documents that never set one explicitly.
    assert metadata["created_at"] is not None


def test_upload_extracts_pptx_metadata(client: TestClient, valid_pptx_bytes: bytes) -> None:
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

    metadata = response.json()["metadata"]
    assert metadata["title"] == "PPTX Test Title"
    assert metadata["author"] == "PPTX Test Author"
    assert metadata["created_at"] is not None


def test_upload_txt_has_no_metadata(client: TestClient) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"plain text has no metadata", "text/plain")},
    )

    assert response.json()["metadata"] == {
        "title": None,
        "author": None,
        "created_at": None,
    }


def test_upload_stores_chunks_in_vector_store(
    client: TestClient,
    isolated_vector_services: VectorStoreService,
) -> None:
    content = ("word " * 1000).encode("utf-8")  # 5000 characters, multiple chunks

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )

    document_id = response.json()["document_id"]
    chunk_count = response.json()["chunk_count"]
    assert chunk_count > 1

    expected_ids = [f"{document_id}:{i}" for i in range(chunk_count)]
    result = isolated_vector_services._collection.get(ids=expected_ids)

    assert set(result["ids"]) == set(expected_ids)
    assert all(metadata["filename"] == "notes.txt" for metadata in result["metadatas"])


def test_upload_failure_does_not_store_chunks_in_vector_store(
    client: TestClient,
    encrypted_pdf_bytes: bytes,
    isolated_vector_services: VectorStoreService,
) -> None:
    client.post(
        "/documents/upload",
        files={"file": ("document.pdf", encrypted_pdf_bytes, "application/pdf")},
    )

    assert isolated_vector_services._collection.count() == 0


def test_search_returns_results_from_uploaded_document(client: TestClient) -> None:
    client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"knowledge base search test", "text/plain")},
    )

    response = client.post("/documents/search", json={"query": "search test"})

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "search test"
    assert len(body["results"]) == 1

    result = body["results"][0]
    assert result["filename"] == "notes.txt"
    assert result["text"] == "knowledge base search test"
    assert "distance" in result
    assert result["citation"] == "notes.txt (chunk 0, characters 0-26)"


def test_search_respects_limit(client: TestClient) -> None:
    content = ("word " * 1000).encode("utf-8")  # multiple chunks

    client.post(
        "/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )

    response = client.post(
        "/documents/search", json={"query": "word", "limit": 1}
    )

    assert len(response.json()["results"]) == 1


def test_search_on_empty_vector_store_returns_no_results(client: TestClient) -> None:
    response = client.post("/documents/search", json={"query": "anything"})

    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_rejects_empty_query(client: TestClient) -> None:
    response = client.post("/documents/search", json={"query": ""})

    assert response.status_code == 422


def test_search_rejects_limit_out_of_range(client: TestClient) -> None:
    response = client.post(
        "/documents/search", json={"query": "test", "limit": 100}
    )

    assert response.status_code == 422


def test_ask_returns_answer_grounded_in_uploaded_document(
    client: TestClient, isolated_answer_service: FakeGroqClient
) -> None:
    client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"knowledge base search test", "text/plain")},
    )

    response = client.post("/documents/ask", json={"question": "search test"})

    assert response.status_code == 200

    body = response.json()
    assert body["question"] == "search test"
    assert body["answer"] == "This is a fake answer. [1]"
    assert len(body["sources"]) == 1
    assert body["sources"][0]["text"] == "knowledge base search test"
    assert body["conversation_id"]


def test_ask_on_empty_vector_store_skips_the_model_call(
    client: TestClient, isolated_answer_service: FakeGroqClient
) -> None:
    response = client.post("/documents/ask", json={"question": "anything"})

    assert response.status_code == 200

    body = response.json()
    assert body["sources"] == []
    assert "don't have any relevant documents" in body["answer"].lower()
    assert isolated_answer_service.last_call is None


def test_ask_without_conversation_id_starts_a_new_conversation_each_time(
    client: TestClient,
) -> None:
    first = client.post("/documents/ask", json={"question": "one"})
    second = client.post("/documents/ask", json={"question": "two"})

    assert first.json()["conversation_id"] != second.json()["conversation_id"]


def test_ask_with_conversation_id_replays_history_to_the_model(
    client: TestClient, isolated_answer_service: FakeGroqClient
) -> None:
    client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"knowledge base search test", "text/plain")},
    )

    first = client.post("/documents/ask", json={"question": "search test"})
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/documents/ask",
        json={"question": "follow up", "conversation_id": conversation_id},
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id

    messages = isolated_answer_service.last_call["messages"]
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "search test"}
    assert messages[2] == {"role": "assistant", "content": "This is a fake answer. [1]"}
    assert "follow up" in messages[3]["content"]


def test_ask_with_unknown_conversation_id_still_answers(client: TestClient) -> None:
    response = client.post(
        "/documents/ask",
        json={"question": "anything", "conversation_id": "does-not-exist-yet"},
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "does-not-exist-yet"


def test_ask_rejects_empty_question(client: TestClient) -> None:
    response = client.post("/documents/ask", json={"question": ""})

    assert response.status_code == 422


def test_ask_rejects_limit_out_of_range(client: TestClient) -> None:
    response = client.post(
        "/documents/ask", json={"question": "test", "limit": 100}
    )

    assert response.status_code == 422
