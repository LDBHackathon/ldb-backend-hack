import hashlib
import hmac
import json
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import status

from app.constants import OUTBOUND_EVENT_PAYMENT_RECEIVED
from app.models.customers import Customer, DedicatedAccount
from app.models.transactions import Transaction, WebhookRegistration
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.helpers import _outstanding_balance
from app.utils.logger import logger
from app.utils.response_formatter import success_response


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
            events=body.events,
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
        registrations = await WebhookRegistration.filter(
            merchant_id=merchant_id,
            active=True,
        )
        if not registrations:
            return

        outstanding = _outstanding_balance(customer)
        payload = {
            "event": OUTBOUND_EVENT_PAYMENT_RECEIVED,
            "data": {
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
            },
        }

        body = json.dumps(payload, separators=(",", ":")).encode()
        for registration in registrations:
            if OUTBOUND_EVENT_PAYMENT_RECEIVED not in registration.events:
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
                        status_code=response.status_code,
                    )
            except httpx.HTTPError as exc:
                logger.warning(
                    "Outbound webhook delivery failed",
                    url=registration.url,
                    error=str(exc),
                )
