from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.enums.customer import CustomerStatus
from app.schemas.requests.customers import CreateCustomerRequestSchema
from app.services.customers import CustomerService
from app.utils.exceptions import ErrorResponse


@pytest.mark.asyncio
async def test_dva_provisioning_persists_account() -> None:
    merchant_id = uuid4()
    body = CreateCustomerRequestSchema(
        name="Ada Okonkwo",
        target_amount=Decimal("100000"),
    )
    service = CustomerService()

    created_customer = AsyncMock()
    created_customer.id = uuid4()
    created_customer.merchant_customer_id = "generated-customer-ref"
    created_customer.name = body.name
    created_customer.email = None
    created_customer.phone = None
    created_customer.target_amount = body.target_amount
    created_customer.wallet_balance = Decimal("0")
    created_customer.metadata = {}
    created_customer.nomba_sub_account_id = "sub-acct-1"
    created_customer.nomba_sub_account_ref = "a" * 32
    created_customer.status = CustomerStatus.PENDING_NOMBA
    created_customer.save = AsyncMock()

    with (
        patch(
            "app.services.customers.generate_merchant_customer_id",
            return_value="generated-customer-ref",
        ),
        patch(
            "app.services.customers.Customer.create",
            new_callable=AsyncMock,
            return_value=created_customer,
        ),
        patch(
            "app.services.customers.NombaSubAccountService.create",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "data": {"account_id": "sub-acct-1", "account_ref": "a" * 32},
            },
        ),
        patch(
            "app.services.customers.NombaVirtualAccountService.create",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "data": {
                    "account_number": "0123456789",
                    "nomba_va_id": "nomba-va-1",
                    "account_ref": "a" * 32,
                },
            },
        ),
        patch(
            "app.services.customers.DedicatedAccount.create",
            new_callable=AsyncMock,
        ) as mock_create_account,
        patch(
            "app.services.customers.DedicatedAccount.filter",
        ) as mock_filter,
        patch(
            "app.services.customers.build_customer_response",
            new_callable=AsyncMock,
            return_value={"merchant_customer_id": "generated-customer-ref"},
        ),
    ):
        mock_filter.return_value.first = AsyncMock(return_value=None)
        result = await service.create(body, merchant_id=merchant_id)

    assert result["status"] == "success"
    assert result["status_code"] == 201
    mock_create_account.assert_awaited_once()


@pytest.mark.asyncio
async def test_dva_provisioning_sub_account_failure_returns_pending() -> None:
    merchant_id = uuid4()
    body = CreateCustomerRequestSchema(name="Pending User")
    service = CustomerService()

    created_customer = AsyncMock()
    created_customer.id = uuid4()
    created_customer.status = CustomerStatus.PENDING_NOMBA
    created_customer.delete = AsyncMock()

    with (
        patch(
            "app.services.customers.generate_merchant_customer_id",
            return_value="generated-customer-ref",
        ),
        patch(
            "app.services.customers.Customer.create",
            new_callable=AsyncMock,
            return_value=created_customer,
        ),
        patch(
            "app.services.customers.NombaSubAccountService.create",
            new_callable=AsyncMock,
            return_value={"success": False, "message": "Forbidden", "status_code": 403},
        ),
        patch(
            "app.services.customers.build_customer_response",
            new_callable=AsyncMock,
            return_value={"status": CustomerStatus.PENDING_NOMBA},
        ),
    ):
        result = await service.create(body, merchant_id=merchant_id)

    assert result["status"] == "success"
    assert result["status_code"] == 201
    created_customer.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_dva_provisioning_va_failure_keeps_customer_pending() -> None:
    merchant_id = uuid4()
    body = CreateCustomerRequestSchema(name="Failed User")
    service = CustomerService()
    created_customer = AsyncMock()
    created_customer.nomba_sub_account_id = "sub-acct-1"
    created_customer.save = AsyncMock()
    created_customer.delete = AsyncMock()

    with (
        patch(
            "app.services.customers.generate_merchant_customer_id",
            return_value="generated-customer-ref",
        ),
        patch(
            "app.services.customers.Customer.create",
            new_callable=AsyncMock,
            return_value=created_customer,
        ),
        patch(
            "app.services.customers.NombaSubAccountService.create",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "data": {"account_id": "sub-acct-1"},
            },
        ),
        patch(
            "app.services.customers.NombaVirtualAccountService.create",
            new_callable=AsyncMock,
            return_value={"success": False, "message": "Nomba down"},
        ),
        patch(
            "app.services.customers.DedicatedAccount.filter",
        ) as mock_filter,
        patch(
            "app.services.customers.build_customer_response",
            new_callable=AsyncMock,
            return_value={"status": CustomerStatus.PENDING_NOMBA},
        ),
    ):
        mock_filter.return_value.first = AsyncMock(return_value=None)
        result = await service.create(body, merchant_id=merchant_id)

    assert result["status"] == "success"
    assert result["status_code"] == 201
    created_customer.delete.assert_not_awaited()
