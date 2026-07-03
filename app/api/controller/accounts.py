from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends

from app.api.security.merchant_auth import ValidMerchant
from app.schemas.requests.accounts import CreateDedicatedAccountRequestSchema
from app.schemas.requests.filter import PaginateFilterRequestSchema
from app.services.accounts import AccountService
from app.services.statements import StatementService


async def create_dedicated_account(
    body: CreateDedicatedAccountRequestSchema,
    merchant: ValidMerchant,
    service: Annotated[AccountService, Depends()],
) -> dict[str, Any]:
    return await service.create_dedicated(body, merchant_id=merchant)


async def get_account(
    account_id: UUID,
    merchant: ValidMerchant,
    service: Annotated[AccountService, Depends()],
) -> dict[str, Any]:
    return await service.get(account_id, merchant_id=merchant)


async def list_transactions(
    account_id: UUID,
    merchant: ValidMerchant,
    filters: Annotated[PaginateFilterRequestSchema, Depends()],
    service: Annotated[StatementService, Depends()],
) -> dict[str, Any]:
    return await service.list_transactions(account_id, merchant, filters)


async def get_statement(
    account_id: UUID,
    merchant: ValidMerchant,
    service: Annotated[StatementService, Depends()],
) -> dict[str, Any]:
    return await service.get_statement(account_id, merchant)
