from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.account import AccountStatus
from app.schemas.responses._commons import Decimal


class AccountResponse(BaseModel):
    """Dedicated virtual account response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    merchant_customer_id: str
    nomba_va_id: str | None = None
    account_number: str
    account_name: str
    account_ref: str
    bank_name: str = "Nomba"
    status: AccountStatus
    wallet_balance: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class StatementTransactionItem(BaseModel):
    """Single transaction line on a customer statement."""

    id: UUID
    amount: Decimal
    status: str
    sender_name: str | None = None
    sender_bank: str | None = None
    merchant_tx_ref: str | None = None
    narration: str | None = None
    created_at: datetime


class StatementResponse(BaseModel):
    """Aggregated customer/account statement."""

    account_id: UUID
    merchant_customer_id: str
    customer_name: str
    account_number: str
    target_amount: Decimal | None = None
    total_received: Decimal
    wallet_balance: Decimal
    outstanding_balance: Decimal
    flagged_short_payments: int
    status: str
    transactions: list[StatementTransactionItem]
