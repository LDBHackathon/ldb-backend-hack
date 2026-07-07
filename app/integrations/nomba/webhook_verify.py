import base64
import hashlib
import hmac
from typing import Any

from app.settings import settings


def build_nomba_signing_payload(payload: dict[str, Any], timestamp: str) -> str:
    """Build the colon-separated string Nomba signs for webhook verification."""
    data = payload.get("data", {})
    merchant = data.get("merchant", {})
    transaction = data.get("transaction", {})

    event_type = payload.get("event_type") or payload.get("eventType") or ""
    request_id = payload.get("requestId") or payload.get("request_id") or ""
    user_id = merchant.get("userId", "")
    wallet_id = merchant.get("walletId", "")
    transaction_id = transaction.get("transactionId", "")
    transaction_type = transaction.get("type", "")
    transaction_time = transaction.get("time", "")
    transaction_response_code = transaction.get("responseCode", "")

    if transaction_response_code == "null":
        transaction_response_code = ""

    return (
        f"{event_type}:{request_id}:{user_id}:{wallet_id}:"
        f"{transaction_id}:{transaction_type}:{transaction_time}:"
        f"{transaction_response_code}:{timestamp}"
    )


def verify_nomba_signature(
    payload: dict[str, Any],
    signature: str | None,
    timestamp: str | None,
) -> bool:
    """Verify Nomba webhook HMAC-SHA256 signature."""
    if not signature or not timestamp or not settings.NOMBA_WEBHOOK_SECRET:
        return False

    signing_payload = build_nomba_signing_payload(payload, timestamp)
    digest = hmac.new(
        settings.NOMBA_WEBHOOK_SECRET.encode(),
        signing_payload.encode(),
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected.lower(), signature.lower())
