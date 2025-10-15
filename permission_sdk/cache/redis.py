"""Redis cache service implementation.

This implementation uses Redis as the cache backend for production deployments.
"""

import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class RedisCacheService:
    """Redis cache implementation.

    This implementation uses Redis for distributed caching across multiple
    processes and servers. Suitable for production deployments.

    The cache stores values as JSON strings for maximum compatibility.
    """

    def __init__(self, redis_client: Redis) -> None:
        """Initialize the Redis cache service.

        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from cache.

        Args:
            key: Cache key to retrieve

        Returns:
            The cached value if found, None otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            value = await self.redis.get(key)
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)

        except RedisError as e:
            # Log error but don't fail - cache misses are acceptable
            logger.warning(
                f"Redis GET error for key {key}: {e}",
                extra={"key": key, "operation": "get"},
            )
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key to store under
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (None for no expiration)

        Returns:
            True if successful, False otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Serialize to JSON
            serialized = json.dumps(value)

            if ttl is not None:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)

            return True

        except (RedisError, TypeError, ValueError) as e:
            # TypeError/ValueError from JSON serialization
            logger.warning(
                f"Redis SET error for key {key}: {e}",
                extra={"key": key, "operation": "set"},
            )
            return False

    async def delete(self, key: str) -> bool:
        """Delete a single key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            result = await self.redis.delete(key)
            return result > 0

        except RedisError as e:
            logger.warning(
                f"Redis DELETE error for key {key}: {e}",
                extra={"key": key, "operation": "delete"},
            )
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Uses Redis SCAN for safe iteration over large keyspaces.

        Args:
            pattern: Pattern to match (e.g., "perm:check:user:*")

        Returns:
            Number of keys deleted

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            deleted_count = 0
            cursor = 0

            # Use SCAN to iterate without blocking
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=100
                )

                if keys:
                    deleted_count += await self.redis.delete(*keys)

                if cursor == 0:
                    break

            return deleted_count

        except RedisError as e:
            logger.warning(
                f"Redis DELETE_PATTERN error for pattern {pattern}: {e}",
                extra={"pattern": pattern, "operation": "delete_pattern"},
            )
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            result = await self.redis.exists(key)
            return result > 0

        except RedisError as e:
            logger.warning(
                f"Redis EXISTS error for key {key}: {e}",
                extra={"key": key, "operation": "exists"},
            )
            return False

    async def clear(self) -> bool:
        """Clear all keys from cache.

        WARNING: This flushes the entire Redis database!
        Use with caution in production.

        Returns:
            True if successful, False otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            await self.redis.flushdb()
            return True

        except RedisError as e:
            logger.warning(
                f"Redis FLUSHDB error: {e}",
                extra={"operation": "flushdb"},
            )
            return False

    async def close(self) -> None:
        """Close the Redis connection.

        Should be called when shutting down the application.
        """
        try:
            await self.redis.aclose()
        except RedisError as e:
            logger.warning(
                f"Redis CLOSE error: {e}",
                extra={"operation": "close"},
            )

    async def ping(self) -> bool:
        """Check if Redis connection is alive.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            await self.redis.ping()
            return True
        except RedisError:
            return False
