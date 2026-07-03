from enum import StrEnum


class TransactionType(StrEnum):
    """Transaction direction/type."""

    INBOUND = "inbound"


class TransactionStatus(StrEnum):
    """Reconciliation outcome for an inbound transfer."""

    FULL = "full"
    PARTIAL = "partial"
    OVERPAYMENT = "overpayment"
    MISDIRECTED = "misdirected"
