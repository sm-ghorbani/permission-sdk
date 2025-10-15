"""Unit tests for SDK data models.

This module tests the Pydantic models used for request/response serialization.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from permission_sdk.models import (
    CheckRequest,
    CheckResult,
    GrantRequest,
    PermissionAssignment,
    PermissionFilter,
    RevokeRequest,
)


class TestGrantRequest:
    """Tests for GrantRequest model."""

    def test_valid_grant_request(self) -> None:
        """Test creating a valid grant request."""
        grant = GrantRequest(
            subject="user:alice",
            scope="documents.management",
            action="read",
            tenant_id="org:acme",
        )

        assert grant.subject == "user:alice"
        assert grant.scope == "documents.management"
        assert grant.action == "read"
        assert grant.tenant_id == "org:acme"
        assert grant.object_id is None
        assert grant.expires_at is None
        assert grant.metadata is None

    def test_grant_request_lowercase_normalization(self) -> None:
        """Test that scope and action are normalized to lowercase."""
        grant = GrantRequest(
            subject="user:alice",
            scope="Documents.Management",  # Mixed case
            action="READ",  # Uppercase
        )

        assert grant.scope == "documents.management"
        assert grant.action == "read"

    def test_grant_request_with_all_fields(self) -> None:
        """Test grant request with all optional fields."""
        expires_at = datetime(2025, 12, 31)
        metadata = {"granted_by": "admin:1", "reason": "Project access"}

        grant = GrantRequest(
            subject="user:alice",
            scope="documents.management",
            action="edit",
            tenant_id="org:acme",
            object_id="doc:123",
            expires_at=expires_at,
            metadata=metadata,
        )

        assert grant.object_id == "doc:123"
        assert grant.expires_at == expires_at
        assert grant.metadata == metadata

    def test_grant_request_with_colon_in_scope(self) -> None:
        """Test that scope identifiers can contain colons."""
        grant = GrantRequest(
            subject="user:alice",
            scope="api:v1.documents",
            action="read",
        )

        assert grant.scope == "api:v1.documents"

    def test_grant_request_with_multiple_colons_in_scope(self) -> None:
        """Test that scope identifiers can contain multiple colons."""
        grant = GrantRequest(
            subject="user:alice",
            scope="service:namespace:resource.read",
            action="read",
        )

        assert grant.scope == "service:namespace:resource.read"

    def test_grant_request_validation_errors(self) -> None:
        """Test validation errors for invalid grant requests."""
        # Missing required field
        with pytest.raises(ValidationError) as exc_info:
            GrantRequest(subject="user:alice", scope="docs")  # type: ignore[call-arg]

        assert "action" in str(exc_info.value)

        # Subject too short
        with pytest.raises(ValidationError):
            GrantRequest(subject="ab", scope="docs", action="read")


class TestRevokeRequest:
    """Tests for RevokeRequest model."""

    def test_valid_revoke_request(self) -> None:
        """Test creating a valid revoke request."""
        revoke = RevokeRequest(
            subject="user:alice",
            scope="documents.management",
            action="read",
        )

        assert revoke.subject == "user:alice"
        assert revoke.scope == "documents.management"
        assert revoke.action == "read"

    def test_revoke_request_lowercase_normalization(self) -> None:
        """Test lowercase normalization."""
        revoke = RevokeRequest(
            subject="user:alice",
            scope="DOCS.MGMT",
            action="DELETE",
        )

        assert revoke.scope == "docs.mgmt"
        assert revoke.action == "delete"

    def test_revoke_request_with_colon_in_scope(self) -> None:
        """Test that scope identifiers can contain colons."""
        revoke = RevokeRequest(
            subject="user:alice",
            scope="api:v2.documents",
            action="write",
        )

        assert revoke.scope == "api:v2.documents"


class TestCheckRequest:
    """Tests for CheckRequest model."""

    def test_valid_check_request(self) -> None:
        """Test creating a valid check request."""
        check = CheckRequest(
            subjects=["user:alice", "role:editor"],
            scope="documents.management",
            action="read",
        )

        assert check.subjects == ["user:alice", "role:editor"]
        assert check.scope == "documents.management"
        assert check.action == "read"

    def test_check_request_with_check_id(self) -> None:
        """Test check request with correlation ID."""
        check = CheckRequest(
            subjects=["user:alice"],
            scope="documents.management",
            action="read",
            check_id="check-123",
        )

        assert check.check_id == "check-123"

    def test_check_request_with_colon_in_scope(self) -> None:
        """Test that scope identifiers can contain colons."""
        check = CheckRequest(
            subjects=["user:alice", "role:admin"],
            scope="service:api.permissions",
            action="manage",
        )

        assert check.scope == "service:api.permissions"

    def test_check_request_validation(self) -> None:
        """Test validation for check requests."""
        # Empty subjects list
        with pytest.raises(ValidationError):
            CheckRequest(subjects=[], scope="docs", action="read")

        # Too many subjects
        with pytest.raises(ValidationError):
            CheckRequest(subjects=["user:1"] * 101, scope="docs", action="read")


class TestCheckResult:
    """Tests for CheckResult model."""

    def test_check_result_allowed(self) -> None:
        """Test check result when allowed."""
        result = CheckResult(
            allowed=True,
            matched_subject="user:alice",
            check_id="check-123",
        )

        assert result.allowed is True
        assert result.matched_subject == "user:alice"
        assert result.check_id == "check-123"

    def test_check_result_denied(self) -> None:
        """Test check result when denied."""
        result = CheckResult(allowed=False)

        assert result.allowed is False
        assert result.matched_subject is None
        assert result.check_id is None


class TestPermissionAssignment:
    """Tests for PermissionAssignment model."""

    def test_valid_assignment(self) -> None:
        """Test creating a valid permission assignment."""
        granted_at = datetime.now()

        assignment = PermissionAssignment(
            assignment_id="perm_123",
            subject="user:alice",
            scope="documents.management",
            action="read",
            granted_at=granted_at,
        )

        assert assignment.assignment_id == "perm_123"
        assert assignment.subject == "user:alice"
        assert assignment.scope == "documents.management"
        assert assignment.action == "read"
        assert assignment.granted_at == granted_at

    def test_is_expired_property(self) -> None:
        """Test is_expired property."""
        # Not expired (no expiration)
        assignment = PermissionAssignment(
            assignment_id="perm_123",
            subject="user:alice",
            scope="docs",
            action="read",
            granted_at=datetime.now(),
        )
        assert assignment.is_expired is False

        # Not expired (future expiration)
        assignment = PermissionAssignment(
            assignment_id="perm_123",
            subject="user:alice",
            scope="docs",
            action="read",
            granted_at=datetime.now(),
            expires_at=datetime(2099, 12, 31),
        )
        assert assignment.is_expired is False

        # Expired (past expiration)
        assignment = PermissionAssignment(
            assignment_id="perm_123",
            subject="user:alice",
            scope="docs",
            action="read",
            granted_at=datetime(2020, 1, 1),
            expires_at=datetime(2020, 12, 31),
        )
        assert assignment.is_expired is True


class TestPermissionFilter:
    """Tests for PermissionFilter model."""

    def test_default_filter(self) -> None:
        """Test filter with default values."""
        filters = PermissionFilter()

        assert filters.subject is None
        assert filters.scope is None
        assert filters.action is None
        assert filters.include_expired is False
        assert filters.limit == 100
        assert filters.offset == 0

    def test_custom_filter(self) -> None:
        """Test filter with custom values."""
        filters = PermissionFilter(
            subject="user:alice",
            scope="documents.management",
            limit=50,
            offset=100,
        )

        assert filters.subject == "user:alice"
        assert filters.scope == "documents.management"
        assert filters.limit == 50
        assert filters.offset == 100

    def test_filter_validation(self) -> None:
        """Test filter validation."""
        # Limit too low
        with pytest.raises(ValidationError):
            PermissionFilter(limit=0)

        # Limit too high
        with pytest.raises(ValidationError):
            PermissionFilter(limit=1001)

        # Negative offset
        with pytest.raises(ValidationError):
            PermissionFilter(offset=-1)
