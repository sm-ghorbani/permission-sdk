"""Cache provider for creating cache service instances.

This module provides factory functions to create cache service instances
based on SDK configuration.
"""

import logging
from typing import TYPE_CHECKING

from redis.asyncio import Redis

from permission_sdk.cache.base import CacheService
from permission_sdk.cache.memory import InMemoryCacheService
from permission_sdk.cache.noop import NoOpCacheService
from permission_sdk.cache.redis import RedisCacheService

if TYPE_CHECKING:
    from permission_sdk.config import SDKConfig


logger = logging.getLogger(__name__)


def create_cache_service(config: "SDKConfig") -> CacheService:
    """Create a cache service instance based on configuration.

    This function creates the appropriate cache implementation based on
    the SDK configuration settings.

    Args:
        config: SDK configuration with cache settings

    Returns:
        The initialized cache service instance

    Raises:
        ValueError: If cache_type is not recognized
        RuntimeError: If Redis connection fails and fallback is not possible
    """
    # If caching is disabled, return no-op cache
    if not config.cache_enabled:
        logger.debug("Cache disabled - using no-op cache")
        return NoOpCacheService()

    cache_type = config.cache_type.lower()

    if cache_type == "redis":
        # Validate Redis URL
        if not config.cache_redis_url:
            logger.warning(
                "Redis cache requested but cache_redis_url not configured. "
                "Falling back to memory cache."
            )
            return InMemoryCacheService()

        # Initialize Redis cache
        try:
            redis_client = Redis.from_url(
                config.cache_redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle JSON serialization
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            logger.info(
                f"Created Redis cache service: {config.cache_redis_url}",
                extra={
                    "cache_type": "redis",
                    "redis_url": config.cache_redis_url,
                },
            )
            return RedisCacheService(redis_client)

        except Exception as e:
            logger.warning(
                f"Failed to create Redis cache: {e}."
                " Falling back to memory cache",
                extra={"cache_type": "redis", "error": str(e)},
            )
            return InMemoryCacheService()

    elif cache_type == "memory":
        # Initialize in-memory cache
        logger.info(
            "Created in-memory cache service",
            extra={"cache_type": "memory"},
        )
        return InMemoryCacheService()

    elif cache_type == "none":
        # Explicitly disabled
        logger.debug("Cache type 'none' - using no-op cache")
        return NoOpCacheService()

    else:
        msg = f"Unknown cache type: {cache_type}."
        " Use 'redis', 'memory', or 'none'"
        raise ValueError(msg)


async def create_cache_service_async(config: "SDKConfig") -> CacheService:
    """Create a cache service instance asynchronously.

    This async version allows for connection
    testing before returning the cache.

    Args:
        config: SDK configuration with cache settings

    Returns:
        The initialized cache service instance

    Raises:
        ValueError: If cache_type is not recognized
    """
    cache = create_cache_service(config)

    # If it's a Redis cache, test the connection
    if isinstance(cache, RedisCacheService):
        try:
            is_healthy = await cache.ping()
            if not is_healthy:
                logger.warning("Redis connection test failed. "
                               "Falling back to memory cache.")
                await cache.close()
                return InMemoryCacheService()
        except Exception as e:
            logger.warning(
                f"Redis connection test failed: {e}."
                " Falling back to memory cache.",
                extra={"error": str(e)},
            )
            await cache.close()
            return InMemoryCacheService()

    return cache
