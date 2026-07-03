from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.requests.customers import CreateCustomerRequestSchema
from app.services.customers import CustomerService
from app.utils.exceptions import ErrorResponse


@pytest.mark.asyncio
async def test_dva_provisioning_persists_account() -> None:
    merchant_id = uuid4()
    body = CreateCustomerRequestSchema(
        merchant_customer_id="cust-99",
        name="Ada Okonkwo",
        target_amount=Decimal("100000"),
    )
    service = CustomerService()

    created_customer = AsyncMock()
    created_customer.id = uuid4()
    created_customer.merchant_customer_id = body.merchant_customer_id
    created_customer.name = body.name
    created_customer.email = None
    created_customer.phone = None
    created_customer.target_amount = body.target_amount
    created_customer.wallet_balance = Decimal("0")
    created_customer.metadata = {}
    created_customer.created_at = AsyncMock()
    created_customer.updated_at = AsyncMock()

    with (
        patch(
            "app.services.customers.Customer.get_or_none",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.customers.DedicatedAccount.filter",
        ) as mock_account_filter,
        patch(
            "app.services.customers.Customer.create",
            new_callable=AsyncMock,
            return_value=created_customer,
        ),
        patch(
            "app.services.customers.NombaVirtualAccountService.create",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "data": {"accountNumber": "0123456789", "id": "nomba-va-1"},
            },
        ),
        patch(
            "app.services.customers.DedicatedAccount.create",
            new_callable=AsyncMock,
        ) as mock_create_account,
        patch(
            "app.services.customers.build_customer_response",
            new_callable=AsyncMock,
            return_value={"merchant_customer_id": "cust-99"},
        ),
    ):
        mock_account_filter.return_value.first = AsyncMock(return_value=None)
        result = await service.create(body, merchant_id=merchant_id)

    assert result["status"] == "success"
    assert result["status_code"] == 201
    mock_create_account.assert_awaited_once()


@pytest.mark.asyncio
async def test_dva_provisioning_nomba_failure_rolls_back() -> None:
    merchant_id = uuid4()
    body = CreateCustomerRequestSchema(
        merchant_customer_id="cust-100",
        name="Failed User",
    )
    service = CustomerService()
    created_customer = AsyncMock()
    created_customer.delete = AsyncMock()

    with (
        patch(
            "app.services.customers.Customer.get_or_none",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.customers.DedicatedAccount.filter",
        ) as mock_account_filter,
        patch(
            "app.services.customers.Customer.create",
            new_callable=AsyncMock,
            return_value=created_customer,
        ),
        patch(
            "app.services.customers.NombaVirtualAccountService.create",
            new_callable=AsyncMock,
            return_value={"success": False, "message": "Nomba down"},
        ),
    ):
        mock_account_filter.return_value.first = AsyncMock(return_value=None)
        with pytest.raises(ErrorResponse) as exc_info:
            await service.create(body, merchant_id=merchant_id)

    assert exc_info.value.status == 502
    created_customer.delete.assert_awaited_once()
