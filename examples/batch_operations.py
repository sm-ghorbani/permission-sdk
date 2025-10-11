"""Batch operations optimization example for the Permission SDK.

This example demonstrates best practices for batch operations:
- Efficient bulk permission grants
- Batch permission checks
- Bulk revocations
- Performance optimization techniques
- Chunking large batches
"""

from permission_sdk import (
    CheckRequest,
    GrantRequest,
    PermissionClient,
    RevokeRequest,
    SDKConfig,
)
from permission_sdk.utils import chunk_list


def bulk_grant_permissions_example(client: PermissionClient) -> None:
    """Demonstrate efficient bulk permission grants.

    This is the recommended approach when granting many permissions at once.
    Batch operations are 10x faster than individual grants.
    """
    print("=== Bulk Grant Permissions ===\n")

    # Scenario: Grant read/write permissions to multiple users
    users = ["user:alice", "user:bob", "user:charlie", "user:diana"]
    scopes = ["documents.management", "reports.viewing", "analytics.dashboard"]
    actions = ["read", "write"]

    # Build grant requests for all combinations
    grants = []
    for user in users:
        for scope in scopes:
            for action in actions:
                grants.append(
                    GrantRequest(
                        subject=user,
                        scope=scope,
                        action=action,
                        tenant_id="org:acme",
                        metadata={"batch_id": "onboarding-2024", "source": "bulk_import"},
                    )
                )

    print(f"  Total permissions to grant: {len(grants)}")

    # Grant all permissions in a single batch
    result = client.grant_many(grants)
    print(f"  Successfully granted: {result.granted} permissions")
    print(f"  First assignment ID: {result.assignments[0].assignment_id}\n")


def chunked_batch_operations(client: PermissionClient) -> None:
    """Demonstrate chunking large batches for optimal performance.

    When dealing with thousands of permissions, it's better to chunk them
    into smaller batches to avoid timeouts and memory issues.
    """
    print("=== Chunked Batch Operations ===\n")

    # Simulate a large number of grants (e.g., from CSV import)
    large_grant_list = [
        GrantRequest(
            subject=f"user:{i}",
            scope="basic.access",
            action="read",
            tenant_id="org:acme",
        )
        for i in range(500)  # 500 permissions
    ]

    print(f"  Total permissions to grant: {len(large_grant_list)}")

    # Chunk into smaller batches (recommended: 100-200 per batch)
    chunk_size = 100
    chunks = chunk_list(large_grant_list, chunk_size)

    print(f"  Splitting into {len(chunks)} chunks of {chunk_size}\n")

    # Process each chunk
    total_granted = 0
    for idx, chunk in enumerate(chunks, 1):
        result = client.grant_many(chunk)
        total_granted += result.granted
        print(f"  Chunk {idx}/{len(chunks)}: Granted {result.granted} permissions")

    print(f"\n  Total granted: {total_granted} permissions\n")


def batch_permission_checks_for_ui(client: PermissionClient) -> None:
    """Demonstrate batch checks optimized for UI rendering.

    When rendering a UI with many permission-dependent elements,
    use batch checks to minimize API calls.
    """
    print("=== Batch Permission Checks for UI ===\n")

    # Scenario: Dashboard with multiple action buttons
    # We need to check if user can perform each action
    user_subjects = ["user:alice", "role:editor"]

    # Define all UI elements that need permission checks
    ui_elements = [
        ("create-doc-btn", "documents.management", "create"),
        ("edit-doc-btn", "documents.management", "edit"),
        ("delete-doc-btn", "documents.management", "delete"),
        ("view-reports-btn", "reports.viewing", "view"),
        ("export-reports-btn", "reports.viewing", "export"),
        ("manage-users-btn", "users.administration", "manage"),
        ("view-analytics-btn", "analytics.dashboard", "view"),
        ("edit-settings-btn", "settings.configuration", "edit"),
    ]

    # Create batch check requests
    checks = [
        CheckRequest(
            subjects=user_subjects,
            scope=scope,
            action=action,
            tenant_id="org:acme",
            check_id=check_id,
        )
        for check_id, scope, action in ui_elements
    ]

    print(f"  Checking {len(checks)} permissions in a single batch...\n")

    # Execute batch check
    results = client.check_many(checks)

    # Build permission map for UI
    permission_map = {result.check_id: result.allowed for result in results}

    # Display results
    print("  UI Element Permissions:")
    for check_id, scope, action in ui_elements:
        allowed = permission_map.get(check_id, False)
        status = "✓ Show" if allowed else "✗ Hide"
        print(f"    {check_id}: {status} ({scope}.{action})")
    print()


