"""Error handling example for the Permission SDK.

This example demonstrates best practices for error handling:
- Catching specific exceptions
- Handling validation errors
- Dealing with network failures
- Retry strategies
- Graceful degradation
"""

import time

from permission_sdk import (
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    PermissionClient,
    RateLimitError,
    ResourceNotFoundError,
    SDKConfig,
    ServerError,
    TimeoutError,
    ValidationError,
)


def handle_authentication_errors() -> None:
    """Demonstrate handling authentication errors.

    This shows what happens when API key is invalid or missing.
    """
    print("=== Authentication Error Handling ===\n")

    try:
        # Try with invalid API key
        config = SDKConfig(
            base_url="http://localhost:8000",
            api_key="invalid-key-12345",
        )

        with PermissionClient(config) as client:
            client.check_permission(
                subjects=["user:alice"],
                scope="documents.management",
                action="read",
            )

    except AuthenticationError as e:
        print(f"  ✗ Authentication failed: {e}")
        print(f"    Status code: {e.status_code}")
        print("    Action: Check your API key in configuration\n")


def handle_validation_errors(client: PermissionClient) -> None:
    """Demonstrate handling validation errors.

    This shows how to catch and handle invalid request parameters.
    """
    print("=== Validation Error Handling ===\n")

    # Example 1: Invalid subject identifier format
    try:
        client.grant_permission(
            subject="invalid-subject",  # Missing 'type:' prefix
            scope="documents.management",
            action="read",
        )
    except ValidationError as e:
        print(f"  ✗ Validation error: {e}")
        print(f"    Field: {e.field}")
        print("    Fix: Use format 'type:id' (e.g., 'user:alice')\n")

    # Example 2: Invalid action format (uppercase)
    try:
        client.grant_permission(
            subject="user:alice",
            scope="documents.management",
            action="READ",  # Should be lowercase
        )
    except ValidationError as e:
        print(f"  ✗ Validation error: {e}")
        print(f"    Field: {e.field}")
        print("    Fix: Actions must be lowercase\n")


def handle_resource_not_found(client: PermissionClient) -> None:
    """Demonstrate handling resource not found errors.

    This shows how to handle missing resources gracefully.
    """
    print("=== Resource Not Found Handling ===\n")

    try:
        # Try to get a non-existent subject
        subject = client.get_subject("user:nonexistent")
        print(f"  Subject found: {subject.identifier}")

    except ResourceNotFoundError as e:
        print(f"  ✗ Resource not found: {e}")
        print(f"    Resource type: {e.resource_type}")
        print("    Action: Create the resource first or check the identifier\n")


def handle_rate_limiting(client: PermissionClient) -> None:
    """Demonstrate handling rate limit errors.

    This shows how to handle and recover from rate limiting.
    """
    print("=== Rate Limit Handling ===\n")

    try:
        # Simulate rapid requests that might trigger rate limiting
        for _ in range(100):
            client.check_permission(
                subjects=["user:alice"],
                scope="test.scope",
                action="test",
            )

    except RateLimitError as e:
        print(f"  ✗ Rate limit exceeded: {e}")
        print(f"    Status code: {e.status_code}")

        if e.retry_after:
            print(f"    Retry after: {e.retry_after} seconds")
            print(f"    Waiting {e.retry_after} seconds before retry...")
            time.sleep(e.retry_after)
            print("    Retry successful!\n")
        else:
            print("    Action: Implement exponential backoff\n")


def handle_network_errors() -> None:
    """Demonstrate handling network errors.

    This shows how to handle connection failures and timeouts.
    """
    print("=== Network Error Handling ===\n")

    # Example 1: Connection error (wrong URL)
    try:
        config = SDKConfig(
            base_url="http://non-existent-host.local",
            api_key="test-key",
            timeout=5,
            max_retries=1,  # Fail faster for demo
        )

        with PermissionClient(config) as client:
            client.check_permission(
                subjects=["user:alice"],
                scope="test",
                action="test",
            )

    except NetworkError as e:
        print(f"  ✗ Network error: {e}")
        print("    Action: Check network connection and service URL\n")

    # Example 2: Timeout error
    try:
        config = SDKConfig(
            base_url="http://localhost:8000",
            api_key="test-key",
            timeout=1,  # Unreasonably short timeout
            max_retries=0,
        )

        with PermissionClient(config) as client:
            client.check_permission(
                subjects=["user:alice"],
                scope="test",
                action="test",
            )

    except TimeoutError as e:
        print(f"  ✗ Timeout error: {e}")
        print(f"    Timeout: {e.timeout}s")
        print("    Action: Increase timeout or check service performance\n")


def handle_server_errors(client: PermissionClient) -> None:
    """Demonstrate handling server errors.

    This shows how to handle 500-series errors from the API.
    """
    print("=== Server Error Handling ===\n")

    try:
        # This might trigger a server error in certain conditions
        client.grant_permission(
            subject="user:test",
            scope="test.scope",
            action="test",
        )

    except ServerError as e:
        print(f"  ✗ Server error: {e}")
        print(f"    Status code: {e.status_code}")
        print("    Action: Retry with exponential backoff")
        print("    If persists: Contact API support\n")


