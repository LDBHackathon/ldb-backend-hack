from typing import Any

import cloudinary  # type: ignore[import-untyped]
import cloudinary.api  # type: ignore[import-untyped]
import cloudinary.uploader  # type: ignore[import-untyped]

from app.settings import settings

from .typing import FileInformation, UploadResponse

_configured = False


def cloudinary_configured() -> bool:
    """Return True when all Cloudinary credentials are set."""
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


def configure_cloudinary() -> None:
    """Configure the Cloudinary SDK from application settings."""
    global _configured  # noqa: PLW0603
    if _configured:
        return
    cloudinary.config(  # type: ignore[no-untyped-call]
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    _configured = True


def upload_file(
    file_content: bytes, folder: str, unique_filename: str
) -> UploadResponse:
    """Upload a file to Cloudinary."""
    configure_cloudinary()
    return cloudinary.uploader.upload(  # type: ignore[no-untyped-call]
        file_content,
        folder=folder,
        public_id=unique_filename,
        resource_type="auto",
        use_filename=True,
        unique_filename=False,
    )


def get_file_info(public_id: str) -> FileInformation:
    """Get file information from Cloudinary."""
    configure_cloudinary()
    response: Any = cloudinary.api.resource(public_id)  # type: ignore[no-untyped-call]

    return {
        "public_id": response["public_id"],
        "url": response["secure_url"],
        "format": response["format"],
        "resource_type": response["resource_type"],
        "file_size": response["bytes"],
        "width": response.get("width"),
        "height": response.get("height"),
        "folder": response.get("folder"),
        "created_at": response["created_at"],
    }


def delete_file(public_id: str) -> bool:
    """Delete a file from Cloudinary."""
    configure_cloudinary()
    response = cloudinary.uploader.destroy(public_id)  # type: ignore[no-untyped-call]

    return response.get("result") == "ok"
