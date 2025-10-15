"""No-op cache service implementation.

This implementation does nothing - used when caching is disabled.
"""

from typing import Any


class NoOpCacheService:
    """No-op cache implementation that does nothing.

    This is used when caching is disabled. All operations succeed
    but no actual caching takes place.

    This allows the rest of the code to use cache methods without
    checking if cache is enabled.
    """

    async def get(self, key: str) -> Any | None:
        """Always returns None (cache miss).

        Args:
            key: Cache key (ignored)

        Returns:
            None
        """
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Does nothing, always succeeds.

        Args:
            key: Cache key (ignored)
            value: Value (ignored)
            ttl: TTL (ignored)

        Returns:
            True
        """
        return True

    async def delete(self, key: str) -> bool:
        """Does nothing, always returns False.

        Args:
            key: Cache key (ignored)

        Returns:
            False (nothing deleted)
        """
        return False

    async def delete_pattern(self, pattern: str) -> int:
        """Does nothing, always returns 0.

        Args:
            pattern: Pattern (ignored)

        Returns:
            0 (nothing deleted)
        """
        return 0

    async def exists(self, key: str) -> bool:
        """Always returns False.

        Args:
            key: Cache key (ignored)

        Returns:
            False
        """
        return False

    async def clear(self) -> bool:
        """Does nothing, always succeeds.

        Returns:
            True
        """
        return True

    async def close(self) -> None:
        """Does nothing.

        No resources to clean up.
        """
        pass
