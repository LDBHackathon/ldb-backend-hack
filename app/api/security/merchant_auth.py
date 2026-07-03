from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.settings import settings
from app.utils.exceptions import ErrorResponse
from app.utils.logger import logger

Authorization = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]


async def get_merchant_from_bearer(auth: Authorization) -> UUID:
    """Validate merchant API key and return merchant ID."""
    if auth.credentials != settings.LDB_API_KEY:
        logger.warning("Merchant bearer auth validation failed")
        raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Unauthorized access")
    return UUID(settings.DEFAULT_MERCHANT_ID)


ValidMerchant = Annotated[UUID, Depends(get_merchant_from_bearer)]
