from pydantic import BaseModel, Field

from app.schemas.responses._commons import Decimal


class CreateCustomerRequestSchema(BaseModel):
    """Create customer and provision dedicated virtual account."""

    merchant_customer_id: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    email: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    target_amount: Decimal | None = Field(None, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)


class UpdateCustomerRequestSchema(BaseModel):
    """Update customer profile."""

    name: str | None = Field(None, max_length=200)
    email: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    target_amount: Decimal | None = Field(None, ge=0)
    metadata: dict[str, str] | None = None
