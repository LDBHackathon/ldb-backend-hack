from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.enums.transaction import TransactionStatus
from app.schemas.requests.filter import PaginateFilterRequestSchema
from app.services.statements import StatementService


@pytest.mark.asyncio
async def test_statement_aggregation() -> None:
    merchant_id = uuid4()
    customer = AsyncMock()
    customer.merchant_id = merchant_id
    customer.merchant_customer_id = "cust-1"
    customer.name = "Test User"
    customer.target_amount = Decimal("100000")
    customer.wallet_balance = Decimal("60000")

    account = AsyncMock()
    account.id = uuid4()
    account.customer = customer
    account.account_number = "0123456789"
    account.fetch_related = AsyncMock()

    tx1 = AsyncMock()
    tx1.id = uuid4()
    tx1.amount = Decimal("60000")
    tx1.status = TransactionStatus.PARTIAL
    tx1.sender_name = "Sender"
    tx1.sender_bank = "GTBank"
    tx1.merchant_tx_ref = "ref-1"
    tx1.narration = "Transfer"
    tx1.created_at = datetime.now(UTC)

    service = StatementService()

    with (
        patch(
            "app.services.statements.DedicatedAccount.get_or_none",
            new_callable=AsyncMock,
            return_value=account,
        ),
        patch(
            "app.services.statements.Transaction.filter",
        ) as mock_filter,
    ):
        mock_filter.return_value.order_by = AsyncMock(return_value=[tx1])
        result = await service.get_statement(account.id, merchant_id)

    assert result["status"] == "success"
    data = result["data"]
    assert data["total_received"] == Decimal("60000")
    assert data["flagged_short_payments"] == 1
    assert data["outstanding_balance"] == Decimal("40000")


@pytest.mark.asyncio
async def test_list_transactions_pagination() -> None:
    merchant_id = uuid4()
    customer = AsyncMock()
    customer.merchant_id = merchant_id

    account = AsyncMock()
    account.id = uuid4()
    account.customer = customer
    account.fetch_related = AsyncMock()

    service = StatementService()
    with (
        patch(
            "app.services.statements.DedicatedAccount.get_or_none",
            new_callable=AsyncMock,
            return_value=account,
        ),
        patch(
            "app.services.statements.Transaction.filter",
        ) as mock_filter,
    ):
        query = mock_filter.return_value.order_by.return_value
        query.count = AsyncMock(return_value=0)
        query.offset.return_value.limit = AsyncMock(return_value=[])

        result = await service.list_transactions(
            account.id,
            merchant_id,
            PaginateFilterRequestSchema(page=1, limit=20),
        )

    assert result["status"] == "success"
    assert result["metadata"]["total"] == 0
    assert result["metadata"]["page"] == 1
