"""Permission SDK - Python client for Permission Service API.

This SDK provides a simple, type-safe interface for interacting with the
Permission Service microservice.

Quick Start:
    >>> from permission_sdk import PermissionClient, SDKConfig
    >>>
    >>> config = SDKConfig(
    ...     base_url="https://permissions.example.com",
    ...     api_key="your-api-key"
    ... )
    >>>
    >>> with PermissionClient(config) as client:
    ...     # Grant permission
    ...     client.grant_permission(
    ...         subject="user:123",
    ...         scope="documents.management",
    ...         action="edit"
    ...     )
    ...
    ...     # Check permission
    ...     allowed = client.check_permission(
    ...         subjects=["user:123"],
    ...         scope="documents.management",
    ...         action="edit"
    ...     )
    ...     print(f"Allowed: {allowed}")
"""

__version__ = "1.0.0"

from permission_sdk.async_client import AsyncPermissionClient
from permission_sdk.client import PermissionClient
from permission_sdk.config import SDKConfig
from permission_sdk.exceptions import (
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    PermissionSDKError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    TimeoutError,
    ValidationError,
)
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

__all__ = [
    # Version
    "__version__",
    # Clients
    "PermissionClient",
    "AsyncPermissionClient",
    # Config
    "SDKConfig",
    # Exceptions
    "PermissionSDKError",
    "ConfigurationError",
    "AuthenticationError",
    "ValidationError",
    "ResourceNotFoundError",
    "ServerError",
    "NetworkError",
    "RateLimitError",
    "TimeoutError",
    # Models
    "PermissionAssignment",
    "PermissionDetail",
    "GrantRequest",
    "RevokeRequest",
    "CheckRequest",
    "CheckResult",
    "GrantManyResult",
    "PermissionFilter",
    "Subject",
    "SubjectFilter",
    "Scope",
    "ScopeFilter",
    "PaginatedResponse",
]
