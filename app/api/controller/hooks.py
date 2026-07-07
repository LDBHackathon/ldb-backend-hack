import json
from typing import Annotated, Any

from fastapi import Depends, Header, Request, status

from app.api.security.merchant_auth import ValidMerchant
from app.integrations.nomba import verify_nomba_signature
from app.schemas.requests.filter import SimulateFundingRequestSchema
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.webhook_forwarder import WebhookForwarderService
from app.services.webhooks import NombaWebhookService
from app.settings import settings
from app.utils.logger import logger
from app.utils.response_formatter import error_response, success_response


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
    if not verify_nomba_signature(payload, signature, nomba_timestamp):
        logger.warning(
            "Nomba webhook signature verification failed",
            has_secret=bool(settings.NOMBA_WEBHOOK_SECRET),
            has_timestamp=bool(nomba_timestamp),
        )
        return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")
    logger.info(
        "Nomba webhook received",
        event_type=payload.get("event_type") or payload.get("eventType"),
        request_id=payload.get("requestId") or payload.get("request_id"),
        nomba_payload=payload,
    )
    result = await service.receive(payload)
    logger.info(
        "Nomba webhook processed",
        request_id=payload.get("requestId") or payload.get("request_id"),
        status_code=result.get("status_code"),
        message=result.get("message"),
        data=result.get("data"),
    )
    return result


async def simulate_funding(
    body: SimulateFundingRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[NombaWebhookService, Depends()],
) -> dict[str, Any]:
    _ = merchant
    return await service.simulate(body)
