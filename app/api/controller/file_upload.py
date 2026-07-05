"""Portal file upload controller."""

from typing import Annotated, Any

from fastapi import Depends, File, UploadFile

from app.api.security.portal_auth import ValidPortalMerchant
from app.services.file_upload import FileUploadService


async def upload_single_file(
    _merchant: ValidPortalMerchant,
    file: UploadFile,
    folder: str = "uploads/kyb",
    service: Annotated[FileUploadService, Depends()] = ...,
) -> dict[str, Any]:
    """Upload a single file to Cloudinary."""
    return await service.upload_single_file(file, folder)


async def upload_multiple_files(
    _merchant: ValidPortalMerchant,
    files: Annotated[list[UploadFile], File()],
    folder: str = "uploads/kyb",
    service: Annotated[FileUploadService, Depends()] = ...,
) -> dict[str, Any]:
    """Upload multiple files to Cloudinary."""
    return await service.upload_multiple_files(files, folder)


async def delete_file(
    _merchant: ValidPortalMerchant,
    public_id: str,
    service: Annotated[FileUploadService, Depends()] = ...,
) -> dict[str, Any]:
    """Delete a file from Cloudinary."""
    return await service.delete_file(public_id)


async def get_file_info(
    _merchant: ValidPortalMerchant,
    public_id: str,
    service: Annotated[FileUploadService, Depends()] = ...,
) -> dict[str, Any]:
    """Get information about a file from Cloudinary."""
    return await service.get_file_info(public_id)
