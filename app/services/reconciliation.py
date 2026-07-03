from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.constants import (
    RECONCILIATION_CREDIT_FULL,
    RECONCILIATION_CREDIT_PARTIAL,
    RECONCILIATION_OVERPAYMENT,
    RECONCILIATION_QUARANTINE,
    SUSPENSE_CLOSED_ACCOUNT,
    SUSPENSE_MISDIRECTED,
)
from app.enums.account import AccountStatus
from app.enums.transaction import TransactionStatus, TransactionType
from app.models.customers import Customer, DedicatedAccount
from app.models.transactions import ReconciliationLog, SuspenseLog, Transaction
from app.services.helpers import derive_transaction_status
from app.services.webhook_forwarder import WebhookForwarderService
from app.utils.logger import logger
from app.utils.references import generate_reference


class ReconciliationService:
    """Inbound transfer reconciliation and edge-case routing."""

    def __init__(self) -> None:
        self._forwarder = WebhookForwarderService()

    async def process_payment(
        self,
        *,
        request_id: str,
        event_type: str,
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Reconcile an inbound Nomba payment_success webhook."""
        data = raw_payload.get("data", {})
        transaction_data = data.get("transaction", {})
        customer_data = data.get("customer", {})

        amount = Decimal(str(transaction_data.get("transactionAmount", 0)))
        fee = Decimal(str(transaction_data.get("fee", 0)))
        alias_account_number = (
            transaction_data.get("aliasAccountNumber") or ""
        ).replace(" ", "")
        alias_account_reference = transaction_data.get("aliasAccountReference")
        nomba_transaction_id = transaction_data.get("transactionId")
        merchant_tx_ref = transaction_data.get("merchantTxRef") or generate_reference()
        sender_name = customer_data.get("senderName")
        sender_bank = customer_data.get("bankName")
        narration = transaction_data.get("narration")

        account = await self._find_account(alias_account_number, alias_account_reference)

        if account is None:
            return await self._quarantine_payment(
                request_id=request_id,
                amount=amount,
                fee=fee,
                nomba_transaction_id=nomba_transaction_id,
                merchant_tx_ref=merchant_tx_ref,
                sender_name=sender_name,
                sender_bank=sender_bank,
                narration=narration,
                raw_payload=raw_payload,
                reason=SUSPENSE_MISDIRECTED,
                decision=RECONCILIATION_QUARANTINE,
            )

        await account.fetch_related("customer")
        customer = account.customer

        if account.status != AccountStatus.ACTIVE:
            return await self._quarantine_payment(
                request_id=request_id,
                amount=amount,
                fee=fee,
                nomba_transaction_id=nomba_transaction_id,
                merchant_tx_ref=merchant_tx_ref,
                sender_name=sender_name,
                sender_bank=sender_bank,
                narration=narration,
                raw_payload=raw_payload,
                reason=SUSPENSE_CLOSED_ACCOUNT,
                decision=RECONCILIATION_QUARANTINE,
                account=account,
            )

        tx_status = derive_transaction_status(amount, customer.target_amount)
        decision = self._decision_for_status(tx_status)

        transaction = await Transaction.create(
            id=uuid4(),
            dedicated_account=account,
            nomba_request_id=request_id,
            nomba_transaction_id=nomba_transaction_id,
            merchant_tx_ref=merchant_tx_ref,
            amount=amount,
            fee=fee,
            sender_name=sender_name,
            sender_bank=sender_bank,
            type=TransactionType.INBOUND,
            status=tx_status,
            narration=narration,
            raw_payload=raw_payload,
        )

        customer.wallet_balance += amount
        await customer.save()

        await ReconciliationLog.create(
            id=uuid4(),
            transaction=transaction,
            expected_amount=customer.target_amount,
            received_amount=amount,
            decision=decision,
            details={
                "event_type": event_type,
                "wallet_balance_after": str(customer.wallet_balance),
            },
        )

        logger.info(
            "Payment reconciled",
            request_id=request_id,
            customer_id=str(customer.id),
            status=tx_status,
            amount=str(amount),
        )

        await self._forwarder.emit_payment_received(
            merchant_id=customer.merchant_id,
            customer=customer,
            account=account,
            transaction=transaction,
        )

        return {
            "transaction_id": transaction.id,
            "status": tx_status,
            "wallet_balance": customer.wallet_balance,
            "quarantined": False,
        }

    async def _find_account(
        self, account_number: str, account_ref: str | None
    ) -> DedicatedAccount | None:
        if account_number:
            account = await DedicatedAccount.get_or_none(account_number=account_number)
            if account:
                return account
        if account_ref:
            return await DedicatedAccount.get_or_none(account_ref=account_ref)
        return None

    async def _quarantine_payment(
        self,
        *,
        request_id: str,
        amount: Decimal,
        fee: Decimal,
        nomba_transaction_id: str | None,
        merchant_tx_ref: str,
        sender_name: str | None,
        sender_bank: str | None,
        narration: str | None,
        raw_payload: dict[str, Any],
        reason: str,
        decision: str,
        account: DedicatedAccount | None = None,
    ) -> dict[str, Any]:
        transaction = await Transaction.create(
            id=uuid4(),
            dedicated_account=account,
            nomba_request_id=request_id,
            nomba_transaction_id=nomba_transaction_id,
            merchant_tx_ref=merchant_tx_ref,
            amount=amount,
            fee=fee,
            sender_name=sender_name,
            sender_bank=sender_bank,
            type=TransactionType.INBOUND,
            status=TransactionStatus.MISDIRECTED,
            narration=narration,
            raw_payload=raw_payload,
        )

        await SuspenseLog.create(
            id=uuid4(),
            transaction=transaction,
            reason=reason,
            amount=amount,
        )

        await ReconciliationLog.create(
            id=uuid4(),
            transaction=transaction,
            expected_amount=None,
            received_amount=amount,
            decision=decision,
            details={"reason": reason},
        )

        logger.warning(
            "Payment quarantined",
            request_id=request_id,
            reason=reason,
            amount=str(amount),
        )

        return {
            "transaction_id": transaction.id,
            "status": TransactionStatus.MISDIRECTED,
            "wallet_balance": None,
            "quarantined": True,
        }

    @staticmethod
    def _decision_for_status(status: TransactionStatus) -> str:
        if status == TransactionStatus.FULL:
            return RECONCILIATION_CREDIT_FULL
        if status == TransactionStatus.PARTIAL:
            return RECONCILIATION_CREDIT_PARTIAL
        if status == TransactionStatus.OVERPAYMENT:
            return RECONCILIATION_OVERPAYMENT
        return RECONCILIATION_QUARANTINE
