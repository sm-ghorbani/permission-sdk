"""Base cache service protocol.

This module defines the interface that all cache implementations must follow.
"""

from typing import Any, Protocol


class CacheService(Protocol):
    """Protocol defining the cache service interface.

    All cache implementations (Redis, in-memory, no-op)
    must implement these methods.This allows for easy swapping of
    cache backends without changing application code.
    """

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from cache.

        Args:
            key: Cache key to retrieve

        Returns:
            The cached value if found, None otherwise
        """
        ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key to store under
            value: Value to cache (must be serializable)
            ttl: Time-to-live in seconds (None for no expiration)

        Returns:
            True if successful, False otherwise
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete a single key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist
        """
        ...

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "perm:check:user:*")

        Returns:
            Number of keys deleted
        """
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        ...

    async def clear(self) -> bool:
        """Clear all keys from cache.

        This is primarily useful for testing.

        Returns:
            True if successful
        """
        ...

    async def close(self) -> None:
        """Close the cache connection and cleanup resources.

        Should be called when shutting down the application.
        """
        ...
