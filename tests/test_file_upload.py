from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import UploadFile

from app.services.file_upload import FileUploadService
from app.utils.exceptions import ErrorResponse


def _upload_file(content: bytes, content_type: str, filename: str = "doc.pdf") -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


@pytest.mark.asyncio
async def test_upload_single_file_success() -> None:
    service = FileUploadService()
    file = _upload_file(b"pdf-content", "application/pdf", "cac.pdf")
    mock_result = {
        "secure_url": "https://res.cloudinary.com/demo/doc.pdf",
        "public_id": "uploads/kyb/uuid",
        "width": None,
        "height": None,
        "format": "pdf",
    }

    with patch(
        "app.services.file_upload.cloudinary_configured",
        return_value=True,
    ), patch(
        "app.services.file_upload.upload_file",
        return_value=mock_result,
    ):
        result = await service.upload_single_file(file)

    assert result["status_code"] == 201
    assert result["data"]["url"] == mock_result["secure_url"]
    assert result["data"]["public_id"] == mock_result["public_id"]
    assert result["data"]["original_filename"] == "cac.pdf"
    assert result["data"]["file_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_upload_single_file_rejects_disallowed_mime() -> None:
    service = FileUploadService()
    file = _upload_file(b"exe-content", "application/x-msdownload", "bad.exe")

    with patch("app.services.file_upload.cloudinary_configured", return_value=True):
        with pytest.raises(ErrorResponse) as exc_info:
            await service.upload_single_file(file)

    assert exc_info.value.status == 400
    assert "not allowed" in exc_info.value.message


@pytest.mark.asyncio
async def test_upload_single_file_rejects_oversized_file() -> None:
    service = FileUploadService()
    file = _upload_file(b"x" * (10 * 1024 * 1024 + 1), "application/pdf", "large.pdf")

    with patch("app.services.file_upload.cloudinary_configured", return_value=True):
        with pytest.raises(ErrorResponse) as exc_info:
            await service.upload_single_file(file)

    assert exc_info.value.status == 400
    assert "10MB" in exc_info.value.message


@pytest.mark.asyncio
async def test_upload_single_file_missing_cloudinary_config() -> None:
    service = FileUploadService()
    file = _upload_file(b"pdf-content", "application/pdf")

    with patch("app.services.file_upload.cloudinary_configured", return_value=False):
        with pytest.raises(ErrorResponse) as exc_info:
            await service.upload_single_file(file)

    assert exc_info.value.status == 503
    assert "CLOUDINARY" in exc_info.value.message


@pytest.mark.asyncio
async def test_upload_multiple_files_partial_success() -> None:
    service = FileUploadService()
    good = _upload_file(b"pdf-content", "application/pdf", "good.pdf")
    bad = _upload_file(b"exe-content", "application/x-msdownload", "bad.exe")

    mock_result = {
        "secure_url": "https://res.cloudinary.com/demo/good.pdf",
        "public_id": "uploads/kyb/good",
        "width": None,
        "height": None,
        "format": "pdf",
    }

    with patch(
        "app.services.file_upload.cloudinary_configured",
        return_value=True,
    ), patch(
        "app.services.file_upload.upload_file",
        return_value=mock_result,
    ):
        result = await service.upload_multiple_files([good, bad])

    assert result["status_code"] == 201
    assert result["data"]["uploaded_count"] == 1
    assert result["data"]["failed_count"] == 1
    assert result["data"]["failed_files"][0]["filename"] == "bad.exe"


@pytest.mark.asyncio
async def test_delete_file_success() -> None:
    service = FileUploadService()

    with patch(
        "app.services.file_upload.cloudinary_configured",
        return_value=True,
    ), patch(
        "app.services.file_upload.cloudinary_delete_file",
        return_value=True,
    ):
        result = await service.delete_file("uploads/kyb/test")

    assert result["status_code"] == 200
    assert result["data"]["public_id"] == "uploads/kyb/test"


@pytest.mark.asyncio
async def test_get_file_info_success() -> None:
    service = FileUploadService()
    file_info = {
        "public_id": "uploads/kyb/test",
        "url": "https://res.cloudinary.com/demo/test.pdf",
        "format": "pdf",
        "resource_type": "image",
        "file_size": 1234,
        "width": None,
        "height": None,
        "folder": "uploads/kyb",
        "created_at": "2026-01-01T00:00:00Z",
    }

    with patch(
        "app.services.file_upload.cloudinary_configured",
        return_value=True,
    ), patch(
        "app.services.file_upload.cloudinary_get_file_info",
        return_value=file_info,
    ):
        result = await service.get_file_info("uploads/kyb/test")

    assert result["status_code"] == 200
    assert result["data"] == file_info
