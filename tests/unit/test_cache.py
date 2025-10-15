"""Unit tests for SDK cache implementations."""

import pytest

from permission_sdk.cache.memory import InMemoryCacheService
from permission_sdk.cache.noop import NoOpCacheService
from permission_sdk.cache.permission_cache import PermissionCacheManager


class TestInMemoryCacheService:
    """Tests for in-memory cache service."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test setting and getting values."""
        cache = InMemoryCacheService()

        # Set a value
        result = await cache.set("test_key", "test_value")
        assert result is True

        # Get the value
        value = await cache.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = InMemoryCacheService()
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting keys."""
        cache = InMemoryCacheService()

        await cache.set("test_key", "test_value")
        deleted = await cache.delete("test_key")
        assert deleted is True

        # Verify it's gone
        value = await cache.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_pattern(self):
        """Test pattern-based deletion."""
        cache = InMemoryCacheService()

        # Set multiple keys
        await cache.set("perm:check:user:123", True)
        await cache.set("perm:check:user:456", False)
        await cache.set("perm:check:role:admin", True)

        # Delete all user checks
        deleted = await cache.delete_pattern("perm:check:user:*")
        assert deleted == 2

        # Verify correct keys were deleted
        assert await cache.get("perm:check:user:123") is None
        assert await cache.get("perm:check:user:456") is None
        assert await cache.get("perm:check:role:admin") is True

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        import asyncio

        cache = InMemoryCacheService()

        # Set value with 0.1 second TTL
        await cache.set("test_key", "test_value", ttl=0)

        # Wait for expiration
        await asyncio.sleep(0.1)

        # Value should be expired
        value = await cache.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing all keys."""
        cache = InMemoryCacheService()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        result = await cache.clear()
        assert result is True

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


class TestNoOpCacheService:
    """Tests for no-op cache service."""

    @pytest.mark.asyncio
    async def test_get_always_returns_none(self):
        """Test get always returns None."""
        cache = NoOpCacheService()
        value = await cache.get("any_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_set_always_succeeds(self):
        """Test set always returns True."""
        cache = NoOpCacheService()
        result = await cache.set("key", "value")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_always_returns_false(self):
        """Test delete always returns False."""
        cache = NoOpCacheService()
        result = await cache.delete("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_pattern_always_returns_zero(self):
        """Test delete_pattern always returns 0."""
        cache = NoOpCacheService()
        result = await cache.delete_pattern("*")
        assert result == 0


class TestPermissionCacheManager:
    """Tests for permission cache manager."""

    @pytest.mark.asyncio
    async def test_build_check_key_sorted_subjects(self):
        """Test that cache keys are consistent regardless of subject order."""
        cache = InMemoryCacheService()
        manager = PermissionCacheManager(cache)

        # Different order, same subjects
        key1 = manager._build_check_key(
            ["user:123", "role:editor"], "docs", "read", "tenant1", None
        )
        key2 = manager._build_check_key(
            ["role:editor", "user:123"], "docs", "read", "tenant1", None
        )

        # Keys should be identical
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_cache_check_result(self):
        """Test caching permission check results."""
        cache = InMemoryCacheService()
        manager = PermissionCacheManager(cache)

        # Cache a result
        await manager.set_check_result(
            ["user:123"], "docs", "read", True, tenant_id="tenant1", object_id=None, ttl=300
        )

        # Retrieve it
        result = await manager.get_check_result(
            ["user:123"], "docs", "read", tenant_id="tenant1", object_id=None
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_subject(self):
        """Test invalidating all checks for a subject."""
        cache = InMemoryCacheService()
        manager = PermissionCacheManager(cache)

        # Cache multiple results for user:123
        await manager.set_check_result(
            ["user:123"], "docs", "read", True, None, None, 300
        )
        await manager.set_check_result(
            ["user:123"], "docs", "write", False, None, None, 300
        )
        await manager.set_check_result(
            ["user:456"], "docs", "read", True, None, None, 300
        )

        # Invalidate user:123
        deleted = await manager.invalidate_subject("user:123")
        assert deleted == 2

        # Verify user:123 checks are gone
        assert await manager.get_check_result(["user:123"], "docs", "read") is None
        assert await manager.get_check_result(["user:123"], "docs", "write") is None

        # But user:456 is still there
        assert await manager.get_check_result(["user:456"], "docs", "read") is True

    @pytest.mark.asyncio
    async def test_invalidate_multiple_subjects(self):
        """Test invalidating multiple subjects at once."""
        cache = InMemoryCacheService()
        manager = PermissionCacheManager(cache)

        # Cache results for multiple subjects
        await manager.set_check_result(["user:123"], "docs", "read", True, None, None, 300)
        await manager.set_check_result(["user:456"], "docs", "read", True, None, None, 300)
        await manager.set_check_result(["user:789"], "docs", "read", True, None, None, 300)

        # Invalidate user:123 and user:456
        deleted = await manager.invalidate_subjects(["user:123", "user:456"])
        assert deleted == 2

        # Verify they're gone
        assert await manager.get_check_result(["user:123"], "docs", "read") is None
        assert await manager.get_check_result(["user:456"], "docs", "read") is None

        # But user:789 remains
        assert await manager.get_check_result(["user:789"], "docs", "read") is True
