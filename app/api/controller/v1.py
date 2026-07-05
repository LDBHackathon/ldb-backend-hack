from typing import Annotated, Any

from fastapi import Depends

from app.api.controller.customers import create_customer, get_customer, update_customer
from app.api.controller.hooks import register_webhook
from app.api.security.merchant_auth import ValidMerchant
from app.schemas.requests.customers import (
    CreateCustomerRequestSchema,
    UpdateCustomerRequestSchema,
)
from app.schemas.requests.webhooks import RegisterWebhookRequestSchema
from app.services.customers import CustomerService
from app.services.portal import PortalService
from app.services.webhook_forwarder import WebhookForwarderService


async def v1_create_customer(
    body: CreateCustomerRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await create_customer(body, merchant, service)


async def v1_get_customer(
    customer_id: str,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await get_customer(customer_id, merchant, service)


async def v1_update_customer(
    customer_id: str,
    body: UpdateCustomerRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await update_customer(customer_id, body, merchant, service)


async def v1_get_customer_statement(
    customer_id: str,
    merchant: ValidMerchant,
    portal: Annotated[PortalService, Depends()],
) -> dict[str, Any]:
    return await portal.get_customer_statement(customer_id, merchant)


async def v1_register_webhook(
    body: RegisterWebhookRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[WebhookForwarderService, Depends()],
) -> dict[str, Any]:
    return await register_webhook(body, merchant, service)
