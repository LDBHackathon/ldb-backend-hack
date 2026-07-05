from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.enums.merchant import MerchantStatus
from app.models.merchants import Merchant, MerchantApiKey
from app.utils.api_keys import api_key_prefix, hash_api_key
from app.utils.exceptions import ErrorResponse
from app.utils.logger import logger

Authorization = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]


async def get_merchant_from_bearer(auth: Authorization) -> UUID:
    """Validate merchant API key and return merchant ID."""
    raw_key = auth.credentials
    prefix = api_key_prefix(raw_key)
    key_hash = hash_api_key(raw_key)

    api_key = (
        await MerchantApiKey.filter(
            key_prefix=prefix,
            key_hash=key_hash,
            revoked_at__isnull=True,
        )
        .select_related("merchant")
        .first()
    )
    if api_key is None:
        logger.warning("Merchant bearer auth validation failed")
        raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Unauthorized access")

    merchant: Merchant = api_key.merchant
    if merchant.status != MerchantStatus.ACTIVE:
        raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Merchant account suspended")

    return merchant.id


ValidMerchant = Annotated[UUID, Depends(get_merchant_from_bearer)]
