import redis
import redis.asyncio

from app.settings import settings

_REDIS_POOL_OPTIONS = {
    "decode_responses": True,
    "health_check_interval": 30,
    "socket_keepalive": True,
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True,
}

redis_pool = redis.asyncio.ConnectionPool.from_url(  # type: ignore
    settings.REDIS_URL,
    **_REDIS_POOL_OPTIONS,
)

sync_redis_pool = redis.ConnectionPool.from_url(  # type: ignore
    settings.REDIS_URL,
    **_REDIS_POOL_OPTIONS,
)


def redis_factory() -> redis.asyncio.Redis:
    """Get an async Redis client from the connection pool."""
    return redis.asyncio.Redis.from_pool(redis_pool)


def sync_redis_factory() -> redis.Redis:
    """Get a synchronous Redis client from the connection pool."""
    return redis.Redis.from_pool(sync_redis_pool)
