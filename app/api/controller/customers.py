from typing import Annotated, Any
from uuid import UUID

from app.api.security.merchant_auth import ValidMerchant
from app.schemas.requests.customers import (
    CreateCustomerRequestSchema,
    LinkNombaSubAccountRequestSchema,
    UpdateCustomerRequestSchema,
)
from app.services.customers import CustomerService
from fastapi import Depends


async def create_customer(
    body: CreateCustomerRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await service.create(body, merchant_id=merchant)


async def link_nomba_sub_account(
    customer_id: str,
    body: LinkNombaSubAccountRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await service.link_nomba_sub_account(customer_id, body, merchant_id=merchant)


async def get_customer(
    customer_id: str,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await service.get(customer_id, merchant_id=merchant)


async def update_customer(
    customer_id: str,
    body: UpdateCustomerRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[CustomerService, Depends()],
) -> dict[str, Any]:
    return await service.update(customer_id, body, merchant_id=merchant)
