"""Data models for the Permission SDK.

This package contains all Pydantic models used for request/response serialization.
"""

from permission_sdk.models.common import PaginatedResponse
from permission_sdk.models.limits import (
    CheckAndIncrementManyRequest,
    CheckAndIncrementManyResult,
    CheckAndIncrementRequest,
    CheckAndIncrementResult,
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
    SingleCheckAndIncrementRequest,
    SingleCheckLimitRequest,
    SingleCheckLimitResult,
    UsageDetail,
)
from permission_sdk.models.permissions import (
    CheckRequest,
    CheckResult,
    GrantManyResult,
    GrantRequest,
    PermissionAssignment,
    PermissionDetail,
    PermissionFilter,
    RevokeRequest,
)
from permission_sdk.models.scopes import Scope, ScopeFilter
from permission_sdk.models.subjects import Subject, SubjectFilter

__all__ = [
    # Common
    "PaginatedResponse",
    # Permissions
    "PermissionAssignment",
    "PermissionDetail",
    "GrantRequest",
    "RevokeRequest",
    "CheckRequest",
    "CheckResult",
    "GrantManyResult",
    "PermissionFilter",
    # Subjects
    "Subject",
    "SubjectFilter",
    # Scopes
    "Scope",
    "ScopeFilter",
    # Resource Limits
    "LimitDetail",
    "SetLimitRequest",
    "CheckLimitRequest",
    "CheckLimitResult",
    "SingleCheckLimitRequest",
    "SingleCheckLimitResult",
    "CheckManyLimitsRequest",
    "CheckManyLimitsResult",
    "CheckAndIncrementRequest",
    "CheckAndIncrementResult",
    "SingleCheckAndIncrementRequest",
    "CheckAndIncrementManyRequest",
    "CheckAndIncrementManyResult",
    "IncrementUsageRequest",
    "IncrementUsageResult",
    "IncrementManyRequest",
    "IncrementManyResult",
    "UsageDetail",
    "ResetUsageRequest",
    "ResetUsageResult",
    "LimitFilter",
]
