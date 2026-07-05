from pydantic import BaseModel, Field

from app.schemas.responses._commons import Decimal


class CreateCustomerRequestSchema(BaseModel):
    """Create customer and provision dedicated virtual account."""

    name: str = Field(..., min_length=8, max_length=64)
    email: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    target_amount: Decimal | None = Field(None, ge=0)
    bvn: str | None = Field(None, min_length=11, max_length=11)
    metadata: dict[str, str] = Field(default_factory=dict)


class UpdateCustomerRequestSchema(BaseModel):
    """Update customer profile."""

    name: str | None = Field(None, min_length=8, max_length=64)
    email: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    target_amount: Decimal | None = Field(None, ge=0)
    metadata: dict[str, str] | None = None


class LinkNombaSubAccountRequestSchema(BaseModel):
    """Link a dashboard-created Nomba sub-account to a customer."""

    nomba_sub_account_id: str = Field(..., min_length=36, max_length=36)
