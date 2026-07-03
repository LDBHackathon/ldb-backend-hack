from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.enums.transaction import TransactionStatus, TransactionType
from app.schemas.responses._commons import Decimal


class TransactionResponse(BaseModel):
    """Inbound transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dedicated_account_id: UUID | None = None
    nomba_request_id: str
    nomba_transaction_id: str | None = None
    merchant_tx_ref: str | None = None
    amount: Decimal
    fee: Decimal
    sender_name: str | None = None
    sender_bank: str | None = None
    type: TransactionType
    status: TransactionStatus
    narration: str | None = None
    created_at: datetime
