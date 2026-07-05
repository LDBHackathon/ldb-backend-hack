"""Nomba API helpers aligned with official docs."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any

from app.utils.references import generate_nomba_account_ref

NOMBA_ACCOUNT_REF_MIN_LENGTH = 16
NOMBA_ACCOUNT_REF_MAX_LENGTH = 64
NOMBA_ACCOUNT_NAME_MIN_LENGTH = 8
NOMBA_ACCOUNT_NAME_MAX_LENGTH = 64


def build_nomba_account_ref(candidate: str | None = None) -> str:
    """Return a Nomba-compliant accountRef (16-64 chars)."""
    if candidate and NOMBA_ACCOUNT_REF_MIN_LENGTH <= len(candidate) <= NOMBA_ACCOUNT_REF_MAX_LENGTH:
        return candidate
    return generate_nomba_account_ref()


def normalize_nomba_account_name(name: str) -> str:
    """Trim and cap account holder name to Nomba limits."""
    trimmed = name.strip()
    if len(trimmed) < NOMBA_ACCOUNT_NAME_MIN_LENGTH:
        msg = (
            f"account name must be at least {NOMBA_ACCOUNT_NAME_MIN_LENGTH} characters "
            "for Nomba virtual accounts"
        )
        raise ValueError(msg)
    return trimmed[:NOMBA_ACCOUNT_NAME_MAX_LENGTH]


def format_nomba_date_range(start_date: date, end_date: date) -> tuple[str, str]:
    """Format UTC date range for Nomba transaction filters."""
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    end = datetime.combine(end_date, time.max, tzinfo=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    return start, end


def format_nomba_expected_amount(amount: Decimal | None) -> str | None:
    """Format expected amount for Nomba virtual account APIs."""
    if amount is None:
        return None
    return format(amount, "f")


def parse_virtual_account_response(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize Nomba virtual account response fields."""
    account_number = data.get("bankAccountNumber") or data.get("accountNumber")
    return {
        "account_ref": data.get("accountRef"),
        "account_name": data.get("accountName") or data.get("bankAccountName"),
        "account_number": str(account_number).replace(" ", "") if account_number else None,
        "bank_name": data.get("bankName"),
        "nomba_va_id": data.get("accountId") or data.get("id"),
        "account_holder_id": data.get("accountHolderId"),
        "currency": data.get("currency"),
        "raw": data,
    }
