import json
from typing import Annotated, Any

from fastapi import Depends, Header, Request

from app.api.security.merchant_auth import ValidMerchant
from app.schemas.requests.filter import SimulateFundingRequestSchema
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.webhook_forwarder import WebhookForwarderService
from app.services.webhooks import NombaWebhookService


def _print_nomba_webhook_in(
    *,
    payload: dict[str, Any],
    nomba_signature: str | None,
    nomba_sig_value: str | None,
    nomba_timestamp: str | None,
    content_type: str | None,
) -> None:
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
                "signature_verification": "skipped",
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
    content_type = request.headers.get("content-type")

    _print_nomba_webhook_in(
        payload=payload,
        nomba_signature=nomba_signature,
        nomba_sig_value=nomba_sig_value,
        nomba_timestamp=nomba_timestamp,
        content_type=content_type,
    )

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
