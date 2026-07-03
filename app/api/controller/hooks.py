import json
from typing import Annotated, Any

from fastapi import Depends, Header, Request, status

from app.api.security.merchant_auth import ValidMerchant
from app.integrations.nomba import verify_nomba_signature
from app.schemas.requests.filter import SimulateFundingRequestSchema
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.webhook_forwarder import WebhookForwarderService
from app.services.webhooks import NombaWebhookService
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
) -> dict[str, Any]:
    raw_body = await request.body()
    if not verify_nomba_signature(raw_body, nomba_signature):
        logger.warning("Nomba webhook signature verification failed")
        return error_response(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")

    payload = json.loads(raw_body)
    return await service.receive(payload)


async def simulate_funding(
    body: SimulateFundingRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[NombaWebhookService, Depends()],
) -> dict[str, Any]:
    _ = merchant
    return await service.simulate(body)
