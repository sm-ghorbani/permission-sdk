"""Unit tests for SDK exceptions.

This module tests the custom exception classes.
"""

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


class TestExceptionHierarchy:
    """Tests for exception class hierarchy."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test that all exceptions inherit from PermissionSDKError."""
        exceptions = [
            ConfigurationError,
            AuthenticationError,
            ValidationError,
            ResourceNotFoundError,
            ServerError,
            NetworkError,
            RateLimitError,
            TimeoutError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, PermissionSDKError)
            assert issubclass(exc_class, Exception)


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_basic(self) -> None:
        """Test basic validation error."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert error.field is None

    def test_validation_error_with_field(self) -> None:
        """Test validation error with field."""
        error = ValidationError("Invalid subject format", field="subject")
        assert str(error) == "Invalid subject format"
        assert error.field == "subject"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_authentication_error(self) -> None:
        """Test authentication error."""
        error = AuthenticationError("Invalid API key")
        assert str(error) == "Invalid API key"


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError."""

    def test_resource_not_found_basic(self) -> None:
        """Test basic resource not found error."""
        error = ResourceNotFoundError("Subject not found")
        assert str(error) == "Subject not found"
        assert error.resource_type is None

    def test_resource_not_found_with_type(self) -> None:
        """Test resource not found with resource type."""
        error = ResourceNotFoundError("Not found", resource_type="Subject")
        assert str(error) == "Not found"
        assert error.resource_type == "Subject"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_rate_limit_basic(self) -> None:
        """Test basic rate limit error."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after is None

    def test_rate_limit_with_retry_after(self) -> None:
        """Test rate limit error with retry_after."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60


class TestTimeoutError:
    """Tests for TimeoutError."""

    def test_timeout_error_basic(self) -> None:
        """Test basic timeout error."""
        error = TimeoutError("Request timed out")
        assert str(error) == "Request timed out"
        assert error.timeout is None

    def test_timeout_error_with_timeout(self) -> None:
        """Test timeout error with timeout value."""
        error = TimeoutError("Request timed out", timeout=30.0)
        assert str(error) == "Request timed out"
        assert error.timeout == 30.0


class TestNetworkError:
    """Tests for NetworkError."""

    def test_network_error(self) -> None:
        """Test network error."""
        error = NetworkError("Connection failed")
        assert str(error) == "Connection failed"


class TestServerError:
    """Tests for ServerError."""

    def test_server_error(self) -> None:
        """Test server error."""
        error = ServerError("Internal server error")
        assert str(error) == "Internal server error"


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error(self) -> None:
        """Test configuration error."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
