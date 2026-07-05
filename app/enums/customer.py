from enum import StrEnum


class CustomerStatus(StrEnum):
    """End-user customer provisioning status on LDB + Nomba."""

    ACTIVE = "active"
    PENDING_NOMBA = "pending_nomba"
    SUSPENDED = "suspended"
