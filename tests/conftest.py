"""Pytest configuration and fixtures for SDK tests.

This module provides common fixtures and configuration for all tests.
"""

from datetime import datetime
from typing import Any

import pytest
import requests_mock
import respx

from permission_sdk import (
    AsyncPermissionClient,
    PermissionClient,
    SDKConfig,
)
from permission_sdk.models import (
    PermissionAssignment,
    PermissionDetail,
    Subject,
)


# ==================== Configuration Fixtures ====================


@pytest.fixture
def sdk_config() -> SDKConfig:
    """Create a test SDK configuration.

    Returns:
        SDKConfig instance for testing
    """
    return SDKConfig(
        base_url="http://test-api.example.com",
        api_key="test-api-key-12345",
        timeout=30,
        max_retries=2,
        validate_identifiers=True,
    )


@pytest.fixture
def sdk_config_no_validation() -> SDKConfig:
    """Create SDK config with validation disabled.

    Returns:
        SDKConfig with validate_identifiers=False
    """
    return SDKConfig(
        base_url="http://test-api.example.com",
        api_key="test-api-key",
        timeout=30,
        validate_identifiers=False,
    )


# ==================== Client Fixtures ====================


@pytest.fixture
def sync_client(sdk_config: SDKConfig) -> PermissionClient:
    """Create a synchronous Permission client.

    Args:
        sdk_config: SDK configuration fixture

    Returns:
        PermissionClient instance
    """
    return PermissionClient(sdk_config)


@pytest.fixture
async def async_client(sdk_config: SDKConfig) -> AsyncPermissionClient:
    """Create an asynchronous Permission client.

    Args:
        sdk_config: SDK configuration fixture

    Returns:
        AsyncPermissionClient instance
    """
    client = AsyncPermissionClient(sdk_config)
    yield client
    await client.close()


# ==================== Mock HTTP Fixtures ====================


@pytest.fixture
def mock_requests() -> requests_mock.Mocker:
    """Create requests mock for testing sync client.

    Returns:
        requests_mock.Mocker instance

    Example:
        >>> def test_grant(mock_requests):
        ...     mock_requests.post(
        ...         "http://test-api.example.com/api/v1/permissions/grant",
        ...         json={"assignment_id": "123", ...}
        ...     )
    """
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def mock_httpx() -> respx.MockRouter:
    """Create httpx mock for testing async client.

    Returns:
        respx.MockRouter instance

    Example:
        >>> async def test_grant(mock_httpx):
        ...     mock_httpx.post(
        ...         "http://test-api.example.com/api/v1/permissions/grant"
        ...     ).mock(return_value=httpx.Response(200, json={...}))
    """
    with respx.mock:
        yield respx


# ==================== Sample Data Fixtures ====================


@pytest.fixture
def sample_permission_assignment() -> dict[str, Any]:
    """Create sample permission assignment data.

    Returns:
        Dictionary representing a permission assignment
    """
    return {
        "assignment_id": "perm_abc123",
        "subject": "user:alice",
        "scope": "documents.management",
        "action": "read",
        "tenant_id": "org:acme",
        "object_id": None,
        "granted_at": datetime.now().isoformat(),
        "expires_at": None,
        "metadata": {"granted_by": "admin:1"},
    }


@pytest.fixture
def sample_permission_detail() -> dict[str, Any]:
    """Create sample permission detail data.

    Returns:
        Dictionary representing a permission detail
    """
    return {
        "assignment_id": "perm_abc123",
        "subject": "user:alice",
        "subject_type": "user",
        "subject_display_name": "Alice Smith",
        "scope": "documents.management",
        "scope_display_name": "Document Management",
        "action": "read",
        "tenant_id": "org:acme",
        "object_id": None,
        "granted_at": datetime.now().isoformat(),
        "expires_at": None,
        "is_valid": True,
        "metadata": None,
    }


@pytest.fixture
def sample_subject() -> dict[str, Any]:
    """Create sample subject data.

    Returns:
        Dictionary representing a subject
    """
    return {
        "id": "subj_123",
        "identifier": "user:alice",
        "subject_type": "user",
        "subject_id": "alice",
        "display_name": "Alice Smith",
        "tenant_id": "org:acme",
        "metadata": {"email": "alice@acme.com"},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_scope() -> dict[str, Any]:
    """Create sample scope data.

    Returns:
        Dictionary representing a scope
    """
    return {
        "id": "scope_123",
        "identifier": "documents.management",
        "display_name": "Document Management",
        "description": "Permissions for managing documents",
        "metadata": {"category": "content"},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


# ==================== Error Response Fixtures ====================


@pytest.fixture
def error_response_401() -> dict[str, Any]:
    """Create sample 401 error response.

    Returns:
        Dictionary representing an authentication error
    """
    return {
        "detail": "Invalid API key",
        "error_type": "AuthenticationError",
    }


@pytest.fixture
def error_response_400() -> dict[str, Any]:
    """Create sample 400 error response.

    Returns:
        Dictionary representing a validation error
    """
    return {
        "detail": "Invalid subject identifier format",
        "error_type": "ValidationError",
        "field": "subject",
    }


@pytest.fixture
def error_response_404() -> dict[str, Any]:
    """Create sample 404 error response.

    Returns:
        Dictionary representing a not found error
    """
    return {
        "detail": "Subject not found",
        "error_type": "ResourceNotFoundError",
        "resource_type": "Subject",
    }


@pytest.fixture
def error_response_429() -> dict[str, Any]:
    """Create sample 429 error response.

    Returns:
        Dictionary representing a rate limit error
    """
    return {
        "detail": "Rate limit exceeded",
        "error_type": "RateLimitError",
    }


# ==================== Pytest Configuration ====================


def pytest_configure(config: Any) -> None:
    """Configure pytest with custom markers.

    Args:
        config: Pytest config object
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "asyncio: Async tests")
