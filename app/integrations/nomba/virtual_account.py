from typing import Any

import httpx

from app.integrations.nomba.auth import NombaAuthService
from app.settings import settings
from app.utils.logger import logger


class NombaVirtualAccountService:
    """Nomba dedicated virtual account API client."""

    @classmethod
    async def create(
        cls, account_ref: str, account_name: str, currency: str = "NGN"
    ) -> dict[str, Any]:
        """Create a permanent virtual account via Nomba."""
        url = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/accounts/virtual"
        payload: dict[str, str] = {
            "accountRef": account_ref,
            "accountName": account_name,
            "currency": currency,
        }
        if settings.NOMBA_SUB_ACCOUNT_ID:
            payload["accountHolderId"] = settings.NOMBA_SUB_ACCOUNT_ID

        try:
            headers = await NombaAuthService._auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                data = body.get("data", body)
                logger.info(
                    "Nomba virtual account created",
                    account_ref=account_ref,
                    account_number=data.get("accountNumber"),
                )
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status_code,
                }
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Nomba virtual account creation failed",
                account_ref=account_ref,
                status_code=exc.response.status_code,
            )
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
    async def update_account_name(cls, account_ref: str, account_name: str) -> dict[str, Any]:
        """Update virtual account holder name when supported by Nomba."""
        url = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/accounts/virtual/{account_ref}"
        payload = {"accountName": account_name}
        try:
            headers = await NombaAuthService._auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                return {
                    "success": True,
                    "data": body.get("data", body),
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
