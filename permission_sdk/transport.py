"""HTTP transport layer for the Permission SDK.

This module provides HTTP communication with retry logic, error handling,
and optional caching with invalidation support.
"""

import asyncio
import logging
from typing import Any
from urllib.parse import urljoin

import httpx

from permission_sdk.cache.permission_cache import PermissionCacheManager
from permission_sdk.cache.provider import create_cache_service_async
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

logger = logging.getLogger(__name__)


class HTTPTransport:
    """HTTP transport layer with automatic retry logic and caching.

    This class handles all HTTP communication with the Permission Service API,
    including:
    - Request/response serialization
    - Authentication header management
    - Automatic retries with exponential backoff
    - Connection pooling
    - Error handling and exception mapping
    - Optional caching with automatic invalidation

    Attributes:
        config: SDK configuration
        client: HTTPX client with connection pooling
        cache_manager: Optional permission cache manager for caching

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
        self.client = self._create_client()
        self.cache_manager: PermissionCacheManager | None = None
        self._cache_initialized = False

    def _create_client(self) -> httpx.Client:
        """Create configured HTTP client with connection pooling.

        Returns:
            Configured httpx.Client instance

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

        # Create client with configuration
        client = httpx.Client(
            headers=headers,
            timeout=httpx.Timeout(self.config.timeout),
            limits=limits,
            follow_redirects=True,
        )

        return client

    def _ensure_cache_initialized(self) -> None:
        """Initialize cache if enabled and not yet initialized.

        Uses asyncio.run() to run async cache initialization in sync context.
        """
        if self._cache_initialized:
            return

        if self.config.cache_enabled:
            try:
                cache_service = asyncio.run(create_cache_service_async(self.config))
                self.cache_manager = PermissionCacheManager(
                    cache_service, self.config.cache_prefix
                )
                logger.debug("Cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}. Continuing without cache.")
                self.cache_manager = None

        self._cache_initialized = True

    def _is_check_request(self, method: str, endpoint: str) -> bool:
        """Check if this is a permission check request."""
        return method == "POST" and (
            "/permissions/check" in endpoint or "/permissions/check-many" in endpoint
        )

    def _is_grant_request(self, method: str, endpoint: str) -> bool:
        """Check if this is a grant request."""
        return method == "POST" and (
            "/permissions/grant" in endpoint or "/permissions/grant-many" in endpoint
        )

    def _is_revoke_request(self, method: str, endpoint: str) -> bool:
        """Check if this is a revoke request."""
        return method == "POST" and (
            "/permissions/revoke" in endpoint or "/permissions/revoke-many" in endpoint
        )

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
        # Initialize cache if enabled (lazy initialization)
        self._ensure_cache_initialized()

        # Route request based on type
        if self._is_check_request(method, endpoint):
            return self._handle_check_request(method, endpoint, json, params)
        elif self._is_grant_request(method, endpoint) or self._is_revoke_request(method, endpoint):
            return self._handle_mutation_request(method, endpoint, json, params)
        else:
            # Pass through for other requests
            return self._do_request(method, endpoint, json, params)

    def _handle_check_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None,
        params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Handle check permission request with caching."""
        # If cache not enabled or no data, pass through
        if not self.cache_manager or not json_data:
            return self._do_request(method, endpoint, json_data, params)

        # Handle single check
        if "/permissions/check-many" not in endpoint:
            subjects = json_data.get("subjects", [])
            scope = json_data.get("scope")
            action = json_data.get("action")
            tenant_id = json_data.get("tenant_id")
            object_id = json_data.get("object_id")

            # Try cache first (run async operation synchronously)
            try:
                cached_result = asyncio.run(
                    self.cache_manager.get_check_result(
                        subjects, scope, action, tenant_id, object_id
                    )
                )

                if cached_result is not None:
                    logger.debug(
                        f"Cache hit for check: {subjects} -> {scope}.{action}",
                        extra={"cache_hit": True},
                    )
                    return {"allowed": cached_result}
            except Exception as e:
                logger.warning(f"Cache get failed: {e}. Falling back to API call.")

        # Cache miss or batch check - call API
        result = self._do_request(method, endpoint, json_data, params)

        # Cache the result for single checks
        if "/permissions/check-many" not in endpoint and self.cache_manager:
            try:
                asyncio.run(
                    self.cache_manager.set_check_result(
                        subjects,
                        scope,
                        action,
                        result.get("allowed", False),
                        tenant_id,
                        object_id,
                        ttl=self.config.cache_ttl,
                    )
                )
                logger.debug(f"Cached check result for {subjects} -> {scope}.{action}")
            except Exception as e:
                logger.warning(f"Failed to cache check result: {e}")

        return result

    def _handle_mutation_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None,
        params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Handle grant/revoke request with cache invalidation."""
        # Call API first
        result = self._do_request(method, endpoint, json_data, params)

        # Invalidate cache if enabled
        if self.cache_manager and json_data:
            try:
                self._invalidate_cache_for_mutation(endpoint, json_data)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

        return result

    def _invalidate_cache_for_mutation(
        self, endpoint: str, json_data: dict[str, Any]
    ) -> None:
        """Invalidate cache entries affected by grant/revoke."""
        if not self.cache_manager:
            return

        # Handle batch operations
        if "/grant-many" in endpoint:
            grants = json_data.get("grants", [])
            subjects = list({g.get("subject") for g in grants if g.get("subject")})
            if subjects:
                invalidated = asyncio.run(
                    self.cache_manager.invalidate_subjects(subjects)
                )
                logger.debug(
                    f"Invalidated {invalidated} cache keys for batch grant ({len(subjects)} subjects)"
                )

        elif "/revoke-many" in endpoint:
            revocations = json_data.get("revocations", [])
            subjects = list({r.get("subject") for r in revocations if r.get("subject")})
            if subjects:
                invalidated = asyncio.run(
                    self.cache_manager.invalidate_subjects(subjects)
                )
                logger.debug(
                    f"Invalidated {invalidated} cache keys for batch revoke ({len(subjects)} subjects)"
                )

        # Handle single operations
        elif "/grant" in endpoint or "/revoke" in endpoint:
            subject = json_data.get("subject")
            if subject:
                invalidated = asyncio.run(
                    self.cache_manager.invalidate_subject(subject)
                )
                logger.debug(
                    f"Invalidated {invalidated} cache keys for subject: {subject}"
                )

    def _do_request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform the actual HTTP request with retry logic."""
        url = urljoin(self.config.base_url, endpoint)

        # Implement retry logic manually
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.request(
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
                self._wait_for_retry(attempt)

            except (httpx.ConnectError, httpx.NetworkError) as e:
                if attempt == self.config.max_retries:
                    raise NetworkError(
                        f"Failed to connect to {self.config.base_url}: {e}"
                    ) from e
                # Retry on network error
                self._wait_for_retry(attempt)

            except httpx.HTTPStatusError as e:
                # Check if status code is retryable
                if (
                    e.response.status_code in self.config.retry_on_status
                    and attempt < self.config.max_retries
                ):
                    self._wait_for_retry(attempt)
                    continue
                # Re-raise for non-retryable errors
                self._handle_response(e.response)

        # Should not reach here, but for type safety
        raise ServerError("Maximum retries exceeded")

    def _wait_for_retry(self, attempt: int) -> None:
        """Wait before retrying with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
        """
        import time

        wait_time = self.config.retry_backoff * (self.config.retry_multiplier**attempt)
        time.sleep(wait_time)

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

    def close(self) -> None:
        """Close the HTTP client and cleanup connections.

        This should be called when the transport is no longer needed to
        properly cleanup connection pools and cache connections.

        Example:
            >>> transport = HTTPTransport(config)
            >>> try:
            ...     # Use transport
            ...     pass
            ... finally:
            ...     transport.close()
        """
        self.client.close()

        # Close cache if initialized
        if self.cache_manager:
            try:
                asyncio.run(self.cache_manager.close())
            except Exception as e:
                logger.warning(f"Failed to close cache: {e}")

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
