"""In-memory cache service implementation.

This implementation is useful for development and testing environments
where Redis is not available or needed.
"""

import fnmatch
import time
from typing import Any


class InMemoryCacheService:
    """In-memory cache implementation using a dictionary.

    This implementation stores cache entries in
    memory with optional TTL support.It's suitable for
    single-process deployments and testing.

    Note: This cache is NOT shared across multiple processes or servers.
    For production with multiple workers, use RedisCacheService instead.
    """

    def __init__(self) -> None:
        """Initialize the in-memory cache."""
        self._cache: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from cache.

        Args:
            key: Cache key to retrieve

        Returns:
            The cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]

        # Check if expired
        if expires_at is not None and time.time() > expires_at:
            # Remove expired entry
            del self._cache[key]
            return None

        return value

    async def set(
        self, key: str, value: Any, ttl: int | None = None
    ) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key to store under
            value: Value to cache
            ttl: Time-to-live in seconds (None for no expiration)

        Returns:
            True (always successful for in-memory cache)
        """
        expires_at = time.time() + ttl if ttl is not None else None
        self._cache[key] = (value, expires_at)
        return True

    async def delete(self, key: str) -> bool:
        """Delete a single key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Uses fnmatch for pattern matching (*, ?, [seq], [!seq]).

        Args:
            pattern: Pattern to match (e.g., "perm:check:user:*")

        Returns:
            Number of keys deleted
        """
        matching_keys = [
            key for key in self._cache if fnmatch.fnmatch(key, pattern)
        ]

        for key in matching_keys:
            del self._cache[key]

        return len(matching_keys)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and not expired, False otherwise
        """
        # Use get to handle expiration check
        value = await self.get(key)
        return value is not None

    async def clear(self) -> bool:
        """Clear all keys from cache.

        Returns:
            True (always successful)
        """
        self._cache.clear()
        return True

    async def close(self) -> None:
        """Close the cache connection.

        For in-memory cache, this just clears the cache.
        """
        self._cache.clear()

    def __len__(self) -> int:
        """Return the number of entries in cache.

        Note: This includes expired entries that haven't been cleaned up yet.
        """
        return len(self._cache)
