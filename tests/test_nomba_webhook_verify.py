import json

import pytest

from app.integrations.nomba.webhook_verify import (
    build_nomba_signing_payload,
    verify_nomba_signature,
)
from app.settings import settings

NOMBA_VACT_TRANSFER_SAMPLE = {
    "event_type": "payment_success",
    "requestId": "45f2dc2d-d559-4773-bba3-2d5ec17b2e20",
    "data": {
        "merchant": {
            "walletId": "6756ff80aafe04a795f18b38",
            "walletBalance": 6052,
            "userId": "b7b10e81-e57d-41d0-8fdc-f4e23a132bbf",
        },
        "terminal": {},
        "transaction": {
            "aliasAccountNumber": "5343270516",
            "fee": 5,
            "sessionId": "IFAP-TRANSFER-46501-e0339485-1a2f-4b43-9bd5-fec9649e5928",
            "type": "vact_transfer",
            "transactionId": "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-9dbb4548fd7a",
            "aliasAccountName": "ZAXBOX/EZENNA NWACHUKWU",
            "responseCode": "",
            "originatingFrom": "api",
            "transactionAmount": 10,
            "narration": "Habiblahi Hamzat Transfer 10.00 To ZAXBOX/EZENNA NWACHUKWU - Nomba",
            "time": "2025-09-29T10:51:44Z",
            "aliasAccountReference": "654f7c80bd4a510c90fb7f92",
            "aliasAccountType": "VIRTUAL",
        },
        "customer": {
            "bankCode": "090645",
            "senderName": "Habiblahi Hamzat",
            "bankName": "Nombank",
            "accountNumber": "9617811496",
        },
    },
}

NOMBA_OFFICIAL_SAMPLE_SECRET = "HkatexKDZg7CLWy96q5sfrVHSvtoz92B"


def test_build_nomba_signing_payload_matches_documented_format() -> None:
    timestamp = "2025-09-29T10:51:44Z"
    signing_payload = build_nomba_signing_payload(NOMBA_VACT_TRANSFER_SAMPLE, timestamp)
    assert signing_payload == (
        "payment_success:45f2dc2d-d559-4773-bba3-2d5ec17b2e20:"
        "b7b10e81-e57d-41d0-8fdc-f4e23a132bbf:6756ff80aafe04a795f18b38:"
        "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-9dbb4548fd7a:"
        "vact_transfer:2025-09-29T10:51:44Z::2025-09-29T10:51:44Z"
    )


def test_nomba_signature_verification_accepts_official_sample(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", NOMBA_OFFICIAL_SAMPLE_SECRET)
    timestamp = "2025-09-29T10:51:44Z"
    signature = "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw="
    assert (
        verify_nomba_signature(NOMBA_VACT_TRANSFER_SAMPLE, signature, timestamp) is True
    )


def test_nomba_signature_verification_rejects_invalid_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", NOMBA_OFFICIAL_SAMPLE_SECRET)
    assert (
        verify_nomba_signature(
            NOMBA_VACT_TRANSFER_SAMPLE,
            "invalid-signature",
            "2025-09-29T10:51:44Z",
        )
        is False
    )


def test_nomba_signature_verification_rejects_missing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", "")
    assert (
        verify_nomba_signature(
            NOMBA_VACT_TRANSFER_SAMPLE,
            "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw=",
            "2025-09-29T10:51:44Z",
        )
        is False
    )


def test_nomba_signature_verification_rejects_missing_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "NOMBA_WEBHOOK_SECRET", NOMBA_OFFICIAL_SAMPLE_SECRET)
    assert (
        verify_nomba_signature(
            NOMBA_VACT_TRANSFER_SAMPLE,
            "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw=",
            None,
        )
        is False
    )


def test_build_nomba_signing_payload_treats_null_response_code_as_empty() -> None:
    payload = json.loads(json.dumps(NOMBA_VACT_TRANSFER_SAMPLE))
    payload["data"]["transaction"]["responseCode"] = "null"
    signing_payload = build_nomba_signing_payload(payload, "2025-09-29T10:51:44Z")
    assert signing_payload.endswith(":2025-09-29T10:51:44Z::2025-09-29T10:51:44Z")
