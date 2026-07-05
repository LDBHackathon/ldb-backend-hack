from typing import Any

import httpx

from app.integrations.nomba.auth import NombaAuthService
from app.integrations.nomba.helpers import normalize_nomba_account_name
from app.settings import settings
from app.utils.logger import logger


def _parse_sub_account_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "account_id": data.get("accountId") or data.get("id"),
        "account_ref": data.get("accountRef"),
        "account_name": data.get("accountName"),
        "status": data.get("status"),
        "raw": data,
    }


class NombaSubAccountService:
    """Nomba sub-account API client (create is deprecated; attempt + fetch)."""

    @classmethod
    def _base_url(cls) -> str:
        return settings.NOMBA_BASE_URL.rstrip("/")

    @classmethod
    async def create(cls, account_name: str, account_ref: str) -> dict[str, Any]:
        """Attempt deprecated sub-account creation API."""
        url = f"{cls._base_url()}/v1/accounts/sub-account"
        payload = {
            "accountName": normalize_nomba_account_name(account_name),
            "accountRef": account_ref,
        }

        try:
            headers = await NombaAuthService.auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                parsed = _parse_sub_account_response(body.get("data", body))
                logger.info(
                    "Nomba sub-account created",
                    account_ref=account_ref,
                    account_id=parsed.get("account_id"),
                )
                return {
                    "success": True,
                    "data": parsed,
                    "status_code": response.status_code,
                }
        except ValueError as exc:
            return {
                "success": False,
                "data": None,
                "status_code": 400,
                "message": str(exc),
            }
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Nomba sub-account creation failed",
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
    async def fetch_details(
        cls,
        *,
        account_id: str | None = None,
        account_ref: str | None = None,
    ) -> dict[str, Any]:
        """Fetch sub-account details by Nomba account ID or reference."""
        if not account_id and not account_ref:
            return {
                "success": False,
                "data": None,
                "status_code": 400,
                "message": "account_id or account_ref is required",
            }

        url = f"{cls._base_url()}/v1/accounts/sub-account-details"
        params: dict[str, str] = {}
        if account_id:
            params["accountId"] = account_id
        if account_ref:
            params["accountRef"] = account_ref

        try:
            headers = await NombaAuthService.auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                body = response.json()
                parsed = _parse_sub_account_response(body.get("data", body))
                return {
                    "success": True,
                    "data": parsed,
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
    async def fetch_balance(cls, sub_account_id: str) -> dict[str, Any]:
        """Fetch sub-account balance."""
        url = f"{cls._base_url()}/v1/accounts/{sub_account_id}/balance"

        try:
            headers = await NombaAuthService.auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
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
