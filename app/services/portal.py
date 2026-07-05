import math
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import status
from tortoise.expressions import Q

from app.enums.transaction import TransactionStatus
from app.models.customers import Customer, DedicatedAccount
from app.models.merchants import Merchant
from app.models.transactions import Transaction
from app.schemas.requests.filter import SimulateFundingRequestSchema
from app.services.helpers import (
    _funding_status,
    _outstanding_balance,
    _progress_percentage,
    derive_customer_flags,
    portal_customer_status,
    transaction_portal_flag,
    transaction_portal_status,
)
from app.services.statements import StatementService
from app.services.webhooks import NombaWebhookService
from app.utils.response_formatter import error_response, paginated_success_response, success_response


class PortalService:
    """Merchant dashboard reads aligned with WealthVault UI mocks."""

    def __init__(self) -> None:
        self._statements = StatementService()
        self._webhooks = NombaWebhookService()

    async def dashboard_summary(self, merchant_id: UUID) -> dict[str, Any]:
        merchant = await Merchant.get_or_none(id=merchant_id)
        customers = await Customer.filter(merchant_id=merchant_id).all()
        account_ids = await DedicatedAccount.filter(
            customer_id__in=[c.id for c in customers]
        ).values_list("id", flat=True)

        total_deposits = sum((c.wallet_balance for c in customers), start=Decimal("0"))
        month_start = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        customers_added_this_month = sum(
            1 for c in customers if c.created_at >= month_start
        )

        transactions = await Transaction.filter(dedicated_account_id__in=account_ids).all()
        flagged_payments = sum(
            1
            for tx in transactions
            if tx.status in (TransactionStatus.PARTIAL, TransactionStatus.OVERPAYMENT)
        )
        failed_transactions = sum(
            1 for tx in transactions if tx.status == TransactionStatus.MISDIRECTED
        )

        funding_progress = []
        for customer in customers[:5]:
            funding_progress.append(
                {
                    "id": customer.id,
                    "name": customer.name,
                    "wallet_balance": customer.wallet_balance,
                    "target_amount": customer.target_amount,
                    "progress_percentage": _progress_percentage(customer),
                }
            )

        return success_response(
            status.HTTP_200_OK,
            "Dashboard summary retrieved",
            data={
                "merchant_name": merchant.name if merchant else None,
                "total_customers": len(customers),
                "customers_added_this_month": customers_added_this_month,
                "total_deposits": total_deposits,
                "flagged_payments": flagged_payments,
                "failed_transactions": failed_transactions,
                "funding_progress": funding_progress,
            },
        )

    async def list_customers(
        self,
        merchant_id: UUID,
        *,
        q: str | None = None,
        flag: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        merchant = await Merchant.get_or_none(id=merchant_id)
        query = Customer.filter(merchant_id=merchant_id).order_by("-created_at")
        if q:
            query = query.filter(
                Q(name__icontains=q)
                | Q(email__icontains=q)
                | Q(merchant_customer_id__icontains=q)
            )

        customers = await query.all()
        items: list[dict[str, Any]] = []
        for customer in customers:
            account = await DedicatedAccount.filter(customer_id=customer.id).first()
            misdirected = False
            if account:
                misdirected = await Transaction.filter(
                    dedicated_account_id=account.id,
                    status=TransactionStatus.MISDIRECTED,
                ).exists()
            flags = derive_customer_flags(customer, has_misdirected=misdirected)
            if flag and flag not in flags:
                continue
            items.append(
                {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "nuban": account.account_number if account else None,
                    "bank": "Nomba",
                    "client_name": merchant.name if merchant else "",
                    "date_joined": customer.created_at,
                    "status": portal_customer_status(flags),
                    "target_amount": customer.target_amount,
                    "total_deposited": customer.wallet_balance,
                    "outstanding_balance": _outstanding_balance(customer),
                    "progress_percentage": _progress_percentage(customer),
                    "flags": flags,
                    "account_id": account.id if account else None,
                }
            )

        total = len(items)
        offset = (page - 1) * limit
        page_items = items[offset : offset + limit]
        pages = max(math.ceil(total / limit), 1) if total else 1

        return paginated_success_response(
            status.HTTP_200_OK,
            "Customers retrieved",
            metadata={
                "page": page,
                "pages": pages,
                "limit": limit,
                "total": total,
                "count": len(page_items),
            },
            data=page_items,
        )

    async def get_customer(
        self, customer_id: str, merchant_id: UUID
    ) -> dict[str, Any]:
        customer = await self._resolve_customer(customer_id, merchant_id)
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")

        merchant = await Merchant.get(id=merchant_id)
        account = await DedicatedAccount.filter(customer_id=customer.id).first()
        misdirected = False
        transactions: list[Transaction] = []
        if account:
            transactions = await Transaction.filter(
                dedicated_account_id=account.id
            ).order_by("-created_at").limit(50)
            misdirected = any(
                tx.status == TransactionStatus.MISDIRECTED for tx in transactions
            )

        flags = derive_customer_flags(customer, has_misdirected=misdirected)
        txn_items = [
            {
                "id": tx.id,
                "date": tx.created_at,
                "reference": tx.merchant_tx_ref or tx.nomba_transaction_id or str(tx.id),
                "description": tx.narration
                or f"Inbound bank transfer · {tx.sender_bank or 'Unknown'}",
                "amount": tx.amount,
                "bank": tx.sender_bank,
                "tags": [transaction_portal_flag(tx.status)],
                "status": transaction_portal_status(tx.status),
            }
            for tx in transactions
        ]

        return success_response(
            status.HTTP_200_OK,
            "Customer retrieved",
            data={
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "nuban": account.account_number if account else None,
                "bank": "Nomba",
                "client_name": merchant.name,
                "date_joined": customer.created_at,
                "status": portal_customer_status(flags),
                "target_amount": customer.target_amount,
                "total_deposited": customer.wallet_balance,
                "outstanding_balance": _outstanding_balance(customer),
                "progress_percentage": _progress_percentage(customer),
                "funding_status": _funding_status(customer),
                "flags": flags,
                "account_id": account.id if account else None,
                "transactions": txn_items,
            },
        )

    async def get_customer_statement(
        self, customer_id: str, merchant_id: UUID
    ) -> dict[str, Any]:
        customer = await self._resolve_customer(customer_id, merchant_id)
        if not customer:
            return error_response(status.HTTP_404_NOT_FOUND, "Customer not found")
        account = await DedicatedAccount.filter(customer_id=customer.id).first()
        if not account:
            return error_response(status.HTTP_404_NOT_FOUND, "Dedicated account not found")
        return await self._statements.get_statement(account.id, merchant_id)

    async def list_transactions(
        self,
        merchant_id: UUID,
        *,
        q: str | None = None,
        txn_type: str | None = None,
        txn_status: str | None = None,
        flag: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        account_rows = await DedicatedAccount.filter(
            customer__merchant_id=merchant_id
        ).prefetch_related("customer")
        account_map = {row.id: row for row in account_rows}
        account_ids = list(account_map.keys())

        account_ids = list(account_map.keys())
        if not account_ids:
            return paginated_success_response(
                status.HTTP_200_OK,
                "Transactions retrieved",
                metadata={"page": page, "pages": 1, "limit": limit, "total": 0, "count": 0},
                data=[],
            )

        query = Transaction.filter(dedicated_account_id__in=account_ids).order_by(
            "-created_at"
        )
        transactions = await query.all()

        items: list[dict[str, Any]] = []
        for tx in transactions:
            if txn_type == "withdrawal":
                continue
            account = account_map.get(tx.dedicated_account_id)
            if not account:
                continue
            customer = account.customer
            portal_flag = transaction_portal_flag(tx.status)
            portal_stat = transaction_portal_status(tx.status)
            if flag and portal_flag != flag:
                continue
            if txn_status and portal_stat.lower() != txn_status.lower():
                continue
            reference = tx.merchant_tx_ref or tx.nomba_transaction_id or str(tx.id)
            if q:
                haystack = " ".join(
                    filter(
                        None,
                        [
                            customer.name,
                            customer.email,
                            reference,
                            tx.sender_bank,
                            tx.sender_name,
                        ],
                    )
                ).lower()
                if q.lower() not in haystack:
                    continue
            items.append(
                {
                    "id": tx.id,
                    "customer_id": customer.id,
                    "customer_name": customer.name,
                    "reference": reference,
                    "date": tx.created_at,
                    "description": tx.narration
                    or f"Inbound bank transfer · {tx.sender_bank or 'Unknown'}",
                    "type": "deposit",
                    "amount": tx.amount,
                    "bank": tx.sender_bank,
                    "status": portal_stat,
                    "flags": [portal_flag],
                }
            )

        total = len(items)
        offset = (page - 1) * limit
        page_items = items[offset : offset + limit]
        pages = max(math.ceil(total / limit), 1) if total else 1

        return paginated_success_response(
            status.HTTP_200_OK,
            "Transactions retrieved",
            metadata={
                "page": page,
                "pages": pages,
                "limit": limit,
                "total": total,
                "count": len(page_items),
            },
            data=page_items,
        )

    async def transactions_summary(self, merchant_id: UUID) -> dict[str, Any]:
        account_ids = await DedicatedAccount.filter(
            customer__merchant_id=merchant_id
        ).values_list("id", flat=True)
        transactions = await Transaction.filter(dedicated_account_id__in=account_ids).all()
        total_deposits = sum(
            (
                tx.amount
                for tx in transactions
                if tx.status != TransactionStatus.MISDIRECTED
            ),
            start=Decimal("0"),
        )
        failed = sum(
            1 for tx in transactions if tx.status == TransactionStatus.MISDIRECTED
        )
        return success_response(
            status.HTTP_200_OK,
            "Transaction summary retrieved",
            data={
                "total_deposits": total_deposits,
                "total_withdrawals": Decimal("0"),
                "net_position": total_deposits,
                "failed_transactions": failed,
            },
        )

    async def recent_transactions(
        self, merchant_id: UUID, limit: int = 6
    ) -> dict[str, Any]:
        result = await self.list_transactions(
            merchant_id, page=1, limit=limit
        )
        return success_response(
            status.HTTP_200_OK,
            "Recent transactions retrieved",
            data=result.get("data", []),
        )

    async def simulate_transfer(
        self, body: SimulateFundingRequestSchema
    ) -> dict[str, Any]:
        return await self._webhooks.simulate(body)

    async def _resolve_customer(
        self, customer_id: str, merchant_id: UUID
    ) -> Customer | None:
        try:
            parsed_id = UUID(customer_id)
            customer = await Customer.get_or_none(id=parsed_id, merchant_id=merchant_id)
            if customer:
                return customer
        except ValueError:
            pass
        return await Customer.get_or_none(
            merchant_id=merchant_id,
            merchant_customer_id=customer_id,
        )
