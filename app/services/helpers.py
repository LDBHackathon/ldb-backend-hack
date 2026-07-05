from decimal import Decimal
from uuid import UUID

from app.enums.customer import CustomerStatus
from app.enums.account import AccountStatus
from app.enums.transaction import TransactionStatus
from app.models.customers import Customer, DedicatedAccount


def _funding_status(customer: Customer) -> str:
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
        "status": customer.status,
        "funding_status": _funding_status(customer),
        "nomba_sub_account_id": customer.nomba_sub_account_id,
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


def derive_customer_flags(
    customer: Customer,
    *,
    has_misdirected: bool = False,
) -> list[str]:
    """Map customer funding state to PDF UI flags."""
    flags: list[str] = []
    if has_misdirected:
        flags.append("Misdirected")
    if (
        customer.target_amount is not None
        and customer.wallet_balance > customer.target_amount
    ):
        flags.append("Overpaid")
    funding = _funding_status(customer)
    if funding == "Underpayment":
        flags.append("Underpaid")
    if not flags:
        flags.append("Normal")
    return flags


def portal_customer_status(flags: list[str]) -> str:
    """Primary status label for portal customer list."""
    if "Misdirected" in flags:
        return "Misdirected"
    if "Overpaid" in flags:
        return "Overpaid"
    if "Underpaid" in flags:
        return "Underpayment"
    return "Normal"


def transaction_portal_flag(status: TransactionStatus) -> str:
    """Map transaction reconciliation status to PDF flag label."""
    mapping = {
        TransactionStatus.PARTIAL: "Underpaid",
        TransactionStatus.OVERPAYMENT: "Overpaid",
        TransactionStatus.MISDIRECTED: "Misdirected",
        TransactionStatus.FULL: "Normal",
    }
    return mapping.get(status, "Normal")


def transaction_portal_status(status: TransactionStatus) -> str:
    """Success/Failed label for portal transaction rows."""
    return "Failed" if status == TransactionStatus.MISDIRECTED else "Success"
