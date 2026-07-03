"""Display formatting helpers."""

from typing import Any
from decimal import Decimal, InvalidOperation


def decimal_to_float_str(value: Decimal) -> str:
    """Serialize Decimal as a plain string without scientific notation."""
    return format(value, "f")


def format_amount(value: Any) -> str:  # noqa: ANN401
    """Format a monetary amount for display."""
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    normalized = (
        amount.quantize(Decimal(1))
        if amount == amount.to_integral_value()
        else amount.normalize()
    )
    formatted = f"{normalized:,f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted
