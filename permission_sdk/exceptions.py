"""Exception hierarchy for the Permission SDK.

This module defines all custom exceptions that can be raised by the SDK.
All exceptions inherit from PermissionSDKError for easy catching.
"""


class PermissionSDKError(Exception):
    """Base exception for all SDK errors.

    All custom exceptions in this SDK inherit from this base class,
    allowing users to catch all SDK-specific errors with a single except clause.

    Example:
        >>> try:
        ...     client.check_permission(...)
        ... except PermissionSDKError as e:
        ...     print(f"SDK error occurred: {e}")
    """


class ConfigurationError(PermissionSDKError):
    """Invalid configuration error.

    Raised when the SDK is configured incorrectly, such as:
    - Missing required configuration (API key, base URL)
    - Invalid configuration values (negative timeout, invalid URL format)
    - Conflicting configuration options

    Example:
        >>> config = SDKConfig(base_url="", api_key="")
        ... # Raises: ConfigurationError("base_url is required")
    """


class AuthenticationError(PermissionSDKError):
    """Authentication failed error.

    Raised when the API key is missing, invalid, or expired (HTTP 401).

    Attributes:
        message: Error message describing the authentication failure
        status_code: HTTP status code (always 401)

    Example:
        >>> try:
        ...     client.check_permission(...)
        ... except AuthenticationError:
        ...     print("Invalid API key - please check your credentials")
    """

    def __init__(self, message: str, status_code: int = 401) -> None:
        """Initialize authentication error.

        Args:
            message: Error message
            status_code: HTTP status code (default: 401)
        """
        super().__init__(message)
        self.status_code = status_code


class ValidationError(PermissionSDKError):
    """Request validation failed error.

    Raised when the API rejects a request due to invalid input (HTTP 400).
    This includes malformed identifiers, invalid scopes, or missing required fields.

    Attributes:
        message: Error message describing what failed validation
        field: Optional field name that failed validation
        status_code: HTTP status code (always 400)

    Example:
        >>> try:
        ...     client.grant_permission(subject="invalid", scope="test", action="read")
        ... except ValidationError as e:
        ...     print(f"Validation failed for field '{e.field}': {e}")
    """

    def __init__(self, message: str, field: str | None = None, status_code: int = 400) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Optional field name that failed validation
            status_code: HTTP status code (default: 400)
        """
        super().__init__(message)
        self.field = field
        self.status_code = status_code


class ResourceNotFoundError(PermissionSDKError):
    """Resource not found error.

    Raised when a requested resource doesn't exist (HTTP 404).
    This includes subjects, scopes, or permission assignments that don't exist.

    Attributes:
        message: Error message describing what resource was not found
        resource_type: Type of resource (e.g., "subject", "scope", "permission")
        resource_id: Identifier of the resource that was not found

    Example:
        >>> try:
        ...     subject = client.get_subject("user:999")
        ... except ResourceNotFoundError as e:
        ...     print(f"{e.resource_type} not found: {e.resource_id}")
    """

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        status_code: int = 404,
    ) -> None:
        """Initialize resource not found error.

        Args:
            message: Error message
            resource_type: Type of resource (e.g., "subject", "scope")
            resource_id: Identifier of the missing resource
            status_code: HTTP status code (default: 404)
        """
        super().__init__(message)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.status_code = status_code


class ConflictError(PermissionSDKError):
    """Resource conflict error.

    Raised when a resource operation conflicts with existing state (HTTP 409).
    This includes scenarios like:
    - Attempting to create a limit with a different window type when one already exists
    - Other state conflicts that prevent the operation

    Attributes:
        message: Error message describing the conflict
        status_code: HTTP status code (always 409)
        response: Optional response data from the API

    Example:
        >>> try:
        ...     client.set_limit(
        ...         subject="user:123",
        ...         resource_type="project",
        ...         scope="projects",
        ...         limit_value=100,
        ...         window_type="monthly"
        ...     )
        ... except ConflictError as e:
        ...     print(f"Conflict: {e}")
        ...     # "Active daily limit exists. Cannot create monthly limit."
    """

    def __init__(self, message: str, response: dict | None = None, status_code: int = 409) -> None:
        """Initialize conflict error.

        Args:
            message: Error message
            response: Optional response data from API
            status_code: HTTP status code (default: 409)
        """
        super().__init__(message)
        self.response = response
        self.status_code = status_code


class ServerError(PermissionSDKError):
    """Server error.

    Raised when the API returns a server error (HTTP 500-599).
    This indicates an issue with the Permission Service itself.

    Attributes:
        message: Error message from the server
        status_code: HTTP status code (5xx)

    Example:
        >>> try:
        ...     client.check_permission(...)
        ... except ServerError:
        ...     print("Permission service is experiencing issues")
    """

    def __init__(self, message: str, status_code: int = 500) -> None:
        """Initialize server error.

        Args:
            message: Error message
            status_code: HTTP status code (5xx)
        """
        super().__init__(message)
        self.status_code = status_code


class NetworkError(PermissionSDKError):
    """Network/connection error.

    Raised when a network-level error occurs, such as:
    - Connection refused
    - DNS resolution failure
    - Connection timeout
    - SSL/TLS errors

    Example:
        >>> try:
        ...     client.check_permission(...)
        ... except NetworkError:
        ...     print("Cannot connect to permission service")
    """


class RateLimitError(PermissionSDKError):
    """Rate limit exceeded error.

    Raised when too many requests are made and the rate limit is exceeded (HTTP 429).

    Attributes:
        message: Error message
        retry_after: Optional number of seconds to wait before retrying
        status_code: HTTP status code (always 429)

    Example:
        >>> try:
        ...     client.check_permission(...)
        ... except RateLimitError as e:
        ...     if e.retry_after:
        ...         print(f"Rate limited. Retry after {e.retry_after} seconds")
        ...         time.sleep(e.retry_after)
    """

    def __init__(
        self, message: str, retry_after: int | None = None, status_code: int = 429
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Optional seconds to wait before retrying
            status_code: HTTP status code (default: 429)
        """
        super().__init__(message)
        self.retry_after = retry_after
        self.status_code = status_code


class TimeoutError(PermissionSDKError):
    """Request timeout error.

    Raised when a request takes longer than the configured timeout period.

    Attributes:
        message: Error message
        timeout: Timeout value in seconds that was exceeded

    Example:
        >>> try:
        ...     client.check_permission(...)
        ... except TimeoutError as e:
        ...     print(f"Request timed out after {e.timeout} seconds")
    """

    def __init__(self, message: str, timeout: float) -> None:
        """Initialize timeout error.

        Args:
            message: Error message
            timeout: Timeout value that was exceeded (in seconds)
        """
        super().__init__(message)
        self.timeout = timeout
