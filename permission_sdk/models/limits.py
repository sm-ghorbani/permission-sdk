"""Resource limit-related data models.

This module contains all models related to resource limit operations including
setting limits, checking limits, incrementing usage, and managing quotas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SetLimitRequest(BaseModel):
    """Request to set or update a resource limit.

    Attributes:
        subject: Subject identifier (format: 'type:id')
        resource_type: Type of resource (e.g., 'project', 'api_call')
        scope: Scope identifier
        limit_value: Maximum allowed consumption
        window_type: Time window ('hourly', 'daily', 'monthly', 'total')
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier
        expires_at: Optional expiration datetime for temporary limits
        metadata: Optional metadata dictionary

    Example:
        >>> request = SetLimitRequest(
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     limit_value=10,
        ...     window_type="monthly",
        ...     tenant_id="org:456",
        ...     expires_at=datetime(2025, 12, 31)
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    limit_value: int = Field(..., ge=0, description="Maximum allowed consumption")
    window_type: str = Field(
        ..., pattern="^(hourly|daily|monthly|total)$", description="Time window type"
    )
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")
    expires_at: datetime | None = Field(default=None, description="Expiration datetime for temporary limits")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class CheckLimitRequest(BaseModel):
    """Request to check if consuming amount would exceed limit.

    Attributes:
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        amount: Amount to check (default: 1)
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> request = CheckLimitRequest(
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     amount=1,
        ...     tenant_id="org:456"
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    amount: int = Field(default=1, ge=0, description="Amount to check")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")


class SingleCheckLimitRequest(BaseModel):
    """Single limit check within a batch request.

    Used for batch checking operations like hierarchy checks (org + system limits).

    Attributes:
        check_id: Optional correlation ID for matching request/response
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        amount: Amount to check (default: 1)
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> request = SingleCheckLimitRequest(
        ...     check_id="org",
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     amount=1,
        ...     tenant_id="org:A"
        ... )
    """

    check_id: str | None = Field(
        default=None, description="Correlation ID for request/response matching"
    )
    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    amount: int = Field(default=1, ge=0, description="Amount to check")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")


class IncrementUsageRequest(BaseModel):
    """Request to increment resource usage counter.

    Attributes:
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        amount: Amount to increment (default: 1)
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> request = IncrementUsageRequest(
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     amount=1,
        ...     tenant_id="org:456"
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    amount: int = Field(default=1, ge=1, description="Amount to increment")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")


class ResetUsageRequest(BaseModel):
    """Request to reset resource usage counter to 0.

    Attributes:
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> request = ResetUsageRequest(
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     tenant_id="org:456"
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")


class LimitDetail(BaseModel):
    """Detailed resource limit information.

    Attributes:
        limit_id: Unique identifier for this limit
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        limit_value: Maximum allowed consumption
        window_type: Time window type
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier
        expires_at: Optional expiration datetime for temporary limits
        created_at: When limit was created
        updated_at: When limit was last updated
        metadata: Optional additional metadata
        window_changed: Whether the window_type was changed (usage was reset)
        previous_window_type: Previous window_type if changed
        previous_usage: Previous usage value before reset

    Example:
        >>> limit = LimitDetail(
        ...     limit_id=123,
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     limit_value=10,
        ...     window_type="monthly",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now(),
        ...     expires_at=datetime(2025, 12, 31),
        ...     window_changed=False
        ... )
    """

    limit_id: int = Field(..., description="Unique limit identifier")
    subject: str = Field(..., description="Subject identifier")
    resource_type: str = Field(..., description="Type of resource")
    scope: str = Field(..., description="Scope identifier")
    limit_value: int = Field(..., description="Maximum allowed consumption")
    window_type: str = Field(..., description="Time window type")
    tenant_id: str | None = Field(default=None, description="Tenant identifier")
    object_id: str | None = Field(default=None, description="Object identifier")
    expires_at: datetime | None = Field(default=None, description="Expiration datetime for temporary limits")
    created_at: datetime = Field(..., description="When limit was created")
    updated_at: datetime = Field(..., description="When limit was last updated")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")
    window_changed: bool = Field(
        default=False, description="Whether the window_type was changed (usage was reset)"
    )
    previous_window_type: str | None = Field(
        default=None, description="Previous window_type if changed"
    )
    previous_usage: int | None = Field(
        default=None, description="Previous usage value before reset"
    )


class CheckLimitResult(BaseModel):
    """Result of a limit check operation.

    Attributes:
        allowed: Whether the consumption is allowed
        limit: Maximum allowed consumption
        current_usage: Current usage count
        remaining: Remaining quota
        would_exceed: Whether the amount would exceed limit
        window_type: Time window type
        window_start: Start of current window
        window_end: End of current window
        resets_at: When usage will reset (alias for window_end)

    Example:
        >>> result = CheckLimitResult(
        ...     allowed=True,
        ...     limit=10,
        ...     current_usage=3,
        ...     remaining=7,
        ...     would_exceed=False,
        ...     window_type="monthly",
        ...     window_start=datetime.now(),
        ...     window_end=datetime.now(),
        ...     resets_at=datetime.now()
        ... )
        >>> if result.allowed:
        ...     print(f"Can proceed. {result.remaining} remaining.")
    """

    allowed: bool = Field(..., description="Whether consumption is allowed")
    limit: int = Field(..., description="Maximum allowed consumption")
    current_usage: int = Field(..., description="Current usage count")
    remaining: int = Field(..., description="Remaining quota")
    would_exceed: bool = Field(..., description="Whether amount would exceed limit")
    window_type: str = Field(..., description="Time window type")
    window_start: datetime = Field(..., description="Start of current window")
    window_end: datetime = Field(..., description="End of current window")
    resets_at: datetime = Field(..., description="When usage will reset")


class SingleCheckLimitResult(BaseModel):
    """Single result within a batch check operation.

    Attributes:
        check_id: Correlation ID from request
        allowed: Whether the consumption is allowed
        limit: Maximum allowed consumption
        current_usage: Current usage count
        remaining: Remaining quota
        would_exceed: Whether the amount would exceed limit
        window_type: Time window type
        window_start: Start of current window
        window_end: End of current window
        resets_at: When usage will reset

    Example:
        >>> result = SingleCheckLimitResult(
        ...     check_id="org",
        ...     allowed=True,
        ...     limit=10,
        ...     current_usage=3,
        ...     remaining=7,
        ...     would_exceed=False,
        ...     window_type="monthly",
        ...     window_start=datetime.now(),
        ...     window_end=datetime.now(),
        ...     resets_at=datetime.now()
        ... )
    """

    check_id: str | None = Field(default=None, description="Correlation ID")
    allowed: bool = Field(..., description="Whether consumption is allowed")
    limit: int = Field(..., description="Maximum allowed consumption")
    current_usage: int = Field(..., description="Current usage count")
    remaining: int = Field(..., description="Remaining quota")
    would_exceed: bool = Field(..., description="Whether amount would exceed limit")
    window_type: str = Field(..., description="Time window type")
    window_start: datetime = Field(..., description="Start of current window")
    window_end: datetime = Field(..., description="End of current window")
    resets_at: datetime = Field(..., description="When usage will reset")


class UsageDetail(BaseModel):
    """Current usage information for a resource.

    Attributes:
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        limit: Maximum allowed consumption
        current_usage: Current usage count
        remaining: Remaining quota
        window_type: Time window type
        window_start: Start of current window
        window_end: End of current window
        last_increment_at: When usage was last incremented
        is_expired: Whether the usage window has expired
        limit_expires_at: When the limit policy expires
        is_limit_expired: Whether the limit policy has expired

    Example:
        >>> usage = UsageDetail(
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     limit=10,
        ...     current_usage=3,
        ...     remaining=7,
        ...     window_type="monthly",
        ...     window_start=datetime.now(),
        ...     window_end=datetime.now(),
        ...     is_expired=False,
        ...     limit_expires_at=datetime(2025, 12, 31),
        ...     is_limit_expired=False
        ... )
    """

    subject: str = Field(..., description="Subject identifier")
    resource_type: str = Field(..., description="Type of resource")
    scope: str = Field(..., description="Scope identifier")
    limit: int = Field(..., description="Maximum allowed consumption")
    current_usage: int = Field(..., description="Current usage count")
    remaining: int = Field(..., description="Remaining quota")
    window_type: str = Field(..., description="Time window type")
    window_start: datetime = Field(..., description="Start of current window")
    window_end: datetime = Field(..., description="End of current window")
    last_increment_at: datetime | None = Field(
        default=None, description="When usage was last incremented"
    )
    is_expired: bool = Field(..., description="Whether usage window has expired")
    limit_expires_at: datetime | None = Field(
        default=None, description="When the limit policy expires"
    )
    is_limit_expired: bool = Field(..., description="Whether the limit policy has expired")


class IncrementUsageResult(BaseModel):
    """Result of incrementing usage counter.

    Attributes:
        success: Whether increment was successful
        current_usage: Updated usage count
        limit: Maximum allowed consumption
        remaining: Remaining quota after increment
        window_start: Start of current window
        window_end: End of current window

    Example:
        >>> result = IncrementUsageResult(
        ...     success=True,
        ...     current_usage=4,
        ...     limit=10,
        ...     remaining=6,
        ...     window_start=datetime.now(),
        ...     window_end=datetime.now()
        ... )
    """

    success: bool = Field(..., description="Whether increment was successful")
    current_usage: int = Field(..., description="Updated usage count")
    limit: int = Field(..., description="Maximum allowed consumption")
    remaining: int = Field(..., description="Remaining quota after increment")
    window_start: datetime = Field(..., description="Start of current window")
    window_end: datetime = Field(..., description="End of current window")


class ResetUsageResult(BaseModel):
    """Result of resetting usage counter.

    Attributes:
        reset: Whether reset was successful
        previous_usage: Usage count before reset
        current_usage: Usage count after reset (always 0)

    Example:
        >>> result = ResetUsageResult(
        ...     reset=True,
        ...     previous_usage=5,
        ...     current_usage=0
        ... )
        >>> print(f"Reset from {result.previous_usage} to {result.current_usage}")
    """

    reset: bool = Field(..., description="Whether reset was successful")
    previous_usage: int = Field(..., description="Usage count before reset")
    current_usage: int = Field(..., description="Usage count after reset")


class IncrementManyRequest(BaseModel):
    """Request to increment multiple resource usages in batch.

    Optimized for hierarchy updates where you need to increment
    usage at multiple levels (user → org → parent → root).

    Attributes:
        increments: List of usage increments to perform

    Example:
        >>> request = IncrementManyRequest(
        ...     increments=[
        ...         IncrementUsageRequest(
        ...             subject="user:123",
        ...             resource_type="scan",
        ...             scope="org:A",
        ...             amount=1,
        ...             tenant_id="org:A"
        ...         ),
        ...         IncrementUsageRequest(
        ...             subject="org:A",
        ...             resource_type="scan",
        ...             scope="system",
        ...             amount=1
        ...         ),
        ...     ]
        ... )
    """

    increments: list[IncrementUsageRequest] = Field(
        ..., min_length=1, max_length=100, description="List of usage increments to perform"
    )


class IncrementManyResult(BaseModel):
    """Result of batch increment operation.

    Attributes:
        results: List of increment results in same order as requests

    Example:
        >>> result = IncrementManyResult(
        ...     results=[
        ...         IncrementUsageResult(success=True, current_usage=5, ...),
        ...         IncrementUsageResult(success=True, current_usage=10, ...),
        ...     ]
        ... )
    """

    results: list[IncrementUsageResult] = Field(..., description="List of increment results")


class CheckManyLimitsRequest(BaseModel):
    """Request to check multiple resource limits in batch.

    Attributes:
        checks: List of limit checks to perform

    Example:
        >>> request = CheckManyLimitsRequest(
        ...     checks=[
        ...         SingleCheckLimitRequest(
        ...             check_id="org",
        ...             subject="user:123",
        ...             resource_type="project",
        ...             scope="projects",
        ...             amount=1,
        ...             tenant_id="org:A"
        ...         ),
        ...         SingleCheckLimitRequest(
        ...             check_id="system",
        ...             subject="user:123",
        ...             resource_type="project",
        ...             scope="projects",
        ...             amount=1
        ...         ),
        ...     ]
        ... )
    """

    checks: list[SingleCheckLimitRequest] = Field(
        ..., min_length=1, max_length=100, description="List of limit checks to perform"
    )


class CheckManyLimitsResult(BaseModel):
    """Result of batch limit check operation.

    Attributes:
        results: List of check results in same order as requests

    Example:
        >>> result = CheckManyLimitsResult(
        ...     results=[
        ...         SingleCheckLimitResult(check_id="org", allowed=True, ...),
        ...         SingleCheckLimitResult(check_id="system", allowed=True, ...),
        ...     ]
        ... )
        >>> # Hierarchy enforcement: caller applies logic
        >>> allowed = all(r.allowed for r in result.results)
    """

    results: list[SingleCheckLimitResult] = Field(..., description="List of check results")


class LimitFilter(BaseModel):
    """Filter criteria for listing resource limits.

    All filter fields are optional and will be combined with AND logic.

    Attributes:
        subject: Filter by subject identifier
        resource_type: Filter by resource type
        scope: Filter by scope identifier
        tenant_id: Filter by tenant
        limit: Number of results per page (1-1000)
        offset: Pagination offset

    Example:
        >>> filters = LimitFilter(
        ...     subject="user:123",
        ...     tenant_id="org:456",
        ...     limit=50
        ... )
        >>> limits = client.list_limits(filters)
    """

    subject: str | None = Field(default=None, description="Filter by subject")
    resource_type: str | None = Field(default=None, description="Filter by resource type")
    scope: str | None = Field(default=None, description="Filter by scope")
    tenant_id: str | None = Field(default=None, description="Filter by tenant")
    limit: int = Field(default=100, ge=1, le=1000, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class CheckAndIncrementRequest(BaseModel):
    """Request to atomically check limit and increment if allowed.

    This combines check_limit() and increment_usage() into a single atomic
    operation, eliminating TOCTOU (Time-Of-Check-Time-Of-Use) race conditions.

    If the increment would NOT exceed the limit, it is performed atomically.
    If it WOULD exceed the limit, no increment occurs.

    Attributes:
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        amount: Amount to consume (default: 1)
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> request = CheckAndIncrementRequest(
        ...     subject="user:123",
        ...     resource_type="project",
        ...     scope="projects",
        ...     amount=1,
        ...     tenant_id="org:456"
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    amount: int = Field(default=1, ge=0, description="Amount to consume")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")


class CheckAndIncrementResult(BaseModel):
    """Result of atomic check-and-increment operation.

    Attributes:
        allowed: Whether the increment was allowed (within limit)
        incremented: Whether usage was actually incremented
        limit: Maximum allowed value
        current_usage: Usage after potential increment
        remaining: Limit - current_usage
        would_exceed: Whether the increment would have exceeded limit
        window_type: Type of time window
        window_start: Start of current window
        window_end: End of current window
        resets_at: When the window resets (alias for window_end)
        is_limit_expired: Whether the limit policy has expired

    Example:
        >>> result = CheckAndIncrementResult(
        ...     allowed=True,
        ...     incremented=True,
        ...     limit=10,
        ...     current_usage=4,
        ...     remaining=6,
        ...     would_exceed=False,
        ...     window_type="monthly",
        ...     window_start=datetime.now(),
        ...     window_end=datetime.now(),
        ...     resets_at=datetime.now(),
        ...     is_limit_expired=False
        ... )
        >>> if result.allowed:
        ...     print(f"Success! Usage incremented. {result.remaining} remaining.")
        ... else:
        ...     print(f"Denied. Would exceed limit.")
    """

    allowed: bool = Field(..., description="Whether increment was allowed")
    incremented: bool = Field(..., description="Whether usage was actually incremented")
    limit: int = Field(..., description="Maximum allowed value")
    current_usage: int = Field(..., description="Usage after potential increment")
    remaining: int = Field(..., description="Remaining quota")
    would_exceed: bool = Field(..., description="Whether increment would exceed limit")
    window_type: str = Field(..., description="Type of time window")
    window_start: datetime = Field(..., description="Start of current window")
    window_end: datetime = Field(..., description="End of current window")
    resets_at: datetime = Field(..., description="When the window resets")
    is_limit_expired: bool = Field(
        default=False, description="Whether the limit policy has expired"
    )


class SingleCheckAndIncrementRequest(BaseModel):
    """Single check-and-increment within a batch request.

    Used for batch atomic operations like hierarchy checks (org + system limits).

    Attributes:
        subject: Subject identifier
        resource_type: Type of resource
        scope: Scope identifier
        amount: Amount to consume (default: 1)
        tenant_id: Optional tenant identifier
        object_id: Optional object identifier

    Example:
        >>> request = SingleCheckAndIncrementRequest(
        ...     subject="user:123",
        ...     resource_type="scan",
        ...     scope="org:A",
        ...     amount=1,
        ...     tenant_id="org:A"
        ... )
    """

    subject: str = Field(..., min_length=3, max_length=255, description="Subject identifier")
    resource_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of resource"
    )
    scope: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    amount: int = Field(default=1, ge=0, description="Amount to consume")
    tenant_id: str | None = Field(default=None, max_length=255, description="Tenant identifier")
    object_id: str | None = Field(default=None, max_length=255, description="Object identifier")


class CheckAndIncrementManyRequest(BaseModel):
    """Request to atomically check and increment multiple limits.

    This is useful for hierarchy operations where you need to check and
    increment at multiple levels (user → org → system) atomically.

    Attributes:
        checks: List of check-and-increment operations to perform

    Example:
        >>> request = CheckAndIncrementManyRequest(
        ...     checks=[
        ...         SingleCheckAndIncrementRequest(
        ...             subject="user:123",
        ...             resource_type="scan",
        ...             scope="org:A",
        ...             amount=1,
        ...             tenant_id="org:A"
        ...         ),
        ...         SingleCheckAndIncrementRequest(
        ...             subject="org:A",
        ...             resource_type="scan",
        ...             scope="system",
        ...             amount=1
        ...         ),
        ...     ]
        ... )
    """

    checks: list[SingleCheckAndIncrementRequest] = Field(
        ..., min_length=1, max_length=100, description="List of check-and-increment operations"
    )


class CheckAndIncrementManyResult(BaseModel):
    """Result of batch check-and-increment operation.

    Attributes:
        results: List of check-and-increment results in same order as requests

    Example:
        >>> result = CheckAndIncrementManyResult(
        ...     results=[
        ...         CheckAndIncrementResult(allowed=True, incremented=True, ...),
        ...         CheckAndIncrementResult(allowed=True, incremented=True, ...),
        ...     ]
        ... )
        >>> # All checks evaluated and increments performed atomically
        >>> if all(r.allowed for r in result.results):
        ...     print("All limits passed!")
        ... else:
        ...     print("At least one limit exceeded - transaction rolled back")
    """

    results: list[CheckAndIncrementResult] = Field(
        ..., description="List of check-and-increment results"
    )
