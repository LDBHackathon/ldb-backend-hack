from fastapi import Request, Response, status
from fastapi_limiter.depends import _BaseRateLimiter
from pyrate_limiter import Duration, InMemoryBucket, Limiter, Rate

from app.integrations.cache import sync_cache_factory
from app.utils.exceptions import RateLimitErrorResponse
from app.utils.logger import logger

_RATE = Rate(70, Duration.MINUTE)


async def _default_key_generator(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0]
    elif request.client:
        ip = request.client.host
    else:
        ip = "anonymous"
    return f"{ip}:{request.method}:{request.scope['path']}"


def _callback(*_args: object, **_kwargs: object) -> None:
    raise RateLimitErrorResponse(
        status=status.HTTP_429_TOO_MANY_REQUESTS,
        message="Too many requests, please try again later.",
    )


def _build_in_memory_limiter() -> Limiter:
    return Limiter(InMemoryBucket([_RATE]))


def _build_limiter() -> Limiter:
    try:
        from pyrate_limiter import RedisBucket

        redis_client = sync_cache_factory()
        redis_client.ping()
        return Limiter(
            RedisBucket.init(
                rates=[_RATE],
                redis=redis_client,
                bucket_key="ldb_dva_api_rate_limit",
            )  # type: ignore
        )
    except Exception as exc:
        logger.warning(
            "Redis rate limiter unavailable; falling back to in-memory limiter",
            error=str(exc),
        )
        return _build_in_memory_limiter()


class CompatibleRateLimiter(_BaseRateLimiter):
    _fallback_limiter: Limiter = _build_in_memory_limiter()
    _fallback_engaged: bool = False

    def _engage_fallback(self, exc: Exception) -> None:
        if not self._fallback_engaged:
            logger.warning(
                "Redis rate limiter failed at runtime; switched to in-memory limiter",
                error=str(exc),
            )
            self._fallback_engaged = True
        self.limiter = self._fallback_limiter

    async def __call__(self, request: Request, response: Response) -> None:
        rate_key = await self.identifier(request)
        try:
            success = await self.limiter.try_acquire_async(rate_key, blocking=self.blocking)
        except Exception as exc:
            self._engage_fallback(exc)
            success = await self.limiter.try_acquire_async(rate_key, blocking=self.blocking)
        if not success:
            return await self.callback(request, response)


RateLimiter = CompatibleRateLimiter(
    limiter=_build_limiter(),
    identifier=_default_key_generator,
    callback=_callback,
)
