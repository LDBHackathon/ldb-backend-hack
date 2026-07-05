"""Transaction reference generation helpers."""

from uuid import uuid4


def generate_reference() -> str:
    """Generate a unique transaction reference."""
    ref = uuid4().hex
    while ref.startswith("0"):
        ref = uuid4().hex
    return ref


def generate_nomba_account_ref() -> str:
    """Generate a Nomba-compliant accountRef (32-char hex, within 16-64 limit)."""
    return generate_reference()


def generate_merchant_customer_id() -> str:
    """Generate an internal merchant-scoped customer reference."""
    return generate_reference()
