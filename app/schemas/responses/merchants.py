from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.enums.merchant import MerchantStatus


class MerchantResponse(BaseModel):
    """Merchant profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    status: MerchantStatus
    created_at: datetime
    updated_at: datetime


class RegisterMerchantResponse(BaseModel):
    """Merchant registration response including one-time API key."""

    merchant: MerchantResponse
    api_key: str
