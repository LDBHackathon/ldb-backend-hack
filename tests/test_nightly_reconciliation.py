from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.jobs.nightly_reconciliation import run_nightly_reconciliation


@pytest.mark.asyncio
async def test_nightly_reconciliation_per_sub_account() -> None:
    customers = [
        AsyncMock(nomba_sub_account_id="sub-1"),
        AsyncMock(nomba_sub_account_id="sub-2"),
    ]

    with (
        patch(
            "app.jobs.nightly_reconciliation.Customer.filter",
        ) as mock_filter,
        patch(
            "app.jobs.nightly_reconciliation.NombaTransactionService.list_transactions",
            new_callable=AsyncMock,
            return_value={"success": True, "data": []},
        ) as mock_list,
        patch(
            "app.jobs.nightly_reconciliation._reconcile_nomba_items",
            new_callable=AsyncMock,
            return_value=(0, 0),
        ),
    ):
        mock_filter.return_value.all = AsyncMock(return_value=customers)
        await run_nightly_reconciliation()

    assert mock_list.await_count == 2
    called_sub_accounts = {
        call.kwargs["sub_account_id"] for call in mock_list.await_args_list
    }
    assert called_sub_accounts == {"sub-1", "sub-2"}
