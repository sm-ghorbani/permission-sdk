"""HTTP transport layer for the Permission SDK.

This module provides HTTP communication with retry logic and error handling.
"""

from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
)
from requests.exceptions import (
    RequestException,
    Timeout,
)
from urllib3.util.retry import Retry

from permission_sdk.config import SDKConfig
from permission_sdk.exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    TimeoutError,
    ValidationError,
)


class HTTPTransport:
    """HTTP transport layer with automatic retry logic.

    This class handles all HTTP communication with the Permission Service API,
    including:
    - Request/response serialization
    - Authentication header management
    - Automatic retries with exponential backoff
    - Connection pooling
    - Error handling and exception mapping

    Attributes:
        config: SDK configuration
        session: Requests session with connection pooling

    Example:
        >>> config = SDKConfig(base_url="https://api.example.com", api_key="key")
        >>> transport = HTTPTransport(config)
        >>> data = transport.request("GET", "/api/v1/subjects")
    """

    def __init__(self, config: SDKConfig) -> None:
        """Initialize HTTP transport.

        Args:
            config: SDK configuration

        Example:
            >>> transport = HTTPTransport(config)
        """
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create configured requests session with retry logic.

        Returns:
            Configured requests.Session instance

        Note:
            The session includes:
            - Authentication headers
            - Connection pooling
            - Retry configuration with exponential backoff
        """
        session = requests.Session()

        # Set authentication header
        session.headers.update(
            {
                "X-API-Key": self.config.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=list(self.config.retry_on_status),
            allowed_methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
            raise_on_status=False,  # We'll handle status codes manually
        )

        # Configure HTTP adapter with retry and pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_maxsize=self.config.pool_maxsize,
            pool_connections=self.config.pool_connections,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path (e.g., '/api/v1/permissions/check')
            json: Optional JSON request body
            params: Optional query parameters

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If authentication fails (401)
            ValidationError: If request validation fails (400)
            ResourceNotFoundError: If resource not found (404)
            RateLimitError: If rate limit exceeded (429)
            ServerError: If server error occurs (500-599)
            NetworkError: If network error occurs
            TimeoutError: If request times out

        Example:
            >>> data = transport.request(
            ...     "POST",
            ...     "/api/v1/permissions/grant",
            ...     json={"subject": "user:123", "scope": "docs", "action": "read"}
            ... )
        """
        url = urljoin(self.config.base_url, endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.config.timeout,
            )

            # Handle different status codes
            self._handle_response(response)

            # Return JSON response
            if response.status_code == 204:  # No content
                return {}

            return response.json()

        except Timeout as e:
            raise TimeoutError(
                f"Request timed out after {self.config.timeout} seconds",
                timeout=float(self.config.timeout),
            ) from e

        except RequestsConnectionError as e:
            raise NetworkError(f"Failed to connect to {self.config.base_url}: {e}") from e

        except RequestException as e:
            raise NetworkError(f"Network error occurred: {e}") from e

    def _handle_response(self, response: requests.Response) -> None:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Raises:
            AuthenticationError: For 401 status
            ValidationError: For 400 status
            ResourceNotFoundError: For 404 status
            RateLimitError: For 429 status
            ServerError: For 500-599 status
        """
        # Success status codes
        if 200 <= response.status_code < 300:
            return

        # Try to extract error details from response
        try:
            error_data = response.json()
            error_message = error_data.get("detail", response.text)
            error_type = error_data.get("error_type")
            error_field = error_data.get("field")
        except Exception:
            error_message = response.text or f"HTTP {response.status_code}"
            error_type = None
            error_field = None

        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(
                error_message or "Authentication failed - invalid API key",
                status_code=response.status_code,
            )

        if response.status_code == 400:
            raise ValidationError(
                error_message or "Request validation failed",
                field=error_field,
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise ResourceNotFoundError(
                error_message or "Resource not found",
                resource_type=error_type,
                status_code=response.status_code,
            )

        if response.status_code == 429:
            # Try to get retry-after header
            retry_after = response.headers.get("Retry-After")
            retry_after_seconds = int(retry_after) if retry_after else None

            raise RateLimitError(
                error_message or "Rate limit exceeded",
                retry_after=retry_after_seconds,
                status_code=response.status_code,
            )

        if response.status_code >= 500:
            raise ServerError(
                error_message or "Internal server error",
                status_code=response.status_code,
            )

        # Fallback for any other error status codes
        raise ServerError(
            error_message or f"Unexpected error: HTTP {response.status_code}",
            status_code=response.status_code,
        )

    def close(self) -> None:
        """Close the HTTP session and cleanup connections.

        This should be called when the transport is no longer needed to
        properly cleanup connection pools.

        Example:
            >>> transport = HTTPTransport(config)
            >>> try:
            ...     # Use transport
            ...     pass
            ... finally:
            ...     transport.close()
        """
        self.session.close()

    def __enter__(self) -> "HTTPTransport":
        """Context manager entry.

        Returns:
            Self for use in with statement

        Example:
            >>> with HTTPTransport(config) as transport:
            ...     data = transport.request("GET", "/api/v1/permissions")
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - cleanup connections.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        self.close()
