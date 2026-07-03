import redis
import redis.asyncio

from app.settings import settings

redis_pool = redis.asyncio.ConnectionPool.from_url(  # type: ignore
    settings.REDIS_URL, decode_responses=True
)

sync_redis_pool = redis.ConnectionPool.from_url(  # type: ignore
    settings.REDIS_URL, decode_responses=True
)


def redis_factory() -> redis.asyncio.Redis:
    """Get an async Redis client from the connection pool."""
    return redis.asyncio.Redis.from_pool(redis_pool)


def sync_redis_factory() -> redis.Redis:
    """Get a synchronous Redis client from the connection pool."""
    return redis.Redis.from_pool(sync_redis_pool)
