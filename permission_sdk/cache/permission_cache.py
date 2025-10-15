"""Permission-specific cache management for SDK.

This module provides cache key building and cache operations
specifically for the permission system with invalidation logic.
"""

import hashlib
import json
import logging
from typing import Any
from permission_sdk.cache.base import CacheService


logger = logging.getLogger(__name__)


class PermissionCacheManager:
    """Manages caching for permission operations in the SDK.

    This class handles:
    - Cache key generation with proper serialization
    - Getting/setting permission check results
    - Cache invalidation strategies for grant/revoke operations
    """

    def __init__(self, cache: CacheService, prefix: str = "perm_sdk") -> None:
        """Initialize the permission cache manager.

        Args:
            cache: The cache service to use
            prefix: Cache key prefix (default: "perm_sdk")
        """
        self.cache = cache
        self.prefix = prefix

    def _build_check_key(
        self,
        subjects: list[str],
        scope: str,
        action: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> str:
        """Build a cache key for permission check.

        Subjects are sorted to ensure consistent keys regardless of order.
        Example: ["user:1", "role:2"] and
        ["role:2", "user:1"] produce same key.

        Args:
            subjects: List of subject identifiers
            scope: Scope identifier
            action: Permission action
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            Cache key string
              (e.g., "perm_sdk:check:user:1|role:2:docs:read:tenant123:null")
        """
        # Sort subjects for consistent keys
        sorted_subjects = "|".join(sorted(subjects))

        # Build key parts
        parts = [
            self.prefix,
            "check",
            sorted_subjects,
            scope,
            action,
            tenant_id or "null",
            object_id or "null",
        ]

        return ":".join(parts)

    def _build_check_many_key(self, checks_hash: str) -> str:
        """Build a cache key for batch permission checks.

        Args:
            checks_hash: Hash of the check requests

        Returns:
            Cache key string
        """
        return f"{self.prefix}:check_many:{checks_hash}"

    def _hash_checks(self, checks: list[dict]) -> str:
        """Generate a stable hash for a list of permission checks.

        Args:
            checks: List of check request dictionaries

        Returns:
            Hash string (16 character hex)
        """
        # Sort checks and their subjects for consistency
        normalized = []
        for check in checks:
            normalized_check = {
                "subjects": tuple(sorted(check.get("subjects", []))),
                "scope": check.get("scope"),
                "action": check.get("action"),
                "tenant_id": check.get("tenant_id"),
                "object_id": check.get("object_id"),
                "check_id": check.get("check_id"),
            }
            normalized.append(normalized_check)

        # Sort by a stable key
        normalized.sort(key=lambda x: json.dumps(x, sort_keys=True))

        # Generate hash
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _build_subject_pattern(self, subject: str) -> str:
        """Build a pattern to match all checks for a subject.

        This is used for cache invalidation when permissions change.

        Args:
            subject: Subject identifier

        Returns:
            Pattern string for cache deletion
            (e.g., "perm_sdk:check:*user:123*")
        """
        return f"{self.prefix}:check:*{subject}*"

    async def get_check_result(
        self,
        subjects: list[str],
        scope: str,
        action: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> bool | None:
        """Get cached permission check result.

        Args:
            subjects: List of subject identifiers
            scope: Scope identifier
            action: Permission action
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            Cached result (True/False) or None if not cached
        """
        key = self._build_check_key(
            subjects,
            scope,
            action,
            tenant_id,
            object_id,
        )
        result = await self.cache.get(key)

        # Ensure we only return bool or None
        if result is None:
            return None

        return bool(result)

    async def set_check_result(
        self,
        subjects: list[str],
        scope: str,
        action: str,
        result: bool,
        tenant_id: str | None = None,
        object_id: str | None = None,
        ttl: int | None = None,
    ) -> bool:
        """Cache a permission check result.

        Args:
            subjects: List of subject identifiers
            scope: Scope identifier
            action: Permission action
            result: Check result to cache
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        key = self._build_check_key(
            subjects,
            scope,
            action,
            tenant_id,
            object_id,
        )
        return await self.cache.set(key, result, ttl=ttl)

    async def get_check_many_result(
        self,
        checks: list[dict],
    ) -> list[dict[str, Any]] | None:
        """Get cached batch permission check results.

        Args:
            checks: List of check request dictionaries

        Returns:
            Cached results or None if not cached
        """
        checks_hash = self._hash_checks(checks)
        key = self._build_check_many_key(checks_hash)

        return await self.cache.get(key)

    async def set_check_many_result(
        self,
        checks: list[dict],
        results: list[dict[str, Any]],
        ttl: int | None = None,
    ) -> bool:
        """Cache batch permission check results.

        Args:
            checks: List of check request dictionaries
            results: Check results to cache
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        checks_hash = self._hash_checks(checks)
        key = self._build_check_many_key(checks_hash)

        return await self.cache.set(key, results, ttl=ttl)

    async def invalidate_subject(self, subject: str) -> int:
        """Invalidate all cached checks for a subject.

        This is called when permissions are granted or revoked for a subject.
        Uses pattern matching to delete
        all cache entries involving this subject.

        Args:
            subject: Subject identifier to invalidate

        Returns:
            Number of keys deleted
        """
        pattern = self._build_subject_pattern(subject)
        deleted = await self.cache.delete_pattern(pattern)

        logger.debug(
            f"Invalidated {deleted} cache keys for subject: {subject}",
            extra={"subject": subject, "keys_deleted": deleted},
        )

        return deleted

    async def invalidate_subjects(self, subjects: list[str]) -> int:
        """Invalidate all cached checks for multiple subjects.

        Used for batch grant/revoke operations.

        Args:
            subjects: List of subject identifiers to invalidate

        Returns:
            Total number of keys deleted
        """
        total_deleted = 0
        for subject in subjects:
            deleted = await self.invalidate_subject(subject)
            total_deleted += deleted

        logger.debug(
            f"Invalidated {total_deleted} cache "
            f"keys for {len(subjects)} subjects",
            extra={
                "subject_count": len(subjects),
                "keys_deleted": total_deleted,
            },
        )

        return total_deleted

    async def invalidate_all_checks(self) -> int:
        """Invalidate all permission check caches.

        Use sparingly - this clears all cached permission checks.

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.prefix}:check:*"
        deleted = await self.cache.delete_pattern(pattern)

        logger.info(
            f"Invalidated all permission check caches: {deleted} keys deleted",
            extra={"keys_deleted": deleted},
        )

        return deleted

    async def clear(self) -> bool:
        """Clear all permission-related caches.

        Returns:
            True if successful
        """
        return await self.cache.clear()

    async def close(self) -> None:
        """Close the cache connection.

        Delegates to the underlying cache service.
        """
        await self.cache.close()
