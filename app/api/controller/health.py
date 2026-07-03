from typing import Any

from fastapi import status

from app.utils.response_formatter import success_response


async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return success_response(status.HTTP_200_OK, "Service is healthy", data={"service": "ldb-dva"})
