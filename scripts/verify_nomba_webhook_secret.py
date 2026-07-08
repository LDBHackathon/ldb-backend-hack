#!/usr/bin/env python3
"""Verify a Nomba webhook signature key against a captured webhook payload."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.integrations.nomba.webhook_verify import (  # noqa: E402
    build_nomba_signing_payload,
    compute_nomba_expected_signature,
)

# Captured from production log 2026-07-07T20:28:07Z
SAMPLE_PAYLOAD = {
    "event_type": "payment_success",
    "requestId": "95573dd6-2a92-465c-a43a-17dfc3a08ab0",
    "data": {
        "merchant": {
            "walletId": "6a3be3c7205e698c1165a45c",
            "walletBalance": 270.0,
            "userId": "ae5cf9f5-79f8-4472-a18a-feaac96d2022",
        },
        "terminal": {},
        "transaction": {
            "aliasAccountNumber": "2979777345",
            "fee": 10.0,
            "sessionId": "100004260707202804164742222378",
            "type": "vact_transfer",
            "transactionId": "API-VACT_TRA-AE5CF-aa9ea011-5e68-4e91-b765-0f2768d3a160",
            "aliasAccountName": "Nomba/faithmattew",
            "responseCode": "",
            "originatingFrom": "api",
            "transactionAmount": 100.0,
            "narration": "Transfer from ABASIFREKE UMANA ISAAC",
            "time": "2026-07-07T20:28:07Z",
            "aliasAccountReference": "883n33n3n3u33h3",
            "aliasAccountType": "VIRTUAL",
        },
        "customer": {
            "bankCode": "305",
            "senderName": "ABASIFREKE UMANA ISAAC",
            "bankName": "Paycom (Opay)",
            "accountNumber": "8083732799",
        },
    },
}
SAMPLE_TIMESTAMP = "2026-07-07T20:28:07Z"
SAMPLE_RECEIVED_SIGNATURE = "S1CekSHew3rfVPw+fqaZ9Irr/nBW6kLoOK3peoDWZQ4="


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a Nomba webhook signature key matches a captured webhook."
    )
    parser.add_argument(
        "secret",
        help="Webhook signature key from Nomba dashboard (Developer → Webhook Setup)",
    )
    parser.add_argument(
        "--received",
        default=SAMPLE_RECEIVED_SIGNATURE,
        help="nomba-signature header value from the webhook log",
    )
    parser.add_argument(
        "--timestamp",
        default=SAMPLE_TIMESTAMP,
        help="nomba-timestamp header value from the webhook log",
    )
    args = parser.parse_args()

    secret = args.secret.strip()
    signing_payload = build_nomba_signing_payload(SAMPLE_PAYLOAD, args.timestamp)
    digest = hmac.new(secret.encode(), signing_payload.encode(), hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    match = hmac.compare_digest(expected.lower(), args.received.lower())

    print(json.dumps({
        "signing_payload": signing_payload,
        "expected_signature": expected,
        "received_signature": args.received,
        "match": match,
    }, indent=2))

    if match:
        print("\nOK: Use this value for NOMBA_WEBHOOK_SECRET in .env-hack, then restart the container.")
        return 0

    print(
        "\nMISMATCH: This secret does not match Nomba's signature. "
        "Copy the exact Signature Key from Nomba dashboard → Developer → Webhook Setup."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
