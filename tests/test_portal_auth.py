from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.enums.merchant import MerchantStatus
from app.enums.transaction import TransactionStatus
from app.services.auth import AuthService, OnboardingService
from app.services.helpers import derive_customer_flags, portal_customer_status, transaction_portal_flag
from app.schemas.requests.auth import LoginAuthRequestSchema, RegisterAuthRequestSchema
from app.utils.passwords import hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    raw = "secure-password-123"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed)
    assert not verify_password("wrong", hashed)


def test_derive_customer_flags_underpaid() -> None:
    customer = AsyncMock()
    customer.target_amount = Decimal("100000")
    customer.wallet_balance = Decimal("60000")
    flags = derive_customer_flags(customer)
    assert "Underpaid" in flags
    assert portal_customer_status(flags) == "Underpayment"


def test_derive_customer_flags_overpaid() -> None:
    customer = AsyncMock()
    customer.target_amount = Decimal("100000")
    customer.wallet_balance = Decimal("150000")
    flags = derive_customer_flags(customer)
    assert "Overpaid" in flags


def test_transaction_portal_flag_mapping() -> None:
    assert transaction_portal_flag(TransactionStatus.PARTIAL) == "Underpaid"
    assert transaction_portal_flag(TransactionStatus.MISDIRECTED) == "Misdirected"


@pytest.mark.asyncio
async def test_auth_register_and_login() -> None:
    auth = AuthService()
    email = f"merchant-{uuid4()}@example.com"
    register_body = RegisterAuthRequestSchema(
        full_name="Amara Olu",
        email=email,
        password="password123",
    )

    merchant = AsyncMock()
    merchant.id = uuid4()
    merchant.name = register_body.full_name
    merchant.email = email
    merchant.phone = None
    merchant.status = MerchantStatus.PENDING_KYB
    merchant.kyb_data = {}
    merchant.created_at = AsyncMock()
    merchant.updated_at = AsyncMock()

    with (
        patch("app.services.auth.Merchant.filter") as mock_filter,
        patch("app.services.auth.Merchant.create", new_callable=AsyncMock, return_value=merchant),
        patch("app.services.auth.MerchantApiKey.create", new_callable=AsyncMock),
        patch("app.services.auth.generate_api_key", return_value="ldb_test_" + "a" * 64),
    ):
        mock_filter.return_value.exists = AsyncMock(return_value=False)
        result = await auth.register(register_body)

    assert result["status_code"] == 201
    assert "api_key" in result["data"]

    merchant.password_hash = hash_password("password123")
    login_body = LoginAuthRequestSchema(email=email, password="password123")

    with patch(
        "app.services.auth.Merchant.get_or_none",
        new_callable=AsyncMock,
        return_value=merchant,
    ):
        login_result = await auth.login(login_body)

    assert login_result["status_code"] == 200


@pytest.mark.asyncio
async def test_onboarding_save_document() -> None:
    service = OnboardingService()
    merchant_id = uuid4()
    merchant = AsyncMock()
    merchant.id = merchant_id
    merchant.kyb_data = {}
    merchant.save = AsyncMock()

    upload_data = {
        "url": "https://res.cloudinary.com/demo/cac.pdf",
        "public_id": f"uploads/kyb/{merchant_id}/cac",
        "original_filename": "cac.pdf",
        "file_type": "application/pdf",
        "file_size": 1024,
    }

    with patch(
        "app.services.auth.Merchant.get_or_none",
        new_callable=AsyncMock,
        return_value=merchant,
    ):
        result = await service.save_document(
            merchant_id, "cac_certificate", upload_data
        )

    assert result["status_code"] == 201
    assert result["data"]["document"]["file_url"] == upload_data["url"]
    assert len(result["data"]["documents"]) == 1
    merchant.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_onboarding_submit_requires_steps() -> None:
    service = OnboardingService()
    merchant = AsyncMock()
    merchant.id = uuid4()
    merchant.kyb_data = {"business": {"business_name": "WealthVault"}}
    merchant.status = MerchantStatus.PENDING_KYB
    merchant.save = AsyncMock()

    with patch(
        "app.services.auth.Merchant.get_or_none",
        new_callable=AsyncMock,
        return_value=merchant,
    ):
        from app.utils.exceptions import ErrorResponse

        with pytest.raises(ErrorResponse):
            await service.submit(merchant.id)


@pytest.mark.asyncio
async def test_onboarding_submit_activates_merchant() -> None:
    service = OnboardingService()
    merchant = AsyncMock()
    merchant.id = uuid4()
    merchant.kyb_data = {
        "business": {"business_name": "WealthVault"},
        "address": {"address_line": "12 Marina"},
        "verification": {"director_name": "Amara", "consent": True},
    }
    merchant.status = MerchantStatus.PENDING_KYB
    merchant.save = AsyncMock()

    with patch(
        "app.services.auth.Merchant.get_or_none",
        new_callable=AsyncMock,
        return_value=merchant,
    ):
        result = await service.submit(merchant.id)

    assert result["status_code"] == 200
    assert result["message"] == "KYB completed — account activated"
    assert merchant.status == MerchantStatus.ACTIVE
    assert merchant.kyb_data["submitted_at"]
    assert merchant.kyb_data["approved_at"] == merchant.kyb_data["submitted_at"]
    merchant.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_onboarding_submit_rejects_when_already_active() -> None:
    service = OnboardingService()
    merchant = AsyncMock()
    merchant.id = uuid4()
    merchant.kyb_data = {
        "business": {"business_name": "WealthVault"},
        "address": {"address_line": "12 Marina"},
        "verification": {"director_name": "Amara", "consent": True},
        "submitted_at": "2026-01-01T00:00:00+00:00",
    }
    merchant.status = MerchantStatus.ACTIVE

    with patch(
        "app.services.auth.Merchant.get_or_none",
        new_callable=AsyncMock,
        return_value=merchant,
    ):
        from app.utils.exceptions import ErrorResponse

        with pytest.raises(ErrorResponse) as exc_info:
            await service.submit(merchant.id)

    assert exc_info.value.status == 422
    assert "already completed" in exc_info.value.message


@pytest.mark.asyncio
async def test_active_portal_merchant_blocks_pending_kyb() -> None:
    from fastapi import status

    from app.api.security.portal_auth import get_active_portal_merchant
    from app.utils.exceptions import ErrorResponse

    merchant_id = uuid4()
    merchant = AsyncMock()
    merchant.id = merchant_id
    merchant.status = MerchantStatus.PENDING_KYB

    with patch(
        "app.api.security.portal_auth.Merchant.get_or_none",
        new_callable=AsyncMock,
        return_value=merchant,
    ):
        with pytest.raises(ErrorResponse) as exc_info:
            await get_active_portal_merchant(merchant_id)

    assert exc_info.value.status == status.HTTP_403_FORBIDDEN
    assert "Complete KYB onboarding" in exc_info.value.message
