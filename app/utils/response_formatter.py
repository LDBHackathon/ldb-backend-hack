from typing import Any

from app.utils.exceptions import ErrorResponse
from app.typing.pagination import PaginationMetadata

__all__ = [
    "error_response",
    "paginated_success_response",
    "success_response",
]


def success_response(
    status_code: int,
    message: str,
    data: Any = None,  # noqa: ANN401
) -> dict[str, Any]:
    """Return a standard success envelope."""
    return {
        "status": "success",
        "status_code": status_code,
        "message": message,
        "data": data,
    }


def paginated_success_response(
    status_code: int, message: str, metadata: PaginationMetadata, data: list[Any]
) -> dict[str, Any]:
    """Return a standard paginated success envelope."""
    return {
        "status": "success",
        "status_code": status_code,
        "message": message,
        "metadata": metadata,
        "data": data,
    }


def error_response(
    status_code: int, message: str, errors: list[str] | None = None
) -> dict[str, Any]:
    """Raise a standard failure envelope."""
    raise ErrorResponse(status_code, message, errors)
