from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.portal import PortalService


@pytest.mark.asyncio
async def test_dashboard_summary_aggregates() -> None:
    merchant_id = uuid4()
    merchant = AsyncMock()
    merchant.name = "WealthVault"

    customer = AsyncMock()
    customer.id = uuid4()
    customer.wallet_balance = Decimal("60000")
    customer.created_at = datetime.now(UTC)
    customer.name = "Ada"
    customer.target_amount = Decimal("100000")

    service = PortalService()
    with (
        patch(
            "app.services.portal.Merchant.get_or_none",
            new_callable=AsyncMock,
            return_value=merchant,
        ),
        patch(
            "app.services.portal.Customer.filter",
        ) as mock_customer_filter,
        patch(
            "app.services.portal.DedicatedAccount.filter",
        ) as mock_account_filter,
        patch(
            "app.services.portal.Transaction.filter",
        ) as mock_tx_filter,
    ):
        mock_customer_filter.return_value.all = AsyncMock(return_value=[customer])
        mock_account_filter.return_value.values_list = AsyncMock(return_value=[uuid4()])
        mock_tx_filter.return_value.all = AsyncMock(return_value=[])
        result = await service.dashboard_summary(merchant_id)

    assert result["status"] == "success"
    assert result["data"]["total_customers"] == 1
    assert result["data"]["total_deposits"] == Decimal("60000")
