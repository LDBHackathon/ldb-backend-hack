import json
from typing import Annotated, Any

from fastapi import Depends, Header, Request, status

from app.api.security.merchant_auth import ValidMerchant
from app.integrations.nomba.webhook_verify import (
    build_nomba_signing_payload,
    compute_nomba_expected_signature,
    verify_nomba_signature,
)
from app.schemas.requests.filter import SimulateFundingRequestSchema
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.webhook_forwarder import WebhookForwarderService
from app.services.webhooks import NombaWebhookService
from app.settings import settings
from app.utils.response_formatter import error_response


def _print_nomba_webhook_in(
    *,
    payload: dict[str, Any],
    nomba_signature: str | None,
    nomba_sig_value: str | None,
    signature: str | None,
    nomba_timestamp: str | None,
    content_type: str | None,
) -> None:
    signing_payload = (
        build_nomba_signing_payload(payload, nomba_timestamp)
        if nomba_timestamp
        else None
    )
    expected_signature = compute_nomba_expected_signature(payload, nomba_timestamp)
    signature_valid = verify_nomba_signature(payload, signature, nomba_timestamp)

    print("=== NOMBA WEBHOOK IN ===", flush=True)
    print(
        json.dumps(
            {
                "headers": {
                    "nomba-signature": nomba_signature,
                    "nomba-sig-value": nomba_sig_value,
                    "nomba-timestamp": nomba_timestamp,
                    "content-type": content_type,
                },
                "payload": payload,
                "signature_debug": {
                    "has_secret": bool(settings.NOMBA_WEBHOOK_SECRET),
                    "signing_payload": signing_payload,
                    "expected_signature": expected_signature,
                    "received_signature": signature,
                    "signature_valid": signature_valid,
                },
            },
            indent=2,
            default=str,
        ),
        flush=True,
    )


def _print_nomba_webhook_out(response: dict[str, Any]) -> None:
    print("=== NOMBA WEBHOOK OUT ===", flush=True)
    print(json.dumps(response, indent=2, default=str), flush=True)


async def register_webhook(
    body: RegisterWebhookRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[WebhookForwarderService, Depends()],
) -> dict[str, Any]:
    return await service.register(body, merchant_id=merchant)


async def nomba_webhook(
    request: Request,
    service: Annotated[NombaWebhookService, Depends()],
    nomba_signature: Annotated[str | None, Header(alias="nomba-signature")] = None,
    nomba_sig_value: Annotated[str | None, Header(alias="nomba-sig-value")] = None,
    nomba_timestamp: Annotated[str | None, Header(alias="nomba-timestamp")] = None,
) -> dict[str, Any]:
    raw_body = await request.body()
    payload = json.loads(raw_body)
    signature = nomba_signature or nomba_sig_value
    content_type = request.headers.get("content-type")

    _print_nomba_webhook_in(
        payload=payload,
        nomba_signature=nomba_signature,
        nomba_sig_value=nomba_sig_value,
        signature=signature,
        nomba_timestamp=nomba_timestamp,
        content_type=content_type,
    )

    if not verify_nomba_signature(payload, signature, nomba_timestamp):
        response = {
            "status": "failure",
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "message": "Invalid webhook signature",
            "errors": None,
        }
        _print_nomba_webhook_out(response)
        return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")

    result = await service.receive(payload)
    _print_nomba_webhook_out(result)
    return result


async def simulate_funding(
    body: SimulateFundingRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[NombaWebhookService, Depends()],
) -> dict[str, Any]:
    _ = merchant
    return await service.simulate(body)
