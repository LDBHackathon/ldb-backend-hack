from pydantic import BaseModel, Field


class CreateDedicatedAccountRequestSchema(BaseModel):
    """Provision a dedicated virtual account for an existing customer."""

    merchant_customer_id: str = Field(..., max_length=100)
    account_name: str | None = Field(None, max_length=200)
