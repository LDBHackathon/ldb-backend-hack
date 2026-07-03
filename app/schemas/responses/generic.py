from typing import Literal

from pydantic import BaseModel


class SuccessResponseSchema[T](BaseModel):
    """Success response schema."""

    status: Literal["success"]
    status_code: int
    message: str
    data: T | None = None


class ErrorResponseSchema(BaseModel):
    """Error response schema."""

    status: Literal["failure"]
    status_code: int
    message: str


class ValidationErrorResponseSchema(BaseModel):
    """Validation error response schema."""

    status: Literal["failure"]
    status_code: int
    message: str
    errors: list[str] | None = None


class _PaginationMetadata(BaseModel):
    page: int
    pages: int
    limit: int
    total: int
    count: int


class PaginatedResponseSchema[T](BaseModel):
    """Paginated response schema."""

    status: Literal["success"]
    status_code: int
    message: str
    metadata: _PaginationMetadata
    data: list[T]
