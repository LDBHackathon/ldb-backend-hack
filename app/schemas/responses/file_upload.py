from pydantic import BaseModel


class UploadFileResponse(BaseModel):
    """Single file upload response."""

    url: str
    public_id: str
    original_filename: str | None
    file_type: str | None
    file_size: int
    width: int | None
    height: int | None
    format: str | None


class _ErrorUpload(BaseModel):
    filename: str
    error: str


class MultipleUploadFileResponse(BaseModel):
    """Multiple file upload response."""

    uploaded_files: list[UploadFileResponse] = []
    uploaded_count: int = 0
    total_count: int = 0
    failed_files: list[_ErrorUpload] = []
    failed_count: int = 0


class FilePublicResponse(BaseModel):
    """File delete response."""

    public_id: str


class FileInformationResponse(BaseModel):
    """File metadata response."""

    public_id: str
    url: str
    format: str
    resource_type: str
    file_size: int
    width: int | None
    height: int | None
    folder: str | None
    created_at: str
