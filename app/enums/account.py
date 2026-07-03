from enum import StrEnum


class AccountStatus(StrEnum):
    """Dedicated virtual account lifecycle status."""

    ACTIVE = "active"
    CLOSED = "closed"
    SUSPENDED = "suspended"
