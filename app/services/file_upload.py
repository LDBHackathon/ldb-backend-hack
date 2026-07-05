import os
import uuid
from typing import Any

from fastapi import UploadFile, status

from app.integrations.files.cloudinary import (
    cloudinary_configured,
    delete_file as cloudinary_delete_file,
    get_file_info as cloudinary_get_file_info,
    upload_file,
)
from app.utils.exceptions import ErrorResponse
from app.utils.logger import logger
from app.utils.response_formatter import error_response, success_response

DEFAULT_ALLOWED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
]

MAX_FILE_SIZE = 10 * 1024 * 1024


class FileUploadService:
    """Upload and manage files in Cloudinary."""

    def _ensure_cloudinary_configured(self) -> None:
        if not cloudinary_configured():
            error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "File upload is not configured. Set CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.",
            )

    async def upload_single_file(
        self,
        file: UploadFile,
        folder: str = "uploads/kyb",
        allowed_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload a single file to Cloudinary."""
        self._ensure_cloudinary_configured()

        if allowed_types is None:
            allowed_types = DEFAULT_ALLOWED_TYPES

        logger.info(
            "File upload requested",
            file_type=file.content_type,
            folder=folder,
        )

        if file.content_type not in allowed_types:
            logger.warning(
                "File upload rejected due to file type",
                file_type=file.content_type,
                folder=folder,
            )
            error_response(
                status.HTTP_400_BAD_REQUEST,
                f"File type {file.content_type} not allowed. "
                f"Allowed types: {', '.join(allowed_types)}",
            )

        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            logger.warning(
                "File upload rejected due to size",
                file_size=len(file_content),
                folder=folder,
            )
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "File size exceeds 10MB limit",
            )

        file_extension = os.path.splitext(file.filename or "")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        try:
            upload_result = upload_file(file_content, folder, unique_filename)
        except Exception as exc:
            logger.exception("File upload failed", folder=folder)
            error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Failed to upload file: {exc}",
            )

        logger.info(
            "File uploaded successfully",
            folder=folder,
            file_type=file.content_type,
            file_size=len(file_content),
        )

        return success_response(
            status.HTTP_201_CREATED,
            "File uploaded successfully",
            data={
                "url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
                "original_filename": file.filename,
                "file_type": file.content_type,
                "file_size": len(file_content),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "format": upload_result.get("format"),
            },
        )

    async def upload_multiple_files(
        self,
        files: list[UploadFile],
        folder: str = "uploads/kyb",
        allowed_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload multiple files to Cloudinary."""
        self._ensure_cloudinary_configured()

        logger.info(
            "Multiple file upload requested",
            files_count=len(files),
            folder=folder,
        )

        if not files:
            error_response(status.HTTP_400_BAD_REQUEST, "No files provided")

        if len(files) > 10:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Maximum 10 files allowed per request",
            )

        uploaded_files: list[dict[str, Any]] = []
        failed_files: list[dict[str, str]] = []

        for upload in files:
            try:
                result = await self.upload_single_file(upload, folder, allowed_types)
                uploaded_files.append(result["data"])
            except ErrorResponse as exc:
                failed_files.append(
                    {"filename": str(upload.filename), "error": exc.message}
                )

        if not uploaded_files and failed_files:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "All file uploads failed",
                errors=[f"{item['filename']}: {item['error']}" for item in failed_files],
            )

        response_data: dict[str, Any] = {
            "uploaded_files": uploaded_files,
            "uploaded_count": len(uploaded_files),
            "total_count": len(files),
        }

        if failed_files:
            response_data["failed_files"] = failed_files
            response_data["failed_count"] = len(failed_files)

        message = (
            f"Successfully uploaded {len(uploaded_files)} out of {len(files)} files"
        )
        if failed_files:
            message += f". {len(failed_files)} files failed to upload"

        return success_response(
            status.HTTP_201_CREATED if uploaded_files else status.HTTP_400_BAD_REQUEST,
            message,
            data=response_data,
        )

    async def delete_file(self, public_id: str) -> dict[str, Any]:
        """Delete a file from Cloudinary."""
        self._ensure_cloudinary_configured()

        try:
            success = cloudinary_delete_file(public_id)
        except Exception as exc:
            logger.exception("File delete failed", public_id=public_id)
            error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Failed to delete file: {exc}",
            )

        if success:
            logger.info("File deleted", public_id=public_id)
            return success_response(
                status.HTTP_200_OK,
                "File deleted successfully",
                data={"public_id": public_id},
            )

        logger.warning("File delete missed", public_id=public_id)
        error_response(
            status.HTTP_404_NOT_FOUND,
            "File not found or already deleted",
        )

    async def get_file_info(self, public_id: str) -> dict[str, Any]:
        """Get information about a file from Cloudinary."""
        self._ensure_cloudinary_configured()

        try:
            file_data = cloudinary_get_file_info(public_id)
        except Exception as exc:
            logger.exception("File info lookup failed", public_id=public_id)
            error_response(status.HTTP_404_NOT_FOUND, f"File not found: {exc}")

        logger.info("File info retrieved", public_id=public_id)
        return success_response(
            status.HTTP_200_OK,
            "File information retrieved successfully",
            data=file_data,
        )
