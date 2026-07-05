from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Response

from app.api.security.portal_auth import ValidPortalMerchant
from app.schemas.requests.filter import SimulateFundingRequestSchema
from app.services.portal import PortalService


async def dashboard_summary(
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
) -> dict[str, Any]:
    return await service.dashboard_summary(merchant)


async def list_portal_customers(
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
    q: str | None = None,
    flag: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    return await service.list_customers(
        merchant, q=q, flag=flag, page=page, limit=limit
    )


async def get_portal_customer(
    customer_id: str,
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
) -> dict[str, Any]:
    return await service.get_customer(customer_id, merchant)


async def get_portal_customer_statement(
    customer_id: str,
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
) -> dict[str, Any]:
    return await service.get_customer_statement(customer_id, merchant)


async def list_portal_transactions(
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
    q: str | None = None,
    txn_type: str | None = None,
    txn_status: str | None = None,
    flag: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    return await service.list_transactions(
        merchant,
        q=q,
        txn_type=txn_type,
        txn_status=txn_status,
        flag=flag,
        page=page,
        limit=limit,
    )


async def portal_transactions_summary(
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
) -> dict[str, Any]:
    return await service.transactions_summary(merchant)


async def portal_recent_transactions(
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
    limit: int = 6,
) -> dict[str, Any]:
    return await service.recent_transactions(merchant, limit=limit)


async def portal_simulate_transfer(
    body: SimulateFundingRequestSchema,
    merchant: ValidPortalMerchant,
    service: Annotated[PortalService, Depends()],
) -> dict[str, Any]:
    _ = merchant
    return await service.simulate_transfer(body)
