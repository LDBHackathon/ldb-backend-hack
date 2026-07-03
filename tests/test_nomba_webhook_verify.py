import base64
import hashlib
import hmac

import pytest

from app.integrations.nomba.webhook_verify import verify_nomba_signature
from app.settings import settings


def test_nomba_hmac_verification_accepts_valid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-webhook-secret"
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", secret)
    body = b'{"event_type":"payment_success","requestId":"abc"}'
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    assert verify_nomba_signature(body, signature) is True


def test_nomba_hmac_verification_rejects_invalid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", "test-webhook-secret")
    body = b'{"event_type":"payment_success","requestId":"abc"}'
    assert verify_nomba_signature(body, "invalid-signature") is False


def test_nomba_hmac_verification_rejects_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", "")
    body = b'{"event_type":"payment_success"}'
    assert verify_nomba_signature(body, "anything") is False
