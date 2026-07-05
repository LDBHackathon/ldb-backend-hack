from uuid import UUID

from pydantic import BaseModel, Field


class CreateDedicatedAccountRequestSchema(BaseModel):
    """Provision a dedicated virtual account for an existing customer."""

    customer_id: UUID
    account_name: str | None = Field(None, min_length=8, max_length=64)
