import base64
import hashlib
import hmac

from app.settings import settings


def verify_nomba_signature(raw_body: bytes, signature: str | None) -> bool:
    """Verify Nomba webhook HMAC-SHA256 signature."""
    if not signature or not settings.NOMBA_WEBHOOK_SECRET:
        return False

    digest = hmac.new(
        settings.NOMBA_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)
