from decimal import Decimal
from uuid import UUID

from app.enums.account import AccountStatus
from app.enums.transaction import TransactionStatus
from app.models.customers import Customer, DedicatedAccount


def _customer_status(customer: Customer) -> str:
    if customer.target_amount is None:
        return "Normal"
    if customer.wallet_balance >= customer.target_amount:
        return "Normal"
    if customer.wallet_balance > 0:
        return "Underpayment"
    return "Normal"


def _outstanding_balance(customer: Customer) -> Decimal | None:
    if customer.target_amount is None:
        return None
    outstanding = customer.target_amount - customer.wallet_balance
    return outstanding if outstanding > 0 else Decimal("0")


def _progress_percentage(customer: Customer) -> float | None:
    if customer.target_amount is None or customer.target_amount <= 0:
        return None
    pct = float(customer.wallet_balance / customer.target_amount * 100)
    return min(round(pct, 2), 100.0)


async def build_customer_response(customer: Customer) -> dict:
    """Build a customer response dict with computed funding fields."""
    account = await DedicatedAccount.filter(customer_id=customer.id).first()
    dedicated_account = None
    if account:
        dedicated_account = {
            "id": account.id,
            "account_number": account.account_number,
            "account_name": account.account_name,
            "bank_name": "Nomba",
            "status": account.status,
        }

    return {
        "id": customer.id,
        "merchant_customer_id": customer.merchant_customer_id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "target_amount": customer.target_amount,
        "wallet_balance": customer.wallet_balance,
        "outstanding_balance": _outstanding_balance(customer),
        "progress_percentage": _progress_percentage(customer),
        "status": _customer_status(customer),
        "metadata": customer.metadata,
        "dedicated_account": dedicated_account,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }


async def build_account_response(account: DedicatedAccount) -> dict:
    """Build an account response dict."""
    await account.fetch_related("customer")
    customer = account.customer
    return {
        "id": account.id,
        "customer_id": customer.id,
        "merchant_customer_id": customer.merchant_customer_id,
        "nomba_va_id": account.nomba_va_id,
        "account_number": account.account_number,
        "account_name": account.account_name,
        "account_ref": account.account_ref,
        "bank_name": "Nomba",
        "status": account.status,
        "wallet_balance": customer.wallet_balance,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


def derive_transaction_status(
    received_amount: Decimal, target_amount: Decimal | None
) -> TransactionStatus:
    """Determine reconciliation status from received vs target amount."""
    if target_amount is None:
        return TransactionStatus.FULL
    if received_amount >= target_amount:
        if received_amount > target_amount:
            return TransactionStatus.OVERPAYMENT
        return TransactionStatus.FULL
    if received_amount > 0:
        return TransactionStatus.PARTIAL
    return TransactionStatus.MISDIRECTED
