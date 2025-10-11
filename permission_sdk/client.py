"""Synchronous client for the Permission Service API.

This module provides the main client interface for interacting with the
Permission Service in synchronous applications.
"""

from typing import Any
from urllib.parse import quote

from permission_sdk.config import SDKConfig
from permission_sdk.models import (
    CheckRequest,
    CheckResult,
    GrantManyResult,
    GrantRequest,
    PaginatedResponse,
    PermissionAssignment,
    PermissionDetail,
    PermissionFilter,
    RevokeRequest,
    Scope,
    ScopeFilter,
    Subject,
    SubjectFilter,
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

    # ==================== Client Lifecycle ====================

    def close(self) -> None:
        """Close the client and cleanup connections.

        This should be called when the client is no longer needed to
        properly cleanup connection pools.

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