def graceful_degradation_pattern(client: PermissionClient) -> None:
    """Demonstrate graceful degradation pattern.

    This shows how to provide fallback behavior when permissions can't be checked.
    """
    print("=== Graceful Degradation Pattern ===\n")

    def check_permission_with_fallback(
        subject: str,
        scope: str,
        action: str,
        fallback: bool = False,
    ) -> bool:
        """Check permission with fallback on error."""
        try:
            return client.check_permission(
                subjects=[subject],
                scope=scope,
                action=action,
            )
        except (NetworkError, TimeoutError, ServerError) as e:
            print(f"  ⚠ Permission check failed: {type(e).__name__}")
            print(f"    Using fallback: {'Allow' if fallback else 'Deny'}")
            return fallback
        except AuthenticationError:
            # Auth errors should not use fallback - they indicate misconfiguration
            print("  ✗ Authentication error - failing securely")
            return False

    # Scenario 1: Fail-safe (deny by default)
    print("  Scenario 1: Fail-safe (deny by default)")
    allowed = check_permission_with_fallback(
        "user:alice",
        "sensitive.data",
        "access",
        fallback=False,  # Deny on error
    )
    print(f"  Result: {'Allowed' if allowed else 'Denied'}\n")

    # Scenario 2: Fail-open (allow by default - use with caution!)
    print("  Scenario 2: Fail-open (allow by default)")
    allowed = check_permission_with_fallback(
        "user:alice",
        "public.content",
        "view",
        fallback=True,  # Allow on error (for public content only!)
    )
    print(f"  Result: {'Allowed' if allowed else 'Denied'}\n")


def comprehensive_error_handling(client: PermissionClient) -> None:
    """Demonstrate comprehensive error handling strategy.

    This shows a production-ready error handling approach.
    """
    print("=== Comprehensive Error Handling ===\n")

    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def perform_permission_operation(operation_name: str) -> bool:
        """Perform operation with comprehensive error handling."""
        try:
            # Example operation
            result = client.check_permission(
                subjects=["user:alice"],
                scope="documents.management",
                action="read",
            )
            logger.info(f"{operation_name}: Success - {result}")
            return True

        except ValidationError as e:
            logger.error(f"{operation_name}: Validation error - {e.field}: {e}")
            # Validation errors indicate client-side bugs - should be fixed
            return False

        except AuthenticationError as e:
            logger.critical(f"{operation_name}: Authentication failed - {e}")
            # Auth errors need immediate attention - configuration issue
            raise  # Re-raise to alert ops team

        except ResourceNotFoundError as e:
            logger.warning(f"{operation_name}: Resource not found - {e}")
            # Resource errors might be expected - handle gracefully
            return False

        except RateLimitError as e:
            logger.warning(f"{operation_name}: Rate limited - retry after {e.retry_after}s")
            # Implement retry with backoff
            if e.retry_after:
                time.sleep(e.retry_after)
                return perform_permission_operation(operation_name)  # Retry once
            return False

        except TimeoutError as e:
            logger.error(f"{operation_name}: Timeout after {e.timeout}s")
            # Timeouts might be transient - consider retry
            return False

        except (NetworkError, ServerError) as e:
            logger.error(f"{operation_name}: {type(e).__name__} - {e}")
            # Network/server errors might be transient - consider retry
            return False

        except Exception as e:
            logger.exception(f"{operation_name}: Unexpected error - {e}")
            # Catch-all for unexpected errors
            return False

    # Execute operation with comprehensive error handling
    success = perform_permission_operation("Permission Check")
    print(f"  Operation {'succeeded' if success else 'failed'}\n")


def configuration_validation() -> None:
    """Demonstrate configuration validation errors.

    This shows how to handle configuration errors at initialization.
    """
    print("=== Configuration Validation ===\n")

    # Example 1: Missing API key
    try:
        _ = SDKConfig(
            base_url="http://localhost:8000",
            api_key="",  # Empty API key
        )
    except ConfigurationError as e:
        print(f"  ✗ Configuration error: {e}")
        print("    Fix: Provide a valid API key\n")

    # Example 2: Invalid URL
    try:
        _ = SDKConfig(
            base_url="not-a-valid-url",  # Missing http://
            api_key="test-key",
        )
    except ConfigurationError as e:
        print(f"  ✗ Configuration error: {e}")
        print("    Fix: URL must start with http:// or https://\n")

    # Example 3: Invalid timeout
    try:
        _ = SDKConfig(
            base_url="http://localhost:8000",
            api_key="test-key",
            timeout=-1,  # Negative timeout
        )
    except ConfigurationError as e:
        print(f"  ✗ Configuration error: {e}")
        print("    Fix: Timeout must be positive\n")


def main() -> None:
    """Run all error handling examples."""
    print("=== Permission SDK Error Handling Examples ===\n")

    # Configuration validation (no client needed)
    configuration_validation()

    # Authentication errors (creates own client with bad config)
    handle_authentication_errors()

    # Network errors (creates own client with bad config)
    handle_network_errors()

    # For other examples, use a properly configured client
    config = SDKConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key-here",
        timeout=30,
    )

    try:
        with PermissionClient(config) as client:
            handle_validation_errors(client)
            handle_resource_not_found(client)
            # handle_rate_limiting(client)  # Uncomment to test (might take time)
            handle_server_errors(client)
            graceful_degradation_pattern(client)
            comprehensive_error_handling(client)

    except AuthenticationError:
        print("\n⚠ Note: Some examples require a running Permission Service")
        print("  with valid authentication.\n")

    print("=== All Error Handling Examples Complete ===")


if __name__ == "__main__":
    main()
