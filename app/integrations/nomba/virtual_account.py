from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from app.integrations.nomba.auth import NombaAuthService
from app.integrations.nomba.helpers import (
    format_nomba_expected_amount,
    normalize_nomba_account_name,
    parse_virtual_account_response,
)
from app.settings import settings
from app.utils.logger import logger


class NombaVirtualAccountService:
    """Nomba dedicated virtual account API client."""

    @classmethod
    def _extract_nomba_error(cls, body: dict[str, Any]) -> str | None:
        """Return business-level API error when Nomba responds with non-success payload."""
        code = str(body.get("code", "")).strip()
        status_flag = body.get("status")
        if code in {"00", "0"} and status_flag in {True, None}:
            return None
        if "message" in body and body["message"]:
            return str(body["message"])
        if "description" in body and body["description"]:
            return str(body["description"])
        return None

    @classmethod
    def _create_url(cls, sub_account_id: str | None = None) -> str:
        base = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/accounts/virtual"
        if sub_account_id:
            return f"{base}/{sub_account_id}"
        if settings.NOMBA_SUB_ACCOUNT_ID:
            return f"{base}/{settings.NOMBA_SUB_ACCOUNT_ID}"
        return base

    @classmethod
    async def create(
        cls,
        account_ref: str,
        account_name: str,
        *,
        sub_account_id: str | None = None,
        bvn: str | None = None,
        expiry_date: datetime | None = None,
        expected_amount: Decimal | None = None,
    ) -> dict[str, Any]:
        """Create a virtual account via Nomba."""
        url = cls._create_url(sub_account_id)
        payload: dict[str, Any] = {
            "accountRef": account_ref,
            "accountName": normalize_nomba_account_name(account_name),
        }
        if bvn:
            payload["bvn"] = bvn
        if expiry_date:
            payload["expiryDate"] = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
        if expected_amount is not None:
            payload["expectedAmount"] = format_nomba_expected_amount(expected_amount)

        try:
            headers = await NombaAuthService.auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                body_error = cls._extract_nomba_error(body)
                if body_error:
                    logger.warning(
                        "Nomba virtual account creation rejected",
                        account_ref=account_ref,
                        status_code=response.status_code,
                        account_id_header=headers.get("accountId"),
                        response_body=body,
                    )
                    return {
                        "success": False,
                        "data": None,
                        "status_code": response.status_code,
                        "message": body_error,
                    }
                parsed = parse_virtual_account_response(body.get("data", body))
                logger.info(
                    "Nomba virtual account created",
                    account_ref=account_ref,
                    account_number=parsed.get("account_number"),
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
                "Nomba virtual account creation failed",
                account_ref=account_ref,
                status_code=exc.response.status_code,
                account_id_header=settings.NOMBA_ACCOUNT_ID,
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
    async def update(
        cls,
        identifier: str,
        *,
        account_name: str | None = None,
        expected_amount: Decimal | None = None,
        new_account_ref: str | None = None,
    ) -> dict[str, Any]:
        """Update a virtual account by accountRef or account number."""
        url = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/accounts/virtual/{identifier}"
        payload: dict[str, Any] = {}
        if account_name is not None:
            payload["accountName"] = normalize_nomba_account_name(account_name)
        if expected_amount is not None:
            payload["expectedAmount"] = format_nomba_expected_amount(expected_amount)
        if new_account_ref is not None:
            payload["newAccountRef"] = new_account_ref

        if not payload:
            return {
                "success": False,
                "data": None,
                "status_code": 400,
                "message": "No virtual account fields provided for update",
            }

        try:
            headers = await NombaAuthService.auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(url, json=payload, headers=headers)
                response.raise_for_status()
                body = response.json()
                return {
                    "success": True,
                    "data": body.get("data", body),
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
        """Update virtual account holder name."""
        return await cls.update(account_ref, account_name=account_name)
