"""Permission-related data models.

This module contains all models related to permission operations including
grants, revocations, checks, and permission details.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class GrantRequest(BaseModel):
    """Request to grant a permission to a subject.

    Attributes:
        subject: Subject identifier (format: 'type:id')
        scope: Scope identifier (e.g., 'documents.management')
        action: Permission action (e.g., 'read', 'write', 'delete')
        tenant_id: Optional tenant identifier for multi-tenancy
        object_id: Optional object identifier for object-level permissions
        expires_at: Optional expiration datetime
        metadata: Optional metadata dictionary

    Example:
        >>> grant = GrantRequest(
        ...     subject="user:123",
        ...     scope="documents.management",
        ...     action="edit",
        ...     tenant_id="org:456",
        ...     expires_at=datetime(2025, 12, 31)
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    action: str = Field(..., min_length=1, max_length=100, description="Permission action")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(
        default=None, max_length=255, description="Object identifier for object-level permissions"
    )
    expires_at: datetime | None = Field(default=None, description="Expiration datetime")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")

    @field_validator("scope", "action")
    @classmethod
    def lowercase_fields(cls, v: str) -> str:
        """Normalize scope and action to lowercase.

        Args:
            v: Field value

        Returns:
            Lowercase field value
        """
        return v.lower() if v else v


class RevokeRequest(BaseModel):
    """Request to revoke a permission from a subject.

    Attributes:
        subject: Subject identifier
        scope: Scope identifier
        action: Permission action
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> revoke = RevokeRequest(
        ...     subject="user:123",
        ...     scope="documents.management",
        ...     action="edit",
        ...     tenant_id="org:456"
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    action: str = Field(..., min_length=1, max_length=100, description="Permission action")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")

    @field_validator("scope", "action")
    @classmethod
    def lowercase_fields(cls, v: str) -> str:
        """Normalize scope and action to lowercase.

        Args:
            v: Field value

        Returns:
            Lowercase field value
        """
        return v.lower() if v else v


class CheckRequest(BaseModel):
    """Request to check if subject(s) have a permission.

    Attributes:
        subjects: List of subject identifiers to check (in priority order)
        scope: Scope identifier
        action: Permission action
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier
        check_id: Optional correlation ID for batch checks

    Example:
        >>> check = CheckRequest(
        ...     subjects=["user:123", "role:editor"],
        ...     scope="documents.management",
        ...     action="edit",
        ...     tenant_id="org:456"
        ... )
    """

    subjects: list[str] = Field(
        ..., min_length=1, max_length=100, description="List of subject identifiers"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    action: str = Field(..., min_length=1, max_length=100, description="Permission action")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")
    check_id: str | None = Field(default=None, description="Correlation ID for batch checks")

    @field_validator("scope", "action")
    @classmethod
    def lowercase_fields(cls, v: str) -> str:
        """Normalize scope and action to lowercase.

        Args:
            v: Field value

        Returns:
            Lowercase field value
        """
        return v.lower() if v else v


class CheckResult(BaseModel):
    """Result of a permission check.

    Attributes:
        allowed: Whether the permission is allowed
        matched_subject: Subject that matched (if any)
        matched_assignment_id: Assignment ID that granted access (if any)
        check_id: Correlation ID from the request (for batch checks)

    Example:
        >>> result = CheckResult(
        ...     allowed=True,
        ...     matched_subject="user:123",
        ...     matched_assignment_id=456,
        ...     check_id="check-1"
        ... )
        >>> if result.allowed:
        ...     print(f"Access granted for {result.matched_subject}")
    """

    allowed: bool = Field(..., description="Whether permission is allowed")
    matched_subject: str | None = Field(default=None, description="Subject that matched")
    matched_assignment_id: int | None = Field(default=None, description="Assignment ID that granted access")
    check_id: str | None = Field(default=None, description="Correlation ID")


class PermissionAssignment(BaseModel):
    """A granted permission assignment.

    Attributes:
        assignment_id: Unique identifier for this assignment
        subject: Subject identifier
        scope: Scope identifier
        action: Permission action
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier
        granted_at: Timestamp when permission was granted
        expires_at: Optional expiration timestamp
        metadata: Optional additional metadata

    Example:
        >>> assignment = PermissionAssignment(
        ...     assignment_id=123,
        ...     subject="user:123",
        ...     scope="documents.management",
        ...     action="edit",
        ...     granted_at=datetime.now()
        ... )
    """

    assignment_id: int = Field(..., description="Assignment ID")
    subject: str = Field(..., description="Subject identifier")
    scope: str = Field(..., description="Scope identifier")
    action: str = Field(..., description="Permission action")
    tenant_id: str | None = Field(default=None, description="Tenant identifier")
    object_id: str | None = Field(default=None, description="Object identifier")
    granted_at: datetime = Field(..., description="When permission was granted")
    expires_at: datetime | None = Field(default=None, description="When permission expires")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")

    @property
    def is_expired(self) -> bool:
        """Check if permission has expired.

        Returns:
            True if permission is expired, False otherwise

        Example:
            >>> if assignment.is_expired:
            ...     print("Permission has expired")
        """
        return self.expires_at is not None and datetime.now() > self.expires_at


class PermissionDetail(BaseModel):
    """Detailed permission information.

    This model contains enriched information about a permission including
    subject and scope display names.

    Attributes:
        assignment_id: Unique identifier for this assignment
        subject: Subject identifier
        subject_type: Type of subject (user, role, group, etc.)
        subject_display_name: Human-readable subject name
        scope: Scope identifier
        scope_display_name: Human-readable scope name
        action: Permission action
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier
        granted_at: When permission was granted
        expires_at: Optional expiration timestamp
        is_valid: Whether permission is currently valid (not expired)
        metadata: Optional additional metadata

    Example:
        >>> detail = PermissionDetail(
        ...     assignment_id=123,
        ...     subject="user:123",
        ...     subject_type="user",
        ...     subject_display_name="John Doe",
        ...     scope="documents.management",
        ...     scope_display_name="Document Management",
        ...     action="edit",
        ...     granted_at=datetime.now(),
        ...     is_valid=True
        ... )
    """

    assignment_id: int = Field(..., description="Assignment ID")
    subject: str = Field(..., description="Subject identifier")
    subject_type: str = Field(..., description="Subject type")
    subject_display_name: str | None = Field(default=None, description="Subject display name")
    scope: str = Field(..., description="Scope identifier")
    scope_display_name: str | None = Field(default=None, description="Scope display name")
    action: str = Field(..., description="Permission action")
    tenant_id: str | None = Field(default=None, description="Tenant identifier")
    object_id: str | None = Field(default=None, description="Object identifier")
    granted_at: datetime = Field(..., description="When permission was granted")
    expires_at: datetime | None = Field(default=None, description="When permission expires")
    is_valid: bool = Field(..., description="Whether permission is valid")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class GrantManyResult(BaseModel):
    """Result of batch grant operation.

    Attributes:
        granted: Number of permissions granted
        assignments: List of permission assignments

    Example:
        >>> result = GrantManyResult(
        ...     granted=5,
        ...     assignments=[...]
        ... )
        >>> print(f"Successfully granted {result.granted} permissions")
    """

    granted: int = Field(..., ge=0, description="Number of permissions granted")
    assignments: list[PermissionAssignment] = Field(..., description="Permission assignments")


class RevokeManyResult(BaseModel):
    """Result of batch revoke operation.

    Attributes:
        revoked: Number of permissions revoked

    Example:
        >>> result = RevokeManyResult(revoked=3)
        >>> print(f"Revoked {result.revoked} permissions")
    """

    revoked: int = Field(..., ge=0, description="Number of permissions revoked")


class PermissionFilter(BaseModel):
    """Filter criteria for listing permissions.

    All filter fields are optional and will be combined with AND logic.

    Attributes:
        subject: Filter by subject identifier
        scope: Filter by scope identifier
        action: Filter by action
        tenant_id: Filter by tenant
        object_id: Filter by object
        include_expired: Include expired permissions
        limit: Number of results per page (1-1000)
        offset: Pagination offset

    Example:
        >>> filters = PermissionFilter(
        ...     subject="user:123",
        ...     scope="documents.management",
        ...     include_expired=False,
        ...     limit=50
        ... )
        >>> permissions = client.list_permissions(filters)
    """

    subject: str | None = Field(default=None, description="Filter by subject")
    scope: str | None = Field(default=None, description="Filter by scope")
    action: str | None = Field(default=None, description="Filter by action")
    tenant_id: str | None = Field(default=None, description="Filter by tenant")
    object_id: str | None = Field(default=None, description="Filter by object")
    include_expired: bool = Field(default=False, description="Include expired permissions")
    limit: int = Field(default=100, ge=1, le=1000, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
