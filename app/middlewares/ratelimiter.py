from fastapi import Request, Response, status
from fastapi_limiter.depends import _BaseRateLimiter
from pyrate_limiter import Duration, InMemoryBucket, Limiter, Rate

from app.integrations.cache import sync_cache_factory
from app.utils.exceptions import RateLimitErrorResponse
from app.utils.logger import logger


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


def _build_limiter() -> Limiter:
    try:
        from pyrate_limiter import RedisBucket

        redis_client = sync_cache_factory()
        redis_client.ping()
        return Limiter(
            RedisBucket.init(
                rates=[Rate(70, Duration.MINUTE)],
                redis=redis_client,
                bucket_key="ldb_dva_api_rate_limit",
            )  # type: ignore
        )
    except Exception as exc:
        logger.warning(
            "Redis rate limiter unavailable; falling back to in-memory limiter",
            error=str(exc),
        )
        return Limiter(InMemoryBucket([Rate(70, Duration.MINUTE)]))


class CompatibleRateLimiter(_BaseRateLimiter):
    async def __call__(self, request: Request, response: Response) -> None:
        rate_key = await self.identifier(request)
        success = await self.limiter.try_acquire_async(rate_key, blocking=self.blocking)
        if not success:
            return await self.callback(request, response)


RateLimiter = CompatibleRateLimiter(
    limiter=_build_limiter(),
    identifier=_default_key_generator,
    callback=_callback,
)
