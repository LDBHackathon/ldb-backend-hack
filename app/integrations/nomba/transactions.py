from datetime import date
from typing import Any

import httpx

from app.integrations.nomba.auth import NombaAuthService
from app.settings import settings


class NombaTransactionService:
    """Nomba transactions API client."""

    @classmethod
    async def list_transactions(
        cls,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Fetch recent Nomba transactions for nightly reconciliation."""
        url = f"{settings.NOMBA_BASE_URL.rstrip('/')}/v1/transactions"
        params: dict[str, Any] = {"limit": limit}
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()

        try:
            headers = await NombaAuthService._auth_headers()
            async with httpx.AsyncClient(timeout=30.0) as client:
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
