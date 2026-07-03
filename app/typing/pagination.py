from typing import TypedDict


class PaginationMetadata(TypedDict):
    """Pagination metadata."""

    page: int
    pages: int
    limit: int
    total: int
    count: int
