"""Async HTTP transport layer for the Permission SDK.

This module provides asynchronous HTTP communication with retry logic and error handling.
"""

from typing import Any
from urllib.parse import urljoin

import httpx

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


class AsyncHTTPTransport:
    """Async HTTP transport layer with automatic retry logic.

    This class handles all asynchronous HTTP communication with the Permission
    Service API, including:
    - Request/response serialization
    - Authentication header management
    - Automatic retries with exponential backoff
    - Connection pooling
    - Error handling and exception mapping

    Attributes:
        config: SDK configuration
        client: HTTPX async client with connection pooling

    Example:
        >>> config = SDKConfig(base_url="https://api.example.com", api_key="key")
        >>> async with AsyncHTTPTransport(config) as transport:
        ...     data = await transport.request("GET", "/api/v1/subjects")
    """

    def __init__(self, config: SDKConfig) -> None:
        """Initialize async HTTP transport.

        Args:
            config: SDK configuration

        Example:
            >>> transport = AsyncHTTPTransport(config)
        """
        self.config = config
        self.client = self._create_client()

    def _create_client(self) -> httpx.AsyncClient:
        """Create configured async HTTP client with retry logic.

        Returns:
            Configured httpx.AsyncClient instance

        Note:
            The client includes:
            - Authentication headers
            - Connection pooling
            - Timeout configuration
        """
        headers = {
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Configure connection limits for pooling
        limits = httpx.Limits(
            max_keepalive_connections=self.config.pool_connections,
            max_connections=self.config.pool_maxsize,
        )

        # Create async client with configuration
        client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(self.config.timeout),
            limits=limits,
            follow_redirects=True,
        )

        return client

    async def request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make async HTTP request with error handling.

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
            >>> data = await transport.request(
            ...     "POST",
            ...     "/api/v1/permissions/grant",
            ...     json={"subject": "user:123", "scope": "docs", "action": "read"}
            ... )
        """
        url = urljoin(self.config.base_url, endpoint)

        # Implement retry logic manually since httpx doesn't have built-in retry
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                )

                # Handle different status codes
                self._handle_response(response)

                # Return JSON response
                if response.status_code == 204:  # No content
                    return {}

                return response.json()

            except httpx.TimeoutException as e:
                if attempt == self.config.max_retries:
                    raise TimeoutError(
                        f"Request timed out after {self.config.timeout} seconds",
                        timeout=float(self.config.timeout),
                    ) from e
                # Retry on timeout
                await self._wait_for_retry(attempt)

            except (httpx.ConnectError, httpx.NetworkError) as e:
                if attempt == self.config.max_retries:
                    raise NetworkError(
                        f"Failed to connect to {self.config.base_url}: {e}"
                    ) from e
                # Retry on network error
                await self._wait_for_retry(attempt)

            except httpx.HTTPStatusError as e:
                # Check if status code is retryable
                if (
                    e.response.status_code in self.config.retry_on_status
                    and attempt < self.config.max_retries
                ):
                    await self._wait_for_retry(attempt)
                    continue
                # Re-raise for non-retryable errors
                self._handle_response(e.response)

        # Should not reach here, but for type safety
        raise ServerError("Maximum retries exceeded")

    async def _wait_for_retry(self, attempt: int) -> None:
        """Wait before retrying with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
        """
        import asyncio

        wait_time = (
            self.config.retry_backoff * (self.config.retry_multiplier**attempt)
        )
        await asyncio.sleep(wait_time)

    def _handle_response(self, response: httpx.Response) -> None:
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

    async def close(self) -> None:
        """Close the async HTTP client and cleanup connections.

        This should be called when the transport is no longer needed to
        properly cleanup connection pools.

        Example:
            >>> transport = AsyncHTTPTransport(config)
            >>> try:
            ...     # Use transport
            ...     pass
            ... finally:
            ...     await transport.close()
        """
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncHTTPTransport":
        """Async context manager entry.

        Returns:
            Self for use in async with statement

        Example:
            >>> async with AsyncHTTPTransport(config) as transport:
            ...     data = await transport.request("GET", "/api/v1/permissions")
        """
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - cleanup connections.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        await self.close()
