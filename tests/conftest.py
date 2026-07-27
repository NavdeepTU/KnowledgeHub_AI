import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.core.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def isolated_upload_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect uploads to a throwaway directory so tests never touch the real uploads/ folder."""
    monkeypatch.setattr(settings, "upload_directory", tmp_path)
    return tmp_path


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def valid_pdf_bytes() -> bytes:
    """A minimal, single-page, unencrypted PDF built at test time."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture()
def encrypted_pdf_bytes() -> bytes:
    """A minimal PDF protected with a user password."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt(user_password="secret")

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture()
def corrupted_pdf_bytes() -> bytes:
    """Bytes with a valid PDF signature but no parsable structure."""
    return b"%PDF-1.4\n" + b"this is not a real pdf body" * 20
