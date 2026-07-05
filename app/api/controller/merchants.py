from typing import Annotated, Any

from fastapi import Depends

from app.api.security.merchant_auth import ValidMerchant
from app.schemas.requests.merchants import RegisterMerchantRequestSchema
from app.services.merchants import MerchantService


async def register_merchant(
    body: RegisterMerchantRequestSchema,
    service: Annotated[MerchantService, Depends()],
) -> dict[str, Any]:
    return await service.register(body)


async def get_merchant_profile(
    merchant: ValidMerchant,
    service: Annotated[MerchantService, Depends()],
) -> dict[str, Any]:
    return await service.get_profile(merchant)
