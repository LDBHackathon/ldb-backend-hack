from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.security.merchant_auth import get_merchant_id_from_bearer
from app.enums.merchant import MerchantStatus
from app.models.merchants import Merchant
from app.settings import settings
from app.utils.exceptions import ErrorResponse
from app.utils.session_tokens import decode_session_token

_bearer = HTTPBearer(auto_error=False)


async def get_merchant_from_session(
    ldb_session: Annotated[str | None, Cookie(alias=settings.SESSION_COOKIE_NAME)] = None,
) -> UUID | None:
    """Return merchant ID from session cookie when present."""
    if not ldb_session:
        return None
    try:
        payload = decode_session_token(ldb_session)
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


async def get_portal_merchant(
    session_merchant: Annotated[UUID | None, Depends(get_merchant_from_session)],
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> UUID:
    """Authenticate portal requests via session cookie or Bearer API key."""
    if session_merchant is not None:
        return session_merchant
    if bearer is not None:
        return await get_merchant_id_from_bearer(bearer)
    raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Unauthorized access")


async def get_active_portal_merchant(
    merchant_id: Annotated[UUID, Depends(get_portal_merchant)],
) -> UUID:
    """Require an active merchant for post-onboarding portal routes."""
    merchant = await Merchant.get_or_none(id=merchant_id)
    if merchant is None:
        raise ErrorResponse(status.HTTP_401_UNAUTHORIZED, "Unauthorized access")

    if merchant.status == MerchantStatus.SUSPENDED:
        raise ErrorResponse(status.HTTP_403_FORBIDDEN, "Merchant account suspended")
    if merchant.status != MerchantStatus.ACTIVE:
        raise ErrorResponse(
            status.HTTP_403_FORBIDDEN,
            "Complete KYB onboarding before accessing this resource",
        )

    return merchant_id


ValidPortalMerchant = Annotated[UUID, Depends(get_portal_merchant)]
ValidActivePortalMerchant = Annotated[UUID, Depends(get_active_portal_merchant)]
