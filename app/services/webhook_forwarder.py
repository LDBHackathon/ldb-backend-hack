import hashlib
import hmac
import json
from typing import Any
from uuid import UUID

import httpx

from app.constants import (
    OUTBOUND_EVENT_ACCOUNT_CREATED,
    OUTBOUND_EVENT_PAYMENT_MISDIRECTED,
    OUTBOUND_EVENT_PAYMENT_PARTIAL,
    OUTBOUND_EVENT_PAYMENT_RECEIVED,
    OUTBOUND_EVENT_RECONCILIATION_FLAGGED,
    OUTBOUND_EVENT_TRANSFER_RECEIVED,
    OUTBOUND_EVENT_WALLET_CREDITED,
    OUTBOUND_EVENTS_ALL,
)
from app.models.customers import Customer, DedicatedAccount
from app.models.transactions import Transaction, WebhookRegistration
from app.enums.transaction import TransactionStatus
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.helpers import _outstanding_balance
from app.utils.logger import logger
from app.utils.response_formatter import success_response
from fastapi import status
from uuid import uuid4


class WebhookForwarderService:
    """Register and deliver enriched merchant webhooks."""

    async def register(
        self, body: RegisterWebhookRequestSchema, merchant_id: UUID
    ) -> dict[str, Any]:
        registration = await WebhookRegistration.create(
            id=uuid4(),
            merchant_id=merchant_id,
            url=body.url,
            secret=body.secret,
            events=body.events or OUTBOUND_EVENTS_ALL,
        )
        return success_response(
            status.HTTP_201_CREATED,
            "Webhook registered",
            data={
                "id": str(registration.id),
                "url": registration.url,
                "events": registration.events,
                "active": registration.active,
            },
        )

    async def emit_payment_received(
        self,
        *,
        merchant_id: UUID,
        customer: Customer,
        account: DedicatedAccount,
        transaction: Transaction,
    ) -> None:
        event_map = self._events_for_transaction(transaction)
        payload_data = self._payment_payload(customer, account, transaction)
        for event in event_map:
            await self._deliver(merchant_id, event, payload_data)

    async def emit_account_created(
        self,
        *,
        merchant_id: UUID,
        customer: Customer,
        account: DedicatedAccount,
    ) -> None:
        payload = {
            "customerId": customer.merchant_customer_id,
            "customerName": customer.name,
            "accountNumber": account.account_number,
            "accountRef": account.account_ref,
        }
        await self._deliver(merchant_id, OUTBOUND_EVENT_ACCOUNT_CREATED, payload)

    async def emit_test_event(self, merchant_id: UUID) -> bool:
        payload = {
            "customerId": "demo-customer",
            "customerName": "Demo Customer",
            "accountNumber": "0123456789",
            "amountReceived": "60000",
            "walletBalance": "60000",
            "targetAmount": "100000",
            "status": "partial",
            "outstandingBalance": "40000",
            "transactionRef": "TXN-DEMO-TEST",
            "senderName": "Demo Sender",
            "senderBank": "GTBank",
        }
        return await self._deliver(
            merchant_id,
            OUTBOUND_EVENT_WALLET_CREDITED,
            payload,
        )

    def _events_for_transaction(self, transaction: Transaction) -> list[str]:
        events = [OUTBOUND_EVENT_PAYMENT_RECEIVED, OUTBOUND_EVENT_WALLET_CREDITED]
        if transaction.status == TransactionStatus.PARTIAL:
            events.extend(
                [OUTBOUND_EVENT_PAYMENT_PARTIAL, OUTBOUND_EVENT_RECONCILIATION_FLAGGED]
            )
        elif transaction.status == TransactionStatus.OVERPAYMENT:
            events.append(OUTBOUND_EVENT_RECONCILIATION_FLAGGED)
        elif transaction.status == TransactionStatus.MISDIRECTED:
            events.append(OUTBOUND_EVENT_PAYMENT_MISDIRECTED)
        else:
            events.append(OUTBOUND_EVENT_TRANSFER_RECEIVED)
        return events

    def _payment_payload(
        self,
        customer: Customer,
        account: DedicatedAccount,
        transaction: Transaction,
    ) -> dict[str, Any]:
        outstanding = _outstanding_balance(customer)
        return {
            "customerId": customer.merchant_customer_id,
            "customerName": customer.name,
            "accountNumber": account.account_number,
            "amountReceived": str(transaction.amount),
            "walletBalance": str(customer.wallet_balance),
            "targetAmount": (
                str(customer.target_amount) if customer.target_amount else None
            ),
            "status": transaction.status.value,
            "outstandingBalance": str(outstanding) if outstanding is not None else None,
            "transactionRef": transaction.merchant_tx_ref,
            "senderName": transaction.sender_name,
            "senderBank": transaction.sender_bank,
        }

    async def _deliver(
        self,
        merchant_id: UUID,
        event: str,
        data: dict[str, Any],
    ) -> bool:
        registrations = await WebhookRegistration.filter(
            merchant_id=merchant_id,
            active=True,
        )
        if not registrations:
            return False

        payload = {"event": event, "data": data}
        body = json.dumps(payload, separators=(",", ":")).encode()
        delivered = False

        for registration in registrations:
            subscribed = set(registration.events)
            legacy_payment = OUTBOUND_EVENT_PAYMENT_RECEIVED in subscribed
            if event not in subscribed and not (
                legacy_payment
                and event
                in {
                    OUTBOUND_EVENT_WALLET_CREDITED,
                    OUTBOUND_EVENT_PAYMENT_RECEIVED,
                    OUTBOUND_EVENT_TRANSFER_RECEIVED,
                }
            ):
                continue
            signature = hmac.new(
                registration.secret.encode(),
                body,
                hashlib.sha256,
            ).hexdigest()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        registration.url,
                        content=body,
                        headers={
                            "Content-Type": "application/json",
                            "X-LDB-Signature": signature,
                        },
                    )
                    logger.info(
                        "Outbound webhook delivered",
                        url=registration.url,
                        event=event,
                        status_code=response.status_code,
                    )
                    delivered = True
            except httpx.HTTPError as exc:
                logger.warning(
                    "Outbound webhook delivery failed",
                    url=registration.url,
                    event=event,
                    error=str(exc),
                )
        return delivered
