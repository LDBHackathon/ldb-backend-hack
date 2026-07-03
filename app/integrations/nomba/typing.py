from typing import Any, TypedDict


class NombaVirtualAccountData(TypedDict, total=False):
    """Nomba virtual account creation response data."""

    accountNumber: str
    accountRef: str
    accountName: str
    bankName: str
    id: str


class NombaWebhookPayload(TypedDict, total=False):
    """Nomba webhook envelope."""

    event_type: str
    requestId: str
    request_id: str
    data: dict[str, Any]
