"""Resource limit usage example for the Permission SDK.

This example demonstrates resource limit operations:
- Setting resource limits with different window types
- Checking if operations would exceed limits
- Incrementing usage after consuming resources
- Hierarchy checking (org + system limits)
- Getting current usage statistics
- Listing limits with filters
- Resetting usage (admin override)
"""

from datetime import datetime

from permission_sdk import (
    LimitFilter,
    PermissionClient,
    SDKConfig,
    SingleCheckLimitRequest,
)


def main() -> None:
    """Run resource limit SDK examples."""
    # Initialize configuration
    config = SDKConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key-here",
        timeout=30,
    )

    # Use context manager for automatic cleanup
    with PermissionClient(config) as client:
        print("=== Resource Limit SDK Usage Examples ===\n")

        # Example 1: Set a monthly project creation limit
        print("1. Setting a monthly project creation limit...")
        limit = client.set_limit(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            limit_value=10,
            window_type="monthly",
            tenant_id="org:acme",
            metadata={"plan": "premium", "set_by": "admin:1"},
        )
        print(f"   Set limit: {limit.limit_value} projects/month")
        print(f"   Window: {limit.window_start} to {limit.window_end}")
        print(f"   Current usage: {limit.current_usage}/{limit.limit_value}\n")

        # Example 2: Set additional limits for hierarchy
        print("2. Setting organization-wide and system-wide limits...")
        org_limit = client.set_limit(
            subject="org:acme",
            resource_type="project",
            scope="system",
            limit_value=100,
            window_type="monthly",
            metadata={"level": "organization"},
        )
        print(f"   Org limit: {org_limit.limit_value} projects/month")

        system_limit = client.set_limit(
            subject="system",
            resource_type="project",
            scope="global",
            limit_value=10000,
            window_type="monthly",
            metadata={"level": "system"},
        )
        print(f"   System limit: {system_limit.limit_value} projects/month\n")

        # Example 3: Check if user can create a project
        print("3. Checking if user can create 1 project...")
        check_result = client.check_limit(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            amount=1,
            tenant_id="org:acme",
        )
        print(f"   Allowed: {check_result.allowed}")
        print(f"   Current usage: {check_result.current_usage}")
        print(f"   Limit: {check_result.limit}")
        print(f"   Remaining: {check_result.remaining}")
        print(f"   Would exceed: {check_result.would_exceed}")
        print(f"   Window resets at: {check_result.resets_at}\n")

        # Example 4: Check multiple limits in hierarchy
        print("4. Checking hierarchy (user, org, and system limits)...")
        hierarchy_checks = [
            SingleCheckLimitRequest(
                subject="user:alice",
                resource_type="project",
                scope="organization:acme",
                amount=1,
                tenant_id="org:acme",
                check_id="user-limit",
            ),
            SingleCheckLimitRequest(
                subject="org:acme",
                resource_type="project",
                scope="system",
                amount=1,
                check_id="org-limit",
            ),
            SingleCheckLimitRequest(
                subject="system",
                resource_type="project",
                scope="global",
                amount=1,
                check_id="system-limit",
            ),
        ]
        hierarchy_result = client.check_many_limits(hierarchy_checks)
        print(f"   All limits allow operation: {hierarchy_result.all_allowed}")
        for check in hierarchy_result.checks:
            status = "✓" if check.allowed else "✗"
            print(
                f"   {status} {check.check_id}: "
                f"{check.current_usage}/{check.limit} "
                f"(remaining: {check.remaining})"
            )
        print()

        # Example 5: Increment usage after creating a project
        print("5. Incrementing usage after creating a project...")
        increment_result = client.increment_usage(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            amount=1,
            tenant_id="org:acme",
            metadata={"project_id": "proj:123", "action": "created"},
        )
        print(f"   Previous usage: {increment_result.previous_usage}")
        print(f"   New usage: {increment_result.new_usage}")
        print(f"   Limit: {increment_result.limit}")
        print(f"   Remaining: {increment_result.remaining}")
        print(f"   At limit: {increment_result.at_limit}\n")

        # Example 6: Get current usage statistics
        print("6. Getting current usage statistics...")
        usage = client.get_usage(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            tenant_id="org:acme",
        )
        print(f"   Resource: {usage.resource_type}")
        print(f"   Current usage: {usage.current_usage}")
        print(f"   Limit: {usage.limit}")
        print(f"   Remaining: {usage.remaining}")
        print(f"   Window: {usage.window_type}")
        print(f"   Resets at: {usage.resets_at}")
        if usage.metadata:
            print(f"   Metadata: {usage.metadata}")
        print()

        # Example 7: Check if bulk operation would exceed limit
        print("7. Checking if creating 5 projects would exceed limit...")
        bulk_check = client.check_limit(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            amount=5,
            tenant_id="org:acme",
        )
        if bulk_check.would_exceed:
            print(
                f"   ✗ Would exceed limit! "
                f"(Trying to use {bulk_check.amount}, but only {bulk_check.remaining} remaining)"
            )
        else:
            print(
                f"   ✓ Operation allowed "
                f"({bulk_check.remaining} remaining after operation)"
            )
        print()

        # Example 8: List all limits for a subject
        print("8. Listing all limits for user:alice...")
        limit_filters = LimitFilter(
            subject="user:alice",
            tenant_id="org:acme",
            limit=10,
        )
        limits_response = client.list_limits(limit_filters)
        print(f"   Total limits: {limits_response.total}")
        for lim in limits_response.items:
            percentage = (
                (lim.current_usage / lim.limit_value * 100) if lim.limit_value > 0 else 0
            )
            print(
                f"   - {lim.resource_type} @ {lim.scope}: "
                f"{lim.current_usage}/{lim.limit_value} "
                f"({percentage:.1f}% used, {lim.window_type})"
            )
        print()

        # Example 9: List limits by resource type
        print("9. Listing all project limits across subjects...")
        resource_filters = LimitFilter(
            resource_type="project",
            limit=10,
        )
        projects_response = client.list_limits(resource_filters)
        print(f"   Total project limits: {projects_response.total}")
        for lim in projects_response.items:
            print(
                f"   - {lim.subject} @ {lim.scope}: "
                f"{lim.current_usage}/{lim.limit_value}"
            )
        print()

        # Example 10: Reset usage (admin override)
        print("10. Resetting usage for a limit...")
        reset_result = client.reset_usage(
            subject="user:alice",
            resource_type="project",
            scope="organization:acme",
            tenant_id="org:acme",
            metadata={"reason": "billing cycle reset", "admin": "admin:1"},
        )
        print(f"   Previous usage: {reset_result.previous_usage}")
        print(f"   New usage: {reset_result.new_usage}")
        print(f"   Reset successful: {reset_result.new_usage == 0}\n")

        # Example 11: Set different window types
        print("11. Setting limits with different window types...")

        # Hourly limit for API calls
        hourly = client.set_limit(
            subject="user:alice",
            resource_type="api_call",
            scope="service:analytics",
            limit_value=1000,
            window_type="hourly",
            tenant_id="org:acme",
        )
        print(f"   Hourly API limit: {hourly.limit_value}/hour")

        # Daily limit for file uploads
        daily = client.set_limit(
            subject="user:alice",
            resource_type="file_upload",
            scope="service:storage",
            limit_value=100,
            window_type="daily",
            tenant_id="org:acme",
        )
        print(f"   Daily upload limit: {daily.limit_value}/day")

        # Total (non-resetting) limit for team members
        total = client.set_limit(
            subject="org:acme",
            resource_type="team_member",
            scope="system",
            limit_value=50,
            window_type="total",
            metadata={"plan": "enterprise"},
        )
        print(f"   Total team limit: {total.limit_value} (never resets)\n")

        # Example 12: Handle limit exceeded scenario
        print("12. Demonstrating limit exceeded scenario...")

        # Set a low limit for testing
        test_limit = client.set_limit(
            subject="user:bob",
            resource_type="export",
            scope="service:reports",
            limit_value=3,
            window_type="daily",
            tenant_id="org:acme",
        )
        print(f"   Set daily export limit: {test_limit.limit_value}")

        # Use up the limit
        for i in range(3):
            client.increment_usage(
                subject="user:bob",
                resource_type="export",
                scope="service:reports",
                amount=1,
                tenant_id="org:acme",
            )
        print(f"   Consumed all {test_limit.limit_value} exports")

        # Try to check if one more is allowed
        exceeded_check = client.check_limit(
            subject="user:bob",
            resource_type="export",
            scope="service:reports",
            amount=1,
            tenant_id="org:acme",
        )
        if not exceeded_check.allowed:
            print(
                f"   ✗ Limit exceeded! "
                f"Usage: {exceeded_check.current_usage}/{exceeded_check.limit}"
            )
            print(
                f"   Limit resets at: {exceeded_check.resets_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        print()

        # Example 13: Pagination for large result sets
        print("13. Handling pagination for limits...")
        page_filters = LimitFilter(limit=5, offset=0)
        first_page = client.list_limits(page_filters)
        print(f"   Page 1: {len(first_page.items)} items")
        print(f"   Total available: {first_page.total}")
        print(f"   Has more pages: {first_page.has_more}")
        if first_page.has_more:
            print(f"   Next offset: {first_page.next_offset}")
        print()

        print("=== Examples Complete ===")


if __name__ == "__main__":
    main()
