from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from app.services.webhook_forwarder import WebhookForwarderService


@pytest.mark.asyncio
async def test_emit_test_event_delivers_without_event_filter() -> None:
    merchant_id = uuid4()
    registration = MagicMock()
    registration.url = "https://example.com/hook"
    registration.secret = "whsec_test"
    registration.events = ["account.created"]

    response = MagicMock()
    response.is_success = True
    response.status_code = 200

    service = WebhookForwarderService()
    with (
        patch(
            "app.services.webhook_forwarder.WebhookRegistration.filter",
        ) as mock_filter,
        patch("app.services.webhook_forwarder.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_filter.return_value.all = AsyncMock(return_value=[registration])
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=response)
        mock_client_cls.return_value = mock_client

        result = await service.emit_test_event(merchant_id)

    assert result["delivered"] is True
    assert result["attempts"][0]["status_code"] == 200
    mock_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_emit_test_event_reports_unreachable_url() -> None:
    merchant_id = uuid4()
    registration = MagicMock()
    registration.url = "https://example.com/hook"
    registration.secret = "whsec_test"
    registration.events = []

    service = WebhookForwarderService()
    with (
        patch(
            "app.services.webhook_forwarder.WebhookRegistration.filter",
        ) as mock_filter,
        patch("app.services.webhook_forwarder.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_filter.return_value.all = AsyncMock(return_value=[registration])
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client_cls.return_value = mock_client

        result = await service.emit_test_event(merchant_id)

    assert result["delivered"] is False
    assert "connection refused" in result["attempts"][0]["error"]
