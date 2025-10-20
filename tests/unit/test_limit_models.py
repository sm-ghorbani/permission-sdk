"""Unit tests for resource limit data models.

This module tests the Pydantic models used for resource limit request/response serialization.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from permission_sdk.models import (
    CheckLimitRequest,
    CheckLimitResult,
    CheckManyLimitsRequest,
    CheckManyLimitsResult,
    IncrementManyRequest,
    IncrementManyResult,
    IncrementUsageRequest,
    IncrementUsageResult,
    LimitDetail,
    LimitFilter,
    ResetUsageRequest,
    ResetUsageResult,
    SetLimitRequest,
    SingleCheckLimitRequest,
    SingleCheckLimitResult,
    UsageDetail,
)


class TestSetLimitRequest:
    """Tests for SetLimitRequest model."""

    def test_valid_set_limit_request(self) -> None:
        """Test creating a valid set limit request."""
        request = SetLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            limit_value=10,
            window_type="monthly",
        )

        assert request.subject == "user:alice"
        assert request.resource_type == "project"
        assert request.scope == "organization:acme"
        assert request.limit_value == 10
        assert request.window_type == "monthly"
        assert request.tenant_id is None
        assert request.object_id is None
        assert request.metadata is None

    def test_set_limit_with_all_fields(self) -> None:
        """Test set limit request with all optional fields."""
        metadata = {"plan": "premium", "set_by": "admin:1"}

        request = SetLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            limit_value=50,
            window_type="daily",
            tenant_id="org:acme",
            object_id="workspace:123",
            metadata=metadata,
        )

        assert request.tenant_id == "org:acme"
        assert request.object_id == "workspace:123"
        assert request.metadata == metadata

    def test_set_limit_window_type_validation(self) -> None:
        """Test window type validation."""
        # Valid window types
        for window_type in ["hourly", "daily", "monthly", "total"]:
            request = SetLimitRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                limit_value=10,
                window_type=window_type,
            )
            assert request.window_type == window_type

        # Invalid window type
        with pytest.raises(ValidationError) as exc_info:
            SetLimitRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                limit_value=10,
                window_type="weekly",  # Invalid
            )
        assert "window_type" in str(exc_info.value).lower()

    def test_set_limit_validation_errors(self) -> None:
        """Test validation errors for invalid set limit requests."""
        # Missing required field
        with pytest.raises(ValidationError) as exc_info:
            SetLimitRequest(  # type: ignore[call-arg]
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                # Missing limit_value and window_type
            )
        assert "limit_value" in str(exc_info.value) or "window_type" in str(exc_info.value)

        # Subject too short
        with pytest.raises(ValidationError):
            SetLimitRequest(
                subject="ab",  # Too short
                resource_type="project",
                scope="org:acme",
                limit_value=10,
                window_type="monthly",
            )

        # Negative limit value
        with pytest.raises(ValidationError):
            SetLimitRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                limit_value=-5,  # Negative
                window_type="monthly",
            )

        # Empty resource type
        with pytest.raises(ValidationError):
            SetLimitRequest(
                subject="user:alice",
                resource_type="",  # Empty
                scope="org:acme",
                limit_value=10,
                window_type="monthly",
            )


class TestCheckLimitRequest:
    """Tests for CheckLimitRequest model."""

    def test_valid_check_limit_request(self) -> None:
        """Test creating a valid check limit request."""
        request = CheckLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
        )

        assert request.subject == "user:alice"
        assert request.resource_type == "project"
        assert request.scope == "organization:acme"
        assert request.amount == 1  # Default
        assert request.tenant_id is None
        assert request.object_id is None

    def test_check_limit_with_custom_amount(self) -> None:
        """Test check limit request with custom amount."""
        request = CheckLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            amount=5,
        )

        assert request.amount == 5

    def test_check_limit_validation(self) -> None:
        """Test validation for check limit requests."""
        # Amount of 0 is allowed (checking if limit exists)
        request = CheckLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="org:acme",
            amount=0,
        )
        assert request.amount == 0

        # Negative amount is not allowed
        with pytest.raises(ValidationError):
            CheckLimitRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                amount=-1,  # Invalid
            )


class TestSingleCheckLimitRequest:
    """Tests for SingleCheckLimitRequest model."""

    def test_valid_single_check_request(self) -> None:
        """Test creating a valid single check limit request."""
        request = SingleCheckLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
        )

        assert request.subject == "user:alice"
        assert request.resource_type == "project"
        assert request.scope == "organization:acme"
        assert request.amount == 1
        assert request.check_id is None

    def test_single_check_with_check_id(self) -> None:
        """Test single check request with correlation ID."""
        request = SingleCheckLimitRequest(
            subject="user:alice",
            resource_type="project",
            scope="org:acme",
            check_id="check-user-limit",
        )

        assert request.check_id == "check-user-limit"


class TestIncrementUsageRequest:
    """Tests for IncrementUsageRequest model."""

    def test_valid_increment_request(self) -> None:
        """Test creating a valid increment usage request."""
        request = IncrementUsageRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
        )

        assert request.subject == "user:alice"
        assert request.resource_type == "project"
        assert request.scope == "organization:acme"
        assert request.amount == 1  # Default
        assert request.tenant_id is None
        assert request.object_id is None

    def test_increment_with_custom_amount(self) -> None:
        """Test increment request with custom amount."""
        request = IncrementUsageRequest(
            subject="user:alice",
            resource_type="api_call",
            scope="service:analytics",
            amount=100,
        )

        assert request.amount == 100

    def test_increment_with_tenant_and_object(self) -> None:
        """Test increment request with tenant_id and object_id."""
        request = IncrementUsageRequest(
            subject="user:alice",
            resource_type="project",
            scope="org:acme",
            tenant_id="org:acme",
            object_id="workspace:123",
        )

        assert request.tenant_id == "org:acme"
        assert request.object_id == "workspace:123"

    def test_increment_validation(self) -> None:
        """Test validation for increment requests."""
        # Amount must be positive
        with pytest.raises(ValidationError):
            IncrementUsageRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                amount=0,
            )


class TestResetUsageRequest:
    """Tests for ResetUsageRequest model."""

    def test_valid_reset_request(self) -> None:
        """Test creating a valid reset usage request."""
        request = ResetUsageRequest(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
        )

        assert request.subject == "user:alice"
        assert request.resource_type == "project"
        assert request.scope == "organization:acme"
        assert request.tenant_id is None
        assert request.object_id is None

    def test_reset_with_tenant_and_object(self) -> None:
        """Test reset request with tenant_id and object_id."""
        request = ResetUsageRequest(
            subject="user:alice",
            resource_type="project",
            scope="org:acme",
            tenant_id="org:acme",
            object_id="workspace:123",
        )

        assert request.tenant_id == "org:acme"
        assert request.object_id == "workspace:123"


class TestLimitDetail:
    """Tests for LimitDetail response model."""

    def test_valid_limit_detail(self) -> None:
        """Test creating a valid limit detail."""
        now = datetime.now()

        detail = LimitDetail(
            limit_id=123,
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            limit_value=10,
            window_type="monthly",
            created_at=now,
            updated_at=now,
        )

        assert detail.limit_id == 123
        assert detail.subject == "user:alice"
        assert detail.resource_type == "project"
        assert detail.scope == "organization:acme"
        assert detail.limit_value == 10
        assert detail.window_type == "monthly"
        assert detail.created_at == now
        assert detail.updated_at == now

    def test_limit_detail_with_optional_fields(self) -> None:
        """Test limit detail with all optional fields."""
        now = datetime.now()
        metadata = {"plan": "premium"}

        detail = LimitDetail(
            limit_id=456,
            subject="user:alice",
            resource_type="project",
            scope="org:acme",
            limit_value=10,
            window_type="monthly",
            created_at=now,
            updated_at=now,
            tenant_id="org:acme",
            object_id="workspace:123",
            metadata=metadata,
        )

        assert detail.tenant_id == "org:acme"
        assert detail.object_id == "workspace:123"
        assert detail.metadata == metadata


class TestCheckLimitResult:
    """Tests for CheckLimitResult response model."""

    def test_check_result_allowed(self) -> None:
        """Test check result when allowed."""
        now = datetime.now()
        resets_at = now + timedelta(days=30)

        result = CheckLimitResult(
            allowed=True,
            limit=10,
            current_usage=3,
            remaining=7,
            would_exceed=False,
            window_type="monthly",
            window_start=now,
            window_end=now + timedelta(days=30),
            resets_at=resets_at,
        )

        assert result.allowed is True
        assert result.limit == 10
        assert result.current_usage == 3
        assert result.remaining == 7
        assert result.would_exceed is False
        assert result.window_type == "monthly"

    def test_check_result_would_exceed(self) -> None:
        """Test check result when would exceed limit."""
        now = datetime.now()

        result = CheckLimitResult(
            allowed=False,
            limit=10,
            current_usage=8,
            remaining=2,
            would_exceed=True,
            window_type="daily",
            window_start=now,
            window_end=now + timedelta(days=1),
            resets_at=now + timedelta(days=1),
        )

        assert result.allowed is False
        assert result.would_exceed is True
        assert result.limit == 10
        assert result.current_usage == 8
        assert result.remaining == 2


class TestSingleCheckLimitResult:
    """Tests for SingleCheckLimitResult response model."""

    def test_single_check_result_with_check_id(self) -> None:
        """Test single check result with correlation ID."""
        now = datetime.now()

        result = SingleCheckLimitResult(
            check_id="check-user-limit",
            allowed=True,
            limit=100,
            current_usage=45,
            remaining=55,
            would_exceed=False,
            window_type="monthly",
            window_start=now,
            window_end=now + timedelta(days=30),
            resets_at=now + timedelta(days=30),
        )

        assert result.check_id == "check-user-limit"
        assert result.allowed is True


class TestCheckManyLimitsResult:
    """Tests for CheckManyLimitsResult response model."""

    def test_check_many_all_allowed(self) -> None:
        """Test check many result when all allowed."""
        now = datetime.now()

        results = [
            SingleCheckLimitResult(
                check_id="user-limit",
                allowed=True,
                limit=10,
                current_usage=3,
                remaining=7,
                would_exceed=False,
                window_type="monthly",
                window_start=now,
                window_end=now + timedelta(days=30),
                resets_at=now + timedelta(days=30),
            ),
            SingleCheckLimitResult(
                check_id="org-limit",
                allowed=True,
                limit=100,
                current_usage=45,
                remaining=55,
                would_exceed=False,
                window_type="monthly",
                window_start=now,
                window_end=now + timedelta(days=30),
                resets_at=now + timedelta(days=30),
            ),
        ]

        result = CheckManyLimitsResult(
            results=results,
        )

        assert len(result.results) == 2
        # Check all allowed via client-side logic
        assert all(r.allowed for r in result.results)

    def test_check_many_some_denied(self) -> None:
        """Test check many result when some denied."""
        now = datetime.now()

        results = [
            SingleCheckLimitResult(
                check_id="user-limit",
                allowed=False,
                limit=10,
                current_usage=10,
                remaining=0,
                would_exceed=True,
                window_type="monthly",
                window_start=now,
                window_end=now + timedelta(days=30),
                resets_at=now + timedelta(days=30),
            ),
            SingleCheckLimitResult(
                check_id="org-limit",
                allowed=True,
                limit=100,
                current_usage=45,
                remaining=55,
                would_exceed=False,
                window_type="monthly",
                window_start=now,
                window_end=now + timedelta(days=30),
                resets_at=now + timedelta(days=30),
            ),
        ]

        result = CheckManyLimitsResult(
            results=results,
        )

        assert len(result.results) == 2
        # Check all allowed via client-side logic
        assert not all(r.allowed for r in result.results)


class TestIncrementUsageResult:
    """Tests for IncrementUsageResult response model."""

    def test_increment_result(self) -> None:
        """Test increment usage result."""
        now = datetime.now()

        result = IncrementUsageResult(
            success=True,
            current_usage=4,
            limit=10,
            remaining=6,
            window_start=now,
            window_end=now + timedelta(days=30),
        )

        assert result.success is True
        assert result.current_usage == 4
        assert result.limit == 10
        assert result.remaining == 6
        assert result.window_start == now

    def test_increment_result_at_limit(self) -> None:
        """Test increment result when at limit."""
        now = datetime.now()

        result = IncrementUsageResult(
            success=True,
            current_usage=10,
            limit=10,
            remaining=0,
            window_start=now,
            window_end=now + timedelta(days=30),
        )

        assert result.success is True
        assert result.current_usage == 10
        assert result.remaining == 0


class TestCheckManyLimitsRequest:
    """Tests for CheckManyLimitsRequest model."""

    def test_valid_check_many_request(self) -> None:
        """Test creating a valid check many request."""
        checks = [
            SingleCheckLimitRequest(
                check_id="user-limit",
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                amount=1,
                tenant_id="org:acme",
            ),
            SingleCheckLimitRequest(
                check_id="system-limit",
                subject="user:alice",
                resource_type="project",
                scope="system",
                amount=1,
            ),
        ]

        request = CheckManyLimitsRequest(checks=checks)

        assert len(request.checks) == 2
        assert request.checks[0].check_id == "user-limit"
        assert request.checks[1].check_id == "system-limit"

    def test_check_many_single_check(self) -> None:
        """Test check many request with single check."""
        checks = [
            SingleCheckLimitRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
            ),
        ]

        request = CheckManyLimitsRequest(checks=checks)

        assert len(request.checks) == 1

    def test_check_many_validation_empty_list(self) -> None:
        """Test validation for empty checks list."""
        with pytest.raises(ValidationError) as exc_info:
            CheckManyLimitsRequest(checks=[])
        assert "checks" in str(exc_info.value).lower()

    def test_check_many_validation_too_many(self) -> None:
        """Test validation for too many checks."""
        # Create 101 checks (exceeds max of 100)
        checks = [
            SingleCheckLimitRequest(
                subject=f"user:{i}",
                resource_type="project",
                scope="org:acme",
            )
            for i in range(101)
        ]

        with pytest.raises(ValidationError) as exc_info:
            CheckManyLimitsRequest(checks=checks)
        assert "checks" in str(exc_info.value).lower()


class TestIncrementManyRequest:
    """Tests for IncrementManyRequest model."""

    def test_valid_increment_many_request(self) -> None:
        """Test creating a valid increment many request."""
        increments = [
            IncrementUsageRequest(
                subject="user:alice",
                resource_type="scan",
                scope="org:acme",
                amount=1,
                tenant_id="org:acme",
            ),
            IncrementUsageRequest(
                subject="org:acme",
                resource_type="scan",
                scope="system",
                amount=1,
            ),
        ]

        request = IncrementManyRequest(increments=increments)

        assert len(request.increments) == 2
        assert request.increments[0].subject == "user:alice"
        assert request.increments[1].subject == "org:acme"

    def test_increment_many_single_increment(self) -> None:
        """Test increment many request with single increment."""
        increments = [
            IncrementUsageRequest(
                subject="user:alice",
                resource_type="project",
                scope="org:acme",
                amount=5,
            ),
        ]

        request = IncrementManyRequest(increments=increments)

        assert len(request.increments) == 1
        assert request.increments[0].amount == 5

    def test_increment_many_validation_empty_list(self) -> None:
        """Test validation for empty increments list."""
        with pytest.raises(ValidationError) as exc_info:
            IncrementManyRequest(increments=[])
        assert "increments" in str(exc_info.value).lower()

    def test_increment_many_validation_too_many(self) -> None:
        """Test validation for too many increments."""
        # Create 101 increments (exceeds max of 100)
        increments = [
            IncrementUsageRequest(
                subject=f"user:{i}",
                resource_type="project",
                scope="org:acme",
            )
            for i in range(101)
        ]

        with pytest.raises(ValidationError) as exc_info:
            IncrementManyRequest(increments=increments)
        assert "increments" in str(exc_info.value).lower()


class TestIncrementManyResult:
    """Tests for IncrementManyResult response model."""

    def test_increment_many_result(self) -> None:
        """Test increment many result."""
        now = datetime.now()

        results = [
            IncrementUsageResult(
                success=True,
                current_usage=4,
                limit=10,
                remaining=6,
                window_start=now,
                window_end=now + timedelta(days=30),
            ),
            IncrementUsageResult(
                success=True,
                current_usage=25,
                limit=100,
                remaining=75,
                window_start=now,
                window_end=now + timedelta(days=30),
            ),
        ]

        result = IncrementManyResult(results=results)

        assert len(result.results) == 2
        assert all(r.success for r in result.results)
        assert result.results[0].current_usage == 4
        assert result.results[1].current_usage == 25

    def test_increment_many_result_mixed_success(self) -> None:
        """Test increment many result with mixed success status."""
        now = datetime.now()

        results = [
            IncrementUsageResult(
                success=True,
                current_usage=5,
                limit=10,
                remaining=5,
                window_start=now,
                window_end=now + timedelta(days=1),
            ),
            IncrementUsageResult(
                success=True,
                current_usage=10,
                limit=10,
                remaining=0,
                window_start=now,
                window_end=now + timedelta(days=1),
            ),
        ]

        result = IncrementManyResult(results=results)

        assert len(result.results) == 2
        assert result.results[0].remaining == 5
        assert result.results[1].remaining == 0


class TestUsageDetail:
    """Tests for UsageDetail response model."""

    def test_usage_detail(self) -> None:
        """Test usage detail."""
        now = datetime.now()
        last_increment = now - timedelta(minutes=30)

        detail = UsageDetail(
            subject="user:alice",
            resource_type="api_call",
            scope="service:analytics",
            limit=1000,
            current_usage=850,
            remaining=150,
            window_type="hourly",
            window_start=now,
            window_end=now + timedelta(hours=1),
            last_increment_at=last_increment,
            is_expired=False,
        )

        assert detail.subject == "user:alice"
        assert detail.resource_type == "api_call"
        assert detail.scope == "service:analytics"
        assert detail.current_usage == 850
        assert detail.limit == 1000
        assert detail.remaining == 150
        assert detail.window_type == "hourly"
        assert detail.is_expired is False

    def test_usage_detail_without_last_increment(self) -> None:
        """Test usage detail without last increment."""
        now = datetime.now()

        detail = UsageDetail(
            subject="user:bob",
            resource_type="query",
            scope="service:database",
            limit=100,
            current_usage=0,
            remaining=100,
            window_type="daily",
            window_start=now,
            window_end=now + timedelta(days=1),
            last_increment_at=None,
            is_expired=False,
        )

        assert detail.last_increment_at is None
        assert detail.current_usage == 0


class TestResetUsageResult:
    """Tests for ResetUsageResult response model."""

    def test_reset_result(self) -> None:
        """Test reset usage result."""
        result = ResetUsageResult(
            reset=True,
            previous_usage=47,
            current_usage=0,
        )

        assert result.reset is True
        assert result.previous_usage == 47
        assert result.current_usage == 0


class TestLimitFilter:
    """Tests for LimitFilter model."""

    def test_default_filter(self) -> None:
        """Test filter with default values."""
        filters = LimitFilter()

        assert filters.subject is None
        assert filters.resource_type is None
        assert filters.scope is None
        assert filters.tenant_id is None
        assert filters.limit == 100
        assert filters.offset == 0

    def test_custom_filter(self) -> None:
        """Test filter with custom values."""
        filters = LimitFilter(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            tenant_id="org:acme",
            limit=50,
            offset=100,
        )

        assert filters.subject == "user:alice"
        assert filters.resource_type == "project"
        assert filters.scope == "organization:acme"
        assert filters.tenant_id == "org:acme"
        assert filters.limit == 50
        assert filters.offset == 100

    def test_filter_validation(self) -> None:
        """Test filter validation."""
        # Limit too low
        with pytest.raises(ValidationError):
            LimitFilter(limit=0)

        # Limit too high
        with pytest.raises(ValidationError):
            LimitFilter(limit=1001)

        # Negative offset
        with pytest.raises(ValidationError):
            LimitFilter(offset=-1)
