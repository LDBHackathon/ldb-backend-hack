from unittest.mock import AsyncMock

import pytest
from fastapi import Response
from starlette.requests import Request

from app.middlewares.ratelimiter import CompatibleRateLimiter, _default_key_generator


class _FlakyLimiter:
    def __init__(self) -> None:
        self.calls = 0

    async def try_acquire_async(self, _key: str, *, blocking: bool) -> bool:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("redis connection closed")
        return True


class _DenyLimiter:
    async def try_acquire_async(self, _key: str, *, blocking: bool) -> bool:
        return False


def _request(path: str = "/v1/customers") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [],
        "client": ("127.0.0.1", 42000),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_rate_limiter_falls_back_to_in_memory_on_runtime_error() -> None:
    callback = AsyncMock()
    limiter = CompatibleRateLimiter(
        limiter=_FlakyLimiter(),
        identifier=_default_key_generator,
        callback=callback,
    )
    limiter._fallback_engaged = False

    await limiter(_request(), Response())

    assert limiter._fallback_engaged is True
    assert callback.await_count == 0


@pytest.mark.asyncio
async def test_rate_limiter_calls_callback_when_quota_exceeded() -> None:
    callback = AsyncMock()
    limiter = CompatibleRateLimiter(
        limiter=_DenyLimiter(),
        identifier=_default_key_generator,
        callback=callback,
    )

    await limiter(_request("/v1/over-limit"), Response())

    callback.assert_awaited_once()
