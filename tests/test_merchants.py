from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from app.enums.customer import CustomerStatus
from app.enums.merchant import MerchantStatus
from app.schemas.requests.customers import LinkNombaSubAccountRequestSchema
from app.schemas.requests.merchants import RegisterMerchantRequestSchema
from app.services.customers import CustomerService
from app.services.merchants import MerchantService
from app.utils.api_keys import hash_api_key
from app.utils.exceptions import ErrorResponse


@pytest.mark.asyncio
async def test_merchant_register_returns_api_key() -> None:
    service = MerchantService()
    body = RegisterMerchantRequestSchema(name="Acme Corp", email="ops@acme.example.com")

    merchant = AsyncMock()
    merchant.id = uuid4()
    merchant.name = body.name
    merchant.email = body.email
    merchant.status = MerchantStatus.ACTIVE
    merchant.created_at = AsyncMock()
    merchant.updated_at = AsyncMock()

    with (
        patch(
            "app.services.merchants.Merchant.filter",
        ) as mock_filter,
        patch(
            "app.services.merchants.Merchant.create",
            new_callable=AsyncMock,
            return_value=merchant,
        ),
        patch(
            "app.services.merchants.MerchantApiKey.create",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.merchants.generate_api_key",
            return_value="ldb_test_" + "a" * 64,
        ),
    ):
        mock_filter.return_value.exists = AsyncMock(return_value=False)
        result = await service.register(body)

    assert result["status"] == "success"
    assert result["status_code"] == 201
    assert result["data"]["api_key"].startswith("ldb_test_")


@pytest.mark.asyncio
async def test_merchant_register_duplicate_email() -> None:
    service = MerchantService()
    body = RegisterMerchantRequestSchema(name="Acme Corp", email="ops@acme.example.com")

    with patch(
        "app.services.merchants.Merchant.filter",
    ) as mock_filter:
        mock_filter.return_value.exists = AsyncMock(return_value=True)
        with pytest.raises(ErrorResponse) as exc_info:
            await service.register(body)

    assert exc_info.value.status == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_get_merchant_from_bearer_valid_key() -> None:
    from app.api.security.merchant_auth import get_merchant_from_bearer

    merchant_id = uuid4()
    api_key = AsyncMock()
    api_key.merchant = AsyncMock()
    api_key.merchant.id = merchant_id
    api_key.merchant.status = MerchantStatus.ACTIVE

    auth = AsyncMock()
    auth.credentials = "ldb_test_" + "b" * 64

    with patch(
        "app.api.security.merchant_auth.MerchantApiKey.filter",
    ) as mock_filter:
        mock_qs = mock_filter.return_value
        mock_qs.select_related.return_value.first = AsyncMock(return_value=api_key)
        result = await get_merchant_from_bearer(auth)

    assert result == merchant_id
    mock_filter.assert_called_once_with(
        key_prefix=auth.credentials[:16],
        key_hash=hash_api_key(auth.credentials),
        revoked_at__isnull=True,
    )


@pytest.mark.asyncio
async def test_get_merchant_from_bearer_invalid_key() -> None:
    from app.api.security.merchant_auth import get_merchant_from_bearer

    auth = AsyncMock()
    auth.credentials = "invalid-key"

    with patch(
        "app.api.security.merchant_auth.MerchantApiKey.filter",
    ) as mock_filter:
        mock_qs = mock_filter.return_value
        mock_qs.select_related.return_value.first = AsyncMock(return_value=None)
        with pytest.raises(ErrorResponse) as exc_info:
            await get_merchant_from_bearer(auth)

    assert exc_info.value.status == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_link_nomba_sub_account_provisions_va() -> None:
    merchant_id = uuid4()
    customer = AsyncMock()
    customer.id = uuid4()
    customer.name = "Link User"
    customer.status = CustomerStatus.PENDING_NOMBA
    customer.nomba_sub_account_id = None
    customer.nomba_sub_account_ref = None
    customer.target_amount = None
    customer.save = AsyncMock()

    service = CustomerService()
    body = LinkNombaSubAccountRequestSchema(
        nomba_sub_account_id="2242b79d-f2cf-4ccc-ada1-e890bd1a9f0d",
    )

    with (
        patch.object(
            service,
            "_resolve_customer",
            new_callable=AsyncMock,
            return_value=customer,
        ),
        patch(
            "app.services.customers.NombaSubAccountService.fetch_details",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "data": {
                    "account_id": body.nomba_sub_account_id,
                    "account_ref": "c" * 32,
                },
            },
        ),
        patch.object(
            service,
            "_provision_virtual_account",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "app.services.customers.build_customer_response",
            new_callable=AsyncMock,
            return_value={"status": CustomerStatus.ACTIVE},
        ),
    ):
        result = await service.link_nomba_sub_account(
            str(customer.id),
            body,
            merchant_id=merchant_id,
        )

    assert result["status"] == "success"
    assert customer.nomba_sub_account_id == body.nomba_sub_account_id
    customer.save.assert_awaited()
