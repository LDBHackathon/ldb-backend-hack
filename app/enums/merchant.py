from enum import StrEnum


class MerchantStatus(StrEnum):
    """LDB merchant account lifecycle status."""

    PENDING_KYB = "pending_kyb"
    ACTIVE = "active"
    SUSPENDED = "suspended"
