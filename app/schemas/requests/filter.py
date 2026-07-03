from pydantic import BaseModel, Field

from app.schemas.responses._commons import Decimal


class PaginateFilterRequestSchema(BaseModel):
    """Pagination query parameters."""

    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class SimulateFundingRequestSchema(BaseModel):
    """Simulate an inbound bank transfer for demo/testing."""

    account_number: str = Field(..., max_length=20)
    amount: Decimal = Field(..., gt=0)
    sender_name: str = Field(default="Demo Sender", max_length=200)
    sender_bank: str = Field(default="GTBank", max_length=100)
    misdirected: bool = Field(default=False)
