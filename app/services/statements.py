from decimal import Decimal
import math
from typing import Any
from uuid import UUID

from fastapi import status

from app.enums.transaction import TransactionStatus
from app.models.customers import DedicatedAccount
from app.models.transactions import Transaction
from app.schemas.requests.filter import PaginateFilterRequestSchema
from app.services.helpers import _funding_status, _outstanding_balance
from app.utils.response_formatter import error_response, paginated_success_response, success_response


class StatementService:
    """Customer-level statements and transaction history."""

    async def list_transactions(
        self,
        account_id: UUID,
        merchant_id: UUID,
        filters: PaginateFilterRequestSchema,
    ) -> dict[str, Any]:
        account = await DedicatedAccount.get_or_none(id=account_id)
        if not account:
            return error_response(status.HTTP_404_NOT_FOUND, "Account not found")
        await account.fetch_related("customer")
        if account.customer.merchant_id != merchant_id:
            return error_response(status.HTTP_404_NOT_FOUND, "Account not found")

        query = Transaction.filter(dedicated_account_id=account.id).order_by("-created_at")
        total = await query.count()
        offset = (filters.page - 1) * filters.limit
        transactions = await query.offset(offset).limit(filters.limit)

        data = [
            {
                "id": tx.id,
                "dedicated_account_id": tx.dedicated_account_id,
                "nomba_request_id": tx.nomba_request_id,
                "nomba_transaction_id": tx.nomba_transaction_id,
                "merchant_tx_ref": tx.merchant_tx_ref,
                "amount": tx.amount,
                "fee": tx.fee,
                "sender_name": tx.sender_name,
                "sender_bank": tx.sender_bank,
                "type": tx.type,
                "status": tx.status,
                "narration": tx.narration,
                "created_at": tx.created_at,
            }
            for tx in transactions
        ]

        pages = max(math.ceil(total / filters.limit), 1)
        return paginated_success_response(
            status.HTTP_200_OK,
            "Transactions retrieved",
            metadata={
                "page": filters.page,
                "pages": pages,
                "limit": filters.limit,
                "total": total,
                "count": len(data),
            },
            data=data,
        )

    async def get_statement(self, account_id: UUID, merchant_id: UUID) -> dict[str, Any]:
        account = await DedicatedAccount.get_or_none(id=account_id)
        if not account:
            return error_response(status.HTTP_404_NOT_FOUND, "Account not found")
        await account.fetch_related("customer")
        if account.customer.merchant_id != merchant_id:
            return error_response(status.HTTP_404_NOT_FOUND, "Account not found")

        customer = account.customer
        transactions = await Transaction.filter(
            dedicated_account_id=account.id
        ).order_by("-created_at")

        total_received = sum(
            (tx.amount for tx in transactions if tx.status != TransactionStatus.MISDIRECTED),
            start=Decimal("0"),
        )

        flagged_short_payments = sum(
            1 for tx in transactions if tx.status == TransactionStatus.PARTIAL
        )

        outstanding = _outstanding_balance(customer) or Decimal("0")

        statement = {
            "account_id": account.id,
            "merchant_customer_id": customer.merchant_customer_id,
            "customer_name": customer.name,
            "account_number": account.account_number,
            "target_amount": customer.target_amount,
            "total_received": total_received,
            "wallet_balance": customer.wallet_balance,
            "outstanding_balance": outstanding,
            "flagged_short_payments": flagged_short_payments,
            "status": _funding_status(customer),
            "transactions": [
                {
                    "id": tx.id,
                    "amount": tx.amount,
                    "status": tx.status.value,
                    "sender_name": tx.sender_name,
                    "sender_bank": tx.sender_bank,
                    "merchant_tx_ref": tx.merchant_tx_ref,
                    "narration": tx.narration,
                    "created_at": tx.created_at,
                }
                for tx in transactions
            ],
        }

        return success_response(
            status.HTTP_200_OK,
            "Statement generated",
            data=statement,
        )
