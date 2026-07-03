from app.integrations.cache.redis import redis_factory, sync_redis_factory

__all__ = ["cache_factory", "sync_cache_factory"]

cache_factory = redis_factory
sync_cache_factory = sync_redis_factory
