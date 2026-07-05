from datetime import date
from typing import Any

import httpx

from app.integrations.nomba.auth import NombaAuthService
from app.integrations.nomba.helpers import format_nomba_date_range
from app.settings import settings


class NombaTransactionService:
    """Nomba transactions API client."""

    @classmethod
    def _list_url(cls, sub_account_id: str | None = None) -> str:
        base = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/transactions/accounts"
        scoped_id = sub_account_id or settings.NOMBA_SUB_ACCOUNT_ID
        if scoped_id:
            return f"{base}/{scoped_id}"
        return base

    @classmethod
    async def list_transactions(
        cls,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        cursor: str | None = None,
        *,
        sub_account_id: str | None = None,
    ) -> dict[str, Any]:
        """Fetch Nomba account transactions for nightly reconciliation."""
        url = cls._list_url(sub_account_id)
        params: dict[str, Any] = {"limit": limit}
        if start_date and end_date:
            date_from, date_to = format_nomba_date_range(start_date, end_date)
            params["dateFrom"] = date_from
            params["dateTo"] = date_to
        if cursor:
            params["cursor"] = cursor

        scoped = sub_account_id or settings.NOMBA_SUB_ACCOUNT_ID

        try:
            headers = await NombaAuthService.auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
                if scoped:
                    response = await client.post(url, json={}, params=params, headers=headers)
                else:
                    response = await client.get(url, params=params, headers=headers)
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
