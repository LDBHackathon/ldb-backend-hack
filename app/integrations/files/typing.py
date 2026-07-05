from typing import TypedDict


class UploadResponse(TypedDict):
    """Cloudinary upload response fields used by the app."""

    secure_url: str
    public_id: str
    width: int | None
    height: int | None
    format: str | None


class FileInformation(TypedDict):
    """Cloudinary resource metadata."""

    public_id: str
    url: str
    format: str
    resource_type: str
    file_size: int
    width: int | None
    height: int | None
    folder: str | None
    created_at: str