def bulk_revoke_permissions(client: PermissionClient) -> None:
    """Demonstrate bulk permission revocation.

    Useful for scenarios like:
    - User offboarding
    - Role changes
    - Access cleanup
    """
    print("=== Bulk Revoke Permissions ===\n")

    # Scenario: User leaving the organization - revoke all their permissions
    user = "user:charlie"
    scopes_to_revoke = [
        "documents.management",
        "reports.viewing",
        "analytics.dashboard",
    ]
    actions = ["read", "write", "delete", "view", "export"]

    # Build revocation requests
    revocations = []
    for scope in scopes_to_revoke:
        for action in actions:
            revocations.append(
                RevokeRequest(
                    subject=user,
                    scope=scope,
                    action=action,
                    tenant_id="org:acme",
                )
            )

    print(f"  Revoking {len(revocations)} permissions from {user}...")

    # Execute batch revocation
    revoked_count = client.revoke_many(revocations)
    print(f"  Successfully revoked: {revoked_count} permissions\n")


def role_based_bulk_grant(client: PermissionClient) -> None:
    """Demonstrate granting a role's permissions to a user.

    This is a common pattern for role-based access control (RBAC).
    """
    print("=== Role-Based Bulk Grant ===\n")

    # Define a role template with all its permissions
    editor_role_permissions = [
        ("documents.management", "read"),
        ("documents.management", "write"),
        ("documents.management", "edit"),
        ("reports.viewing", "view"),
        ("comments.moderation", "moderate"),
        ("media.library", "upload"),
        ("media.library", "view"),
    ]

    # User to receive the role
    new_editor = "user:eve"

    # Create grant requests for all role permissions
    grants = [
        GrantRequest(
            subject=new_editor,
            scope=scope,
            action=action,
            tenant_id="org:acme",
            metadata={
                "role": "editor",
                "granted_by": "admin:system",
                "reason": "New editor onboarding",
            },
        )
        for scope, action in editor_role_permissions
    ]

    print(f"  Granting 'editor' role ({len(grants)} permissions) to {new_editor}...")

    result = client.grant_many(grants)
    print(f"  Successfully granted: {result.granted} permissions")
    print("  Role: editor")
    print(f"  User: {new_editor}\n")


def performance_comparison(client: PermissionClient) -> None:
    """Demonstrate performance difference between individual and batch operations.

    This shows why batch operations are the recommended approach.
    """
    print("=== Performance Comparison ===\n")

    import time

    # Prepare test data
    test_grants = [
        GrantRequest(
            subject=f"user:perf-test-{i}",
            scope="test.scope",
            action="test",
            tenant_id="org:test",
        )
        for i in range(20)
    ]

    # Method 1: Individual grants (not recommended for multiple permissions)
    print("  Method 1: Individual grants (sequential)...")
    start = time.time()
    individual_count = 0
    for grant in test_grants[:5]:  # Only do 5 to avoid slow execution
        try:
            client.grant_permission(
                subject=grant.subject,
                scope=grant.scope,
                action=grant.action,
                tenant_id=grant.tenant_id,
            )
            individual_count += 1
        except Exception:
            pass
    individual_time = time.time() - start
    print(f"    Granted {individual_count} permissions in {individual_time:.2f}s")
    print(f"    Average: {individual_time/individual_count:.3f}s per permission\n")

    # Method 2: Batch grant (recommended)
    print("  Method 2: Batch grant (optimized)...")
    start = time.time()
    result = client.grant_many(test_grants)
    batch_time = time.time() - start
    print(f"    Granted {result.granted} permissions in {batch_time:.2f}s")
    print(f"    Average: {batch_time/result.granted:.3f}s per permission\n")

    if individual_count > 0:
        speedup = (individual_time / individual_count) / (batch_time / result.granted)
        print(f"  Speedup: {speedup:.1f}x faster with batch operations! 🚀\n")


def main() -> None:
    """Run all batch operation examples."""
    # Initialize configuration
    config = SDKConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key-here",
        timeout=60,  # Higher timeout for batch operations
    )

    with PermissionClient(config) as client:
        print("=== Permission SDK Batch Operations Examples ===\n")

        bulk_grant_permissions_example(client)
        chunked_batch_operations(client)
        batch_permission_checks_for_ui(client)
        bulk_revoke_permissions(client)
        role_based_bulk_grant(client)
        performance_comparison(client)

        print("=== All Batch Examples Complete ===")


if __name__ == "__main__":
    main()
