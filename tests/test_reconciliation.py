from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.enums.account import AccountStatus
from app.enums.transaction import TransactionStatus
from app.services.helpers import derive_transaction_status
from app.services.reconciliation import ReconciliationService


def test_derive_transaction_status_full() -> None:
    assert derive_transaction_status(Decimal("100000"), Decimal("100000")) == TransactionStatus.FULL


def test_derive_transaction_status_partial() -> None:
    assert derive_transaction_status(Decimal("60000"), Decimal("100000")) == TransactionStatus.PARTIAL


def test_derive_transaction_status_overpayment() -> None:
    assert derive_transaction_status(Decimal("150000"), Decimal("100000")) == TransactionStatus.OVERPAYMENT


@pytest.mark.asyncio
async def test_reconciliation_full_payment() -> None:
    customer = AsyncMock()
    customer.id = uuid4()
    customer.merchant_id = uuid4()
    customer.merchant_customer_id = "cust-1"
    customer.name = "Test User"
    customer.target_amount = Decimal("100000")
    customer.wallet_balance = Decimal("0")
    customer.save = AsyncMock()

    account = AsyncMock()
    account.id = uuid4()
    account.customer = customer
    account.account_number = "0123456789"
    account.account_ref = "cust-1"
    account.status = AccountStatus.ACTIVE
    account.fetch_related = AsyncMock()
    transaction = AsyncMock()
    transaction.id = uuid4()

    service = ReconciliationService()
    service._forwarder.emit_payment_received = AsyncMock()

    with (
        patch(
            "app.services.reconciliation.DedicatedAccount.get_or_none",
            new_callable=AsyncMock,
            return_value=account,
        ),
        patch(
            "app.services.reconciliation.Transaction.create",
            new_callable=AsyncMock,
            return_value=transaction,
        ),
        patch(
            "app.services.reconciliation.ReconciliationLog.create",
            new_callable=AsyncMock,
        ),
    ):
        result = await service.process_payment(
            request_id="req-1",
            event_type="payment_success",
            raw_payload={
                "data": {
                    "transaction": {
                        "aliasAccountNumber": "0123456789",
                        "aliasAccountReference": "cust-1",
                        "transactionAmount": 100000,
                        "fee": 0,
                        "transactionId": "tx-1",
                        "merchantTxRef": "ref-1",
                    },
                    "customer": {"senderName": "Sender", "bankName": "GTBank"},
                }
            },
        )

    assert result["quarantined"] is False
    assert result["status"] == TransactionStatus.FULL
    assert customer.wallet_balance == Decimal("100000")


@pytest.mark.asyncio
async def test_reconciliation_misdirected() -> None:
    transaction = AsyncMock()
    transaction.id = uuid4()
    service = ReconciliationService()

    with (
        patch(
            "app.services.reconciliation.DedicatedAccount.get_or_none",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.reconciliation.Transaction.create",
            new_callable=AsyncMock,
            return_value=transaction,
        ),
        patch(
            "app.services.reconciliation.SuspenseLog.create",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.reconciliation.ReconciliationLog.create",
            new_callable=AsyncMock,
        ),
    ):
        result = await service.process_payment(
            request_id="req-2",
            event_type="payment_success",
            raw_payload={
                "data": {
                    "transaction": {
                        "aliasAccountNumber": "9999999999",
                        "transactionAmount": 5000,
                        "fee": 0,
                    },
                    "customer": {},
                }
            },
        )

    assert result["quarantined"] is True
    assert result["status"] == TransactionStatus.MISDIRECTED


@pytest.mark.asyncio
async def test_webhook_idempotency() -> None:
    from app.services.webhooks import NombaWebhookService

    service = NombaWebhookService()
    with patch(
        "app.services.webhooks.ProcessedWebhookEvent.filter",
    ) as mock_filter:
        mock_filter.return_value.exists = AsyncMock(return_value=True)
        result = await service.receive(
            {"event_type": "payment_success", "requestId": "dup-1", "data": {}}
        )

    assert result["status"] == "success"
    assert result["message"] == "Webhook already processed"
