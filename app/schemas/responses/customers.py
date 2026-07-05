from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.account import AccountStatus
from app.enums.customer import CustomerStatus
from app.schemas.responses._commons import Decimal


class DedicatedAccountSummary(BaseModel):
    """Embedded dedicated account summary."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_number: str
    account_name: str
    bank_name: str = "Nomba"
    status: AccountStatus


class CustomerResponse(BaseModel):
    """Customer profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_customer_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    target_amount: Decimal | None = None
    wallet_balance: Decimal
    outstanding_balance: Decimal | None = None
    progress_percentage: float | None = None
    status: CustomerStatus
    funding_status: str | None = None
    nomba_sub_account_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    dedicated_account: DedicatedAccountSummary | None = None
    created_at: datetime
    updated_at: datetime
