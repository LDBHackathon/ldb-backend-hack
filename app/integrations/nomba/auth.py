from typing import Any

import httpx

from app.constants import NOMBA_TOKEN_CACHE_KEY, NOMBA_TOKEN_TTL_SECONDS
from app.integrations.cache import cache_factory
from app.settings import settings
from app.utils.logger import logger


class NombaAuthService:
    """Nomba OAuth client credentials token management."""

    @classmethod
    async def get_access_token(cls) -> dict[str, Any]:
        """Return a cached or freshly fetched Nomba access token."""
        redis = cache_factory()
        try:
            cached = await redis.get(NOMBA_TOKEN_CACHE_KEY)
            if cached:
                return {"success": True, "data": cached, "status_code": 200}
        except Exception as exc:
            logger.warning("Nomba token cache read failed", error=str(exc))

        if not settings.NOMBA_CLIENT_ID or not settings.NOMBA_CLIENT_SECRET:
            return {
                "success": False,
                "data": None,
                "status_code": 503,
                "message": "Nomba credentials are not configured",
            }

        url = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/auth/token/issue"
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.NOMBA_CLIENT_ID,
            "client_secret": settings.NOMBA_CLIENT_SECRET,
        }

        headers = {"Content-Type": "application/json"}
        if settings.NOMBA_ACCOUNT_ID:
            headers["accountId"] = settings.NOMBA_ACCOUNT_ID

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                token = body.get("data", {}).get("access_token") or body.get(
                    "access_token"
                )
                if not token:
                    return {
                        "success": False,
                        "data": None,
                        "status_code": response.status_code,
                        "message": "Nomba token response missing access_token",
                    }

                try:
                    await redis.setex(
                        NOMBA_TOKEN_CACHE_KEY, NOMBA_TOKEN_TTL_SECONDS, token
                    )
                except Exception as exc:
                    logger.warning("Nomba token cache write failed", error=str(exc))

                return {
                    "success": True,
                    "data": token,
                    "status_code": response.status_code,
                }
        except httpx.HTTPStatusError as exc:
            return {
                "success": False,
                "data": None,
                "status_code": exc.response.status_code,
                "message": exc.response.text,
            }
        except httpx.HTTPError as exc:
            return {
                "success": False,
                "data": None,
                "status_code": 502,
                "message": str(exc),
            }

    @classmethod
    async def _auth_headers(cls) -> dict[str, str]:
        token_result = await cls.get_access_token()
        if not token_result["success"]:
            raise RuntimeError(token_result.get("message", "Unable to fetch Nomba token"))
        headers = {
            "Authorization": f"Bearer {token_result['data']}",
            "Content-Type": "application/json",
        }
        if settings.NOMBA_ACCOUNT_ID:
            headers["accountId"] = settings.NOMBA_ACCOUNT_ID
        return headers
