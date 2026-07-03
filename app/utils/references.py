"""Transaction reference generation helpers."""

from uuid import uuid4


def generate_reference() -> str:
    """Generate a unique transaction reference."""
    ref = uuid4().hex
    while ref.startswith("0"):
        ref = uuid4().hex
    return ref
