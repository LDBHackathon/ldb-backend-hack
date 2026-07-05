import math
from typing import Any
from uuid import UUID, uuid4

from fastapi import status

from app.constants import NOMBA_PAYMENT_SUCCESS_EVENT, NOMBA_VACT_TRANSFER_TYPE
from app.models.customers import DedicatedAccount
from app.models.transactions import ProcessedWebhookEvent, Transaction
from app.schemas.requests.filter import PaginateFilterRequestSchema, SimulateFundingRequestSchema
from app.services.reconciliation import ReconciliationService
from app.utils.logger import logger
from app.utils.references import generate_reference
from app.utils.response_formatter import error_response, success_response


class NombaWebhookService:
    """Inbound Nomba webhook processing."""

    def __init__(self) -> None:
        self._reconciliation = ReconciliationService()

    async def receive(self, payload: dict[str, Any]) -> dict[str, Any]:
        event_type = payload.get("event_type") or payload.get("eventType")
        request_id = payload.get("requestId") or payload.get("request_id")
        if not request_id:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                "Webhook missing requestId",
            )

        if await ProcessedWebhookEvent.filter(request_id=request_id).exists():
            logger.info("Duplicate webhook skipped", request_id=request_id)
            return success_response(
                status.HTTP_200_OK,
                "Webhook already processed",
            )

        if event_type != NOMBA_PAYMENT_SUCCESS_EVENT:
            await ProcessedWebhookEvent.create(
                id=uuid4(),
                request_id=request_id,
                event_type=str(event_type),
            )
            return success_response(
                status.HTTP_200_OK,
                "Webhook event ignored",
            )

        transaction_data = payload.get("data", {}).get("transaction", {})
        if transaction_data.get("type") != NOMBA_VACT_TRANSFER_TYPE:
            await ProcessedWebhookEvent.create(
                id=uuid4(),
                request_id=request_id,
                event_type=str(event_type),
            )
            return success_response(
                status.HTTP_200_OK,
                "Non virtual-account transfer ignored",
            )

        result = await self._reconciliation.process_payment(
            request_id=request_id,
            event_type=str(event_type),
            raw_payload=payload,
        )

        await ProcessedWebhookEvent.create(
            id=uuid4(),
            request_id=request_id,
            event_type=str(event_type),
        )

        return success_response(
            status.HTTP_200_OK,
            "Payment reconciled" if not result["quarantined"] else "Payment quarantined",
            data={
                "transactionId": str(result["transaction_id"]),
                "status": result["status"].value
                if hasattr(result["status"], "value")
                else result["status"],
                "walletBalance": (
                    str(result["wallet_balance"])
                    if result["wallet_balance"] is not None
                    else None
                ),
                "quarantined": result["quarantined"],
            },
        )

    async def simulate(self, body: SimulateFundingRequestSchema) -> dict[str, Any]:
        account_number = body.account_number.replace(" ", "")
        account = await DedicatedAccount.get_or_none(account_number=account_number)

        if body.misdirected or account is None:
            payload = self._build_nomba_payload(
                request_id=generate_reference(),
                account_number="0000000000",
                account_ref="invalid-ref-0000000001",
                amount=body.amount,
                sender_name=body.sender_name,
                sender_bank=body.sender_bank,
            )
        else:
            payload = self._build_nomba_payload(
                request_id=generate_reference(),
                account_number=account.account_number,
                account_ref=account.account_ref,
                amount=body.amount,
                sender_name=body.sender_name,
                sender_bank=body.sender_bank,
            )

        return await self.receive(payload)

    @staticmethod
    def _build_nomba_payload(
        *,
        request_id: str,
        account_number: str,
        account_ref: str,
        amount: Any,
        sender_name: str,
        sender_bank: str,
    ) -> dict[str, Any]:
        return {
            "event_type": NOMBA_PAYMENT_SUCCESS_EVENT,
            "requestId": request_id,
            "data": {
                "transaction": {
                    "aliasAccountNumber": account_number,
                    "aliasAccountReference": account_ref,
                    "transactionAmount": float(amount),
                    "fee": 0,
                    "type": NOMBA_VACT_TRANSFER_TYPE,
                    "transactionId": f"SIM-{request_id}",
                    "merchantTxRef": request_id,
                    "narration": "Simulated transfer",
                },
                "customer": {
                    "senderName": sender_name,
                    "bankName": sender_bank,
                },
            },
        }
