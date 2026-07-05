from typing import Any, TypedDict


class NombaVirtualAccountData(TypedDict, total=False):
    """Normalized Nomba virtual account response."""

    account_ref: str
    account_name: str
    account_number: str
    bank_name: str
    nomba_va_id: str
    account_holder_id: str
    currency: str
    raw: dict[str, Any]


class NombaWebhookPayload(TypedDict, total=False):
    """Nomba webhook envelope."""

    event_type: str
    requestId: str
    request_id: str
    data: dict[str, Any]
