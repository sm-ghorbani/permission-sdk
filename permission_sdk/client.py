"""Synchronous client for the Permission Service API.

This module provides the main client interface for interacting with the
Permission Service in synchronous applications.
"""

from typing import Any
from urllib.parse import quote

from permission_sdk.config import SDKConfig
from permission_sdk.models import (
    CheckLimitResult,
    CheckManyLimitsResult,
    CheckRequest,
    CheckResult,
    GrantManyResult,
    GrantRequest,
    IncrementManyResult,
    IncrementUsageRequest,
    IncrementUsageResult,
    LimitDetail,
    LimitFilter,
    PaginatedResponse,
    PermissionAssignment,
    PermissionDetail,
    PermissionFilter,
    ResetUsageResult,
    RevokeRequest,
    Scope,
    ScopeFilter,
    SingleCheckLimitRequest,
    Subject,
    SubjectFilter,
    UsageDetail,
)
from permission_sdk.models.scopes import ScopeCreate
from permission_sdk.models.subjects import SubjectCreate
from permission_sdk.transport import HTTPTransport
from permission_sdk.utils import validate_grant_request


class PermissionClient:
    """Synchronous client for Permission Service API.

    This client provides a high-level interface for all permission operations
    including grants, revocations, checks, and management of subjects and scopes.

    Features:
    - Type-safe methods for all API endpoints
    - Automatic retry with exponential backoff
    - Connection pooling
    - Context manager support for proper cleanup

    Attributes:
        config: SDK configuration
        transport: HTTP transport layer

    Example:
        >>> config = SDKConfig(
        ...     base_url="https://permissions.example.com",
        ...     api_key="your-api-key"
        ... )
        >>> client = PermissionClient(config)
        >>> try:
        ...     allowed = client.check_permission(
        ...         subjects=["user:123"],
        ...         scope="documents.management",
        ...         action="edit"
        ...     )
        ...     if allowed:
        ...         print("Access granted")
        ... finally:
        ...     client.close()

    Example (with context manager):
        >>> with PermissionClient(config) as client:
        ...     allowed = client.check_permission(["user:123"], "docs", "read")
    """

    def __init__(self, config: SDKConfig) -> None:
        """Initialize the Permission client.

        Args:
            config: SDK configuration

        Example:
            >>> config = SDKConfig(base_url="https://api.example.com", api_key="key")
            >>> client = PermissionClient(config)
        """
        self.config = config
        self.transport = HTTPTransport(config)

    # ==================== Permission Operations ====================

    def grant_permission(
        self,
        subject: str,
        scope: str,
        action: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
        expires_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PermissionAssignment:
        """Grant a permission to a subject.

        This operation is idempotent - if the permission already exists,
        it will be updated with the new metadata/expiration.

        Args:
            subject: Subject identifier (format: 'type:id')
            scope: Scope identifier (e.g., 'documents.management')
            action: Permission action (e.g., 'read', 'write', 'delete')
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier for object-level permissions
            expires_at: Optional expiration datetime (ISO 8601 format)
            metadata: Optional metadata dictionary

        Returns:
            PermissionAssignment with details of the granted permission

        Raises:
            ValidationError: If input parameters are invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> assignment = client.grant_permission(
            ...     subject="user:123",
            ...     scope="documents.management",
            ...     action="edit",
            ...     tenant_id="org:456",
            ...     metadata={"granted_by": "admin:1", "reason": "Project access"}
            ... )
            >>> print(f"Permission granted: {assignment.assignment_id}")
        """
        # Validate input if enabled
        validate_grant_request(subject, scope, action, self.config.validate_identifiers)

        request_data = {
            "subject": subject,
            "scope": scope,
            "action": action,
            "tenant_id": tenant_id,
            "object_id": object_id,
            "expires_at": expires_at,
            "metadata": metadata,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/permissions/grant",
            json=request_data,
        )

        return PermissionAssignment(**response)

    def grant_many(self, grants: list[GrantRequest]) -> GrantManyResult:
        """Grant multiple permissions in batch.

        Optimized for performance by batching operations. More efficient
        than calling grant_permission() multiple times.

        Args:
            grants: List of grant requests

        Returns:
            GrantManyResult with count and details of granted permissions

        Raises:
            ValidationError: If any grant request is invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> grants = [
            ...     GrantRequest(
            ...         subject="user:123",
            ...         scope="documents.management",
            ...         action="read"
            ...     ),
            ...     GrantRequest(
            ...         subject="user:123",
            ...         scope="documents.management",
            ...         action="write"
            ...     ),
            ... ]
            >>> result = client.grant_many(grants)
            >>> print(f"Granted {result.granted} permissions")
        """
        # Validate all grants if enabled
        if self.config.validate_identifiers:
            for grant in grants:
                validate_grant_request(grant.subject, grant.scope, grant.action)

        request_data = {"grants": [grant.model_dump(exclude_none=True) for grant in grants]}

        response = self.transport.request(
            "POST",
            "/api/v1/permissions/grant-many",
            json=request_data,
        )

        return GrantManyResult(
            granted=response["granted"],
            assignments=[PermissionAssignment(**a) for a in response["assignments"]],
        )

    def revoke_permission(
        self,
        subject: str,
        scope: str,
        action: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> bool:
        """Revoke a permission from a subject.

        Args:
            subject: Subject identifier
            scope: Scope identifier
            action: Permission action
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            True if permission was revoked, False if it didn't exist

        Raises:
            ValidationError: If input parameters are invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> revoked = client.revoke_permission(
            ...     subject="user:123",
            ...     scope="documents.management",
            ...     action="edit",
            ...     tenant_id="org:456"
            ... )
            >>> if revoked:
            ...     print("Permission revoked successfully")
        """
        # Validate input if enabled
        validate_grant_request(subject, scope, action, self.config.validate_identifiers)

        request_data = {
            "subject": subject,
            "scope": scope,
            "action": action,
            "tenant_id": tenant_id,
            "object_id": object_id,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/permissions/revoke",
            json=request_data,
        )

        return response.get("revoked", False)

    def revoke_many(self, revocations: list[RevokeRequest]) -> int:
        """Revoke multiple permissions in batch.

        Args:
            revocations: List of revocation requests

        Returns:
            Number of permissions revoked

        Raises:
            ValidationError: If any revocation request is invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> revocations = [
            ...     RevokeRequest(
            ...         subject="user:123",
            ...         scope="documents.management",
            ...         action="read"
            ...     ),
            ...     RevokeRequest(
            ...         subject="user:123",
            ...         scope="documents.management",
            ...         action="write"
            ...     ),
            ... ]
            >>> count = client.revoke_many(revocations)
            >>> print(f"Revoked {count} permissions")
        """
        # Validate all revocations if enabled
        if self.config.validate_identifiers:
            for revoke in revocations:
                validate_grant_request(revoke.subject, revoke.scope, revoke.action)

        request_data = {"revocations": [r.model_dump(exclude_none=True) for r in revocations]}

        response = self.transport.request(
            "POST",
            "/api/v1/permissions/revoke-many",
            json=request_data,
        )

        return response.get("revoked_count", 0)

    def check_permission(
        self,
        subjects: list[str],
        scope: str,
        action: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> bool:
        """Check if any subject has a permission.

        Checks permissions in the order provided - returns True as soon as
        a match is found.

        Args:
            subjects: List of subject identifiers to check (in priority order)
            scope: Scope identifier
            action: Permission action
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            True if any subject has the permission, False otherwise

        Raises:
            ValidationError: If input parameters are invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> allowed = client.check_permission(
            ...     subjects=["user:123", "role:editor"],
            ...     scope="documents.management",
            ...     action="edit",
            ...     tenant_id="org:456"
            ... )
            >>> if allowed:
            ...     print("Access granted")
            ... else:
            ...     print("Access denied")
        """
        request_data = {
            "subjects": subjects,
            "scope": scope,
            "action": action,
            "tenant_id": tenant_id,
            "object_id": object_id,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/permissions/check",
            json=request_data,
        )

        return response.get("allowed", False)

    def check_many(self, checks: list[CheckRequest]) -> list[CheckResult]:
        """Check multiple permissions in batch.

        Highly optimized for performance - uses a single query to check
        all permissions. Ideal for UI rendering where multiple permission
        checks are needed.

        Args:
            checks: List of permission check requests

        Returns:
            List of check results in the same order as requests

        Raises:
            ValidationError: If any check request is invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> checks = [
            ...     CheckRequest(
            ...         subjects=["user:123"],
            ...         scope="documents.management",
            ...         action="read",
            ...         check_id="check-1"
            ...     ),
            ...     CheckRequest(
            ...         subjects=["user:123"],
            ...         scope="documents.management",
            ...         action="write",
            ...         check_id="check-2"
            ...     ),
            ... ]
            >>> results = client.check_many(checks)
            >>> for result in results:
            ...     print(f"{result.check_id}: {result.allowed}")
        """
        request_data = {"checks": [c.model_dump(exclude_none=True) for c in checks]}

        response = self.transport.request(
            "POST",
            "/api/v1/permissions/check-many",
            json=request_data,
        )

        return [CheckResult(**r) for r in response.get("results", [])]

    def list_permissions(
        self, filters: PermissionFilter | None = None
    ) -> PaginatedResponse[PermissionDetail]:
        """List permissions with optional filtering and pagination.

        Args:
            filters: Optional filter criteria

        Returns:
            Paginated response with permission details

        Raises:
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> filters = PermissionFilter(
            ...     subject="user:123",
            ...     scope="documents.management",
            ...     limit=50
            ... )
            >>> response = client.list_permissions(filters)
            >>> print(f"Total permissions: {response.total}")
            >>> for perm in response.items:
            ...     print(f"{perm.subject} -> {perm.scope}.{perm.action}")
        """
        params = {}
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            params = {k: str(v) for k, v in filter_dict.items()}

        response = self.transport.request(
            "GET",
            "/api/v1/permissions",
            params=params,
        )

        return PaginatedResponse[PermissionDetail](
            total=response["total"],
            limit=response["limit"],
            offset=response["offset"],
            items=[PermissionDetail(**p) for p in response["permissions"]],
        )

    # ==================== Subject Operations ====================

    def create_subject(
        self,
        identifier: str,
        display_name: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Subject:
        """Create or update a subject.

        This operation is idempotent - if the subject already exists,
        it will be updated with the new information.

        Args:
            identifier: Subject identifier (format: 'type:id')
            display_name: Optional human-readable name
            tenant_id: Optional tenant identifier
            metadata: Optional metadata dictionary

        Returns:
            Subject details

        Raises:
            ValidationError: If identifier format is invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> subject = client.create_subject(
            ...     identifier="user:john.doe",
            ...     display_name="John Doe",
            ...     tenant_id="org:acme",
            ...     metadata={"email": "john@acme.com"}
            ... )
            >>> print(f"Subject created: {subject.id}")
        """
        request = SubjectCreate(
            identifier=identifier,
            display_name=display_name,
            tenant_id=tenant_id,
            metadata=metadata,
        )

        response = self.transport.request(
            "POST",
            "/api/v1/subjects",
            json=request.model_dump(exclude_none=True),
        )

        return Subject(**response)

    def get_subject(self, identifier: str, tenant_id: str | None = None) -> Subject:
        """Get a subject by identifier.

        Args:
            identifier: Subject identifier
            tenant_id: Optional tenant filter

        Returns:
            Subject details

        Raises:
            ResourceNotFoundError: If subject not found
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> subject = client.get_subject("user:john.doe")
            >>> print(f"Display name: {subject.display_name}")
        """
        # URL encode the identifier
        encoded_identifier = quote(identifier, safe="")

        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id

        response = self.transport.request(
            "GET",
            f"/api/v1/subjects/{encoded_identifier}",
            params=params,
        )

        return Subject(**response)

    def list_subjects(self, filters: SubjectFilter | None = None) -> PaginatedResponse[Subject]:
        """List subjects with optional filtering and pagination.

        Args:
            filters: Optional filter criteria

        Returns:
            Paginated response with subjects

        Raises:
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> filters = SubjectFilter(
            ...     subject_type="user",
            ...     search="john",
            ...     limit=50
            ... )
            >>> response = client.list_subjects(filters)
            >>> for subject in response.items:
            ...     print(f"{subject.identifier}: {subject.display_name}")
        """
        params = {}
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            params = {k: str(v) for k, v in filter_dict.items()}

        response = self.transport.request(
            "GET",
            "/api/v1/subjects",
            params=params,
        )

        return PaginatedResponse[Subject](
            total=response["total"],
            limit=response["limit"],
            offset=response["offset"],
            items=[Subject(**s) for s in response["subjects"]],
        )

    def deactivate_subject(self, identifier: str) -> bool:
        """Deactivate a subject (soft delete).

        Args:
            identifier: Subject identifier

        Returns:
            True if subject was deactivated

        Raises:
            ResourceNotFoundError: If subject not found
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> deactivated = client.deactivate_subject("user:john.doe")
            >>> if deactivated:
            ...     print("Subject deactivated")
        """
        # URL encode the identifier
        encoded_identifier = quote(identifier, safe="")

        self.transport.request(
            "DELETE",
            f"/api/v1/subjects/{encoded_identifier}",
        )

        return True

    # ==================== Scope Operations ====================

    def create_scope(
        self,
        identifier: str,
        display_name: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Scope:
        """Create or update a scope.

        This operation is idempotent - if the scope already exists,
        it will be updated with the new information.

        Args:
            identifier: Scope identifier (e.g., 'documents.management')
            display_name: Optional human-readable name
            description: Optional description
            metadata: Optional metadata dictionary

        Returns:
            Scope details

        Raises:
            ValidationError: If identifier format is invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> scope = client.create_scope(
            ...     identifier="documents.management",
            ...     display_name="Document Management",
            ...     description="Permissions for managing documents",
            ...     metadata={"category": "content"}
            ... )
            >>> print(f"Scope created: {scope.id}")
        """
        request = ScopeCreate(
            identifier=identifier,
            display_name=display_name,
            description=description,
            metadata=metadata,
        )

        response = self.transport.request(
            "POST",
            "/api/v1/scopes",
            json=request.model_dump(exclude_none=True),
        )

        return Scope(**response)

    def get_scope(self, identifier: str) -> Scope:
        """Get a scope by identifier.

        Args:
            identifier: Scope identifier

        Returns:
            Scope details

        Raises:
            ResourceNotFoundError: If scope not found
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> scope = client.get_scope("documents.management")
            >>> print(f"Display name: {scope.display_name}")
        """
        # URL encode the identifier
        encoded_identifier = quote(identifier, safe="")

        response = self.transport.request(
            "GET",
            f"/api/v1/scopes/{encoded_identifier}",
        )

        return Scope(**response)

    def list_scopes(self, filters: ScopeFilter | None = None) -> PaginatedResponse[Scope]:
        """List scopes with optional filtering and pagination.

        Args:
            filters: Optional filter criteria

        Returns:
            Paginated response with scopes

        Raises:
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> filters = ScopeFilter(
            ...     search="document",
            ...     limit=50
            ... )
            >>> response = client.list_scopes(filters)
            >>> for scope in response.items:
            ...     print(f"{scope.identifier}: {scope.display_name}")
        """
        params = {}
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            params = {k: str(v) for k, v in filter_dict.items()}

        response = self.transport.request(
            "GET",
            "/api/v1/scopes",
            params=params,
        )

        return PaginatedResponse[Scope](
            total=response["total"],
            limit=response["limit"],
            offset=response["offset"],
            items=[Scope(**s) for s in response["scopes"]],
        )

    def deactivate_scope(self, identifier: str) -> bool:
        """Deactivate a scope (soft delete).

        Args:
            identifier: Scope identifier

        Returns:
            True if scope was deactivated

        Raises:
            ResourceNotFoundError: If scope not found
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> deactivated = client.deactivate_scope("documents.management")
            >>> if deactivated:
            ...     print("Scope deactivated")
        """
        # URL encode the identifier
        encoded_identifier = quote(identifier, safe="")

        self.transport.request(
            "DELETE",
            f"/api/v1/scopes/{encoded_identifier}",
        )

        return True

    # ==================== Resource Limit Operations ====================

    def set_limit(
        self,
        subject: str,
        resource_type: str,
        scope: str,
        limit_value: int,
        window_type: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LimitDetail:
        """Set or update a resource limit.

        This operation is idempotent - if the limit already exists, it will be updated.

        **Window Type Changes**: If you update a limit with a different window_type,
        the service will automatically reset usage to 0 and return metadata about the change:
        - window_changed: True if window type was changed
        - previous_window_type: The old window type
        - previous_usage: The usage count before reset

        Args:
            subject: Subject identifier (format: 'type:id')
            resource_type: Type of resource (e.g., 'project', 'api_call')
            scope: Scope identifier
            limit_value: Maximum allowed consumption
            window_type: Time window ('hourly', 'daily', 'monthly', 'total')
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier
            metadata: Optional metadata dictionary

        Returns:
            LimitDetail with configured limit information

        Raises:
            ValidationError: If input parameters are invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> limit = client.set_limit(
            ...     subject="user:123",
            ...     resource_type="project",
            ...     scope="projects",
            ...     limit_value=10,
            ...     window_type="monthly",
            ...     tenant_id="org:456"
            ... )
            >>> print(f"Limit set: {limit.limit_id}")
            >>>
            >>> # Changing window type resets usage automatically
            >>> updated = client.set_limit(
            ...     subject="user:123",
            ...     resource_type="project",
            ...     scope="projects",
            ...     limit_value=50,
            ...     window_type="daily",  # Changed from monthly to daily
            ...     tenant_id="org:456"
            ... )
            >>> if updated.window_changed:
            ...     print(f"Window changed from {updated.previous_window_type}")
            ...     print(f"Previous usage: {updated.previous_usage}")
        """
        request_data = {
            "subject": subject,
            "resource_type": resource_type,
            "scope": scope,
            "limit_value": limit_value,
            "window_type": window_type,
            "tenant_id": tenant_id,
            "object_id": object_id,
            "metadata": metadata,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/limits/set",
            json=request_data,
        )

        return LimitDetail(**response)

    def check_limit(
        self,
        subject: str,
        resource_type: str,
        scope: str,
        amount: int = 1,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> CheckLimitResult:
        """Check if consuming amount would exceed limit.

        This is a read-only operation - does NOT increment the counter.

        Args:
            subject: Subject identifier
            resource_type: Type of resource
            scope: Scope identifier
            amount: Amount to check (default: 1)
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            CheckLimitResult with usage information

        Raises:
            ValidationError: If input parameters are invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> result = client.check_limit(
            ...     subject="user:123",
            ...     resource_type="project",
            ...     scope="projects",
            ...     amount=1,
            ...     tenant_id="org:456"
            ... )
            >>> if result.allowed:
            ...     print(f"Can create project. {result.remaining} remaining.")
            ... else:
            ...     print(f"Limit exceeded. Usage: {result.current_usage}/{result.limit}")
        """
        request_data = {
            "subject": subject,
            "resource_type": resource_type,
            "scope": scope,
            "amount": amount,
            "tenant_id": tenant_id,
            "object_id": object_id,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/limits/check",
            json=request_data,
        )

        return CheckLimitResult(**response)

    def check_many_limits(
        self,
        checks: list[SingleCheckLimitRequest],
    ) -> CheckManyLimitsResult:
        """Check multiple limits in a single batch request.

        Useful for hierarchy checking (e.g., org limit + system limit) or reducing HTTP round trips.
        All checks are read-only - do NOT increment counters.

        Args:
            checks: List of limit checks to perform

        Returns:
            CheckManyLimitsResult with results in same order

        Raises:
            ValidationError: If any check request is invalid
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> checks = [
            ...     SingleCheckLimitRequest(
            ...         check_id="org",
            ...         subject="user:123",
            ...         resource_type="project",
            ...         scope="projects",
            ...         amount=1,
            ...         tenant_id="org:A"
            ...     ),
            ...     SingleCheckLimitRequest(
            ...         check_id="system",
            ...         subject="user:123",
            ...         resource_type="project",
            ...         scope="projects",
            ...         amount=1
            ...     ),
            ... ]
            >>> results = client.check_many_limits(checks)
            >>> # Hierarchy enforcement: caller applies logic
            >>> allowed = all(r.allowed for r in results.results)
        """
        request_data = {"checks": [c.model_dump(exclude_none=True) for c in checks]}

        response = self.transport.request(
            "POST",
            "/api/v1/limits/check-many",
            json=request_data,
        )

        return CheckManyLimitsResult(**response)

    def increment_usage(
        self,
        subject: str,
        resource_type: str,
        scope: str,
        amount: int = 1,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> IncrementUsageResult:
        """Increment resource usage counter.

        Args:
            subject: Subject identifier
            resource_type: Type of resource
            scope: Scope identifier
            amount: Amount to increment (default: 1)
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            IncrementUsageResult with updated usage information

        Raises:
            ValidationError: If input parameters are invalid
            ResourceNotFoundError: If no limit configured
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> # After creating a project
            >>> result = client.increment_usage(
            ...     subject="user:123",
            ...     resource_type="project",
            ...     scope="projects",
            ...     amount=1,
            ...     tenant_id="org:456"
            ... )
            >>> print(f"New usage: {result.current_usage}/{result.limit}")
        """
        request_data = {
            "subject": subject,
            "resource_type": resource_type,
            "scope": scope,
            "amount": amount,
            "tenant_id": tenant_id,
            "object_id": object_id,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/limits/increment",
            json=request_data,
        )

        return IncrementUsageResult(**response)

    def increment_many(
        self,
        increments: list[IncrementUsageRequest],
    ) -> IncrementManyResult:
        """Increment multiple usage counters in a single batch request.

        Optimized for hierarchy updates where you need to increment usage at
        multiple levels (user → org → parent → root). Reduces HTTP round trips.

        Args:
            increments: List of usage increments to perform

        Returns:
            IncrementManyResult with results in same order

        Raises:
            ValidationError: If any increment request is invalid
            ResourceNotFoundError: If any limit not configured
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> increments = [
            ...     IncrementUsageRequest(
            ...         subject="user:123",
            ...         resource_type="scan",
            ...         scope="org:A",
            ...         amount=1,
            ...         tenant_id="org:A"
            ...     ),
            ...     IncrementUsageRequest(
            ...         subject="org:A",
            ...         resource_type="scan",
            ...         scope="system",
            ...         amount=1
            ...     ),
            ... ]
            >>> results = client.increment_many(increments)
            >>> for result in results.results:
            ...     print(f"New usage: {result.current_usage}/{result.limit}")
        """
        request_data = {"increments": [inc.model_dump(exclude_none=True) for inc in increments]}

        response = self.transport.request(
            "POST",
            "/api/v1/limits/increment-many",
            json=request_data,
        )

        return IncrementManyResult(**response)

    def get_usage(
        self,
        subject: str,
        resource_type: str,
        scope: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> UsageDetail:
        """Get current usage information for a resource.

        Args:
            subject: Subject identifier
            resource_type: Type of resource
            scope: Scope identifier
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            UsageDetail with current usage information

        Raises:
            ResourceNotFoundError: If no limit configured
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> usage = client.get_usage(
            ...     subject="user:123",
            ...     resource_type="project",
            ...     scope="projects",
            ...     tenant_id="org:456"
            ... )
            >>> print(f"Usage: {usage.current_usage}/{usage.limit}")
            >>> print(f"Resets at: {usage.window_end}")
        """
        params = {
            "subject": subject,
            "resource_type": resource_type,
            "scope": scope,
        }
        if tenant_id:
            params["tenant_id"] = tenant_id
        if object_id:
            params["object_id"] = object_id

        response = self.transport.request(
            "GET",
            "/api/v1/limits/usage",
            params=params,
        )

        return UsageDetail(**response)

    def reset_usage(
        self,
        subject: str,
        resource_type: str,
        scope: str,
        tenant_id: str | None = None,
        object_id: str | None = None,
    ) -> ResetUsageResult:
        """Manually reset usage counter to 0.

        Useful for admin overrides, testing, or subscription upgrades.

        Args:
            subject: Subject identifier
            resource_type: Type of resource
            scope: Scope identifier
            tenant_id: Optional tenant identifier
            object_id: Optional object identifier

        Returns:
            ResetUsageResult with previous and current usage

        Raises:
            ResourceNotFoundError: If no usage record found
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> # Admin override or subscription upgrade
            >>> result = client.reset_usage(
            ...     subject="user:123",
            ...     resource_type="project",
            ...     scope="projects",
            ...     tenant_id="org:456"
            ... )
            >>> print(f"Reset from {result.previous_usage} to {result.current_usage}")
        """
        request_data = {
            "subject": subject,
            "resource_type": resource_type,
            "scope": scope,
            "tenant_id": tenant_id,
            "object_id": object_id,
        }

        response = self.transport.request(
            "POST",
            "/api/v1/limits/reset",
            json=request_data,
        )

        return ResetUsageResult(**response)

    def list_limits(
        self,
        filters: LimitFilter | None = None,
    ) -> PaginatedResponse[LimitDetail]:
        """List resource limits with optional filtering and pagination.

        Args:
            filters: Optional filter criteria

        Returns:
            Paginated response with limit details

        Raises:
            AuthenticationError: If API key is invalid
            ServerError: If server error occurs

        Example:
            >>> filters = LimitFilter(
            ...     subject="user:123",
            ...     tenant_id="org:456",
            ...     limit=50
            ... )
            >>> response = client.list_limits(filters)
            >>> print(f"Total limits: {response.total}")
            >>> for limit in response.items:
            ...     print(f"{limit.resource_type}: {limit.limit_value} ({limit.window_type})")
        """
        params = {}
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
            params = {k: str(v) for k, v in filter_dict.items()}

        response = self.transport.request(
            "GET",
            "/api/v1/limits",
            params=params,
        )

        return PaginatedResponse[LimitDetail](
            total=response["total"],
            limit=response["limit"],
            offset=response["offset"],
            items=[LimitDetail(**lim) for lim in response["limits"]],
        )

    # ==================== Client Lifecycle ====================

    def close(self) -> None:
        """Close the client and cleanup connections.

        This is optional - connections are automatically cleaned up when the
        client is garbage collected. However, explicit cleanup is recommended
        for production use to ensure immediate resource release.

        Example:
            >>> client = PermissionClient(config)
            >>> try:
            ...     # Use client
            ...     pass
            ... finally:
            ...     client.close()
        """
        self.transport.close()

    def __enter__(self) -> "PermissionClient":
        """Context manager entry.

        Returns:
            Self for use in with statement

        Example:
            >>> with PermissionClient(config) as client:
            ...     allowed = client.check_permission(["user:123"], "docs", "read")
        """
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit - cleanup connections.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        self.close()
