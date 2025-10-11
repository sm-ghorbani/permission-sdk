"""Async usage example for the Permission SDK.

This example demonstrates how to use the async client for concurrent operations:
- Using AsyncPermissionClient with async/await
- Concurrent permission checks
- Batch operations with asyncio
- Async context managers
"""

import asyncio

from permission_sdk import (
    AsyncPermissionClient,
    CheckRequest,
    GrantRequest,
    PermissionFilter,
    SDKConfig,
)


async def concurrent_checks_example(client: AsyncPermissionClient) -> None:
    """Demonstrate concurrent permission checks.

    This shows how to check multiple permissions simultaneously using asyncio.gather,
    which is much faster than sequential checks.
    """
    print("=== Concurrent Permission Checks ===\n")

    # Create multiple check tasks
    check_tasks = [
        client.check_permission(
            subjects=["user:alice"],
            scope="documents.management",
            action="read",
        ),
        client.check_permission(
            subjects=["user:alice"],
            scope="documents.management",
            action="write",
        ),
        client.check_permission(
            subjects=["user:alice"],
            scope="reports.viewing",
            action="view",
        ),
        client.check_permission(
            subjects=["user:alice"],
            scope="admin.settings",
            action="manage",
        ),
    ]

    # Run all checks concurrently
    results = await asyncio.gather(*check_tasks)

    # Display results
    permissions = ["read docs", "write docs", "view reports", "manage admin"]
    for perm, allowed in zip(permissions, results, strict=True):
        status = "✓ Allowed" if allowed else "✗ Denied"
        print(f"  {perm}: {status}")
    print()


async def batch_operations_example(client: AsyncPermissionClient) -> None:
    """Demonstrate batch grant and check operations.

    This shows how to efficiently grant multiple permissions at once
    and then verify them with a batch check.
    """
    print("=== Batch Grant Operations ===\n")

    # Batch grant permissions
    grants = [
        GrantRequest(
            subject="user:bob",
            scope="documents.management",
            action="read",
            tenant_id="org:acme",
        ),
        GrantRequest(
            subject="user:bob",
            scope="documents.management",
            action="write",
            tenant_id="org:acme",
        ),
        GrantRequest(
            subject="user:bob",
            scope="reports.viewing",
            action="view",
            tenant_id="org:acme",
        ),
    ]

    result = await client.grant_many(grants)
    print(f"  Granted {result.granted} permissions to user:bob\n")

    # Batch check the granted permissions
    print("=== Batch Permission Checks ===\n")

    checks = [
        CheckRequest(
            subjects=["user:bob"],
            scope="documents.management",
            action="read",
            tenant_id="org:acme",
            check_id="check-1",
        ),
        CheckRequest(
            subjects=["user:bob"],
            scope="documents.management",
            action="write",
            tenant_id="org:acme",
            check_id="check-2",
        ),
        CheckRequest(
            subjects=["user:bob"],
            scope="reports.viewing",
            action="view",
            tenant_id="org:acme",
            check_id="check-3",
        ),
    ]

    check_results = await client.check_many(checks)
    for check_result in check_results:
        status = "✓ Allowed" if check_result.allowed else "✗ Denied"
        print(f"  {check_result.check_id}: {status}")
    print()


async def concurrent_crud_operations(client: AsyncPermissionClient) -> None:
    """Demonstrate concurrent CRUD operations.

    This shows how to create subjects and scopes in parallel,
    which significantly speeds up bulk operations.
    """
    print("=== Concurrent CRUD Operations ===\n")

    # Create multiple subjects concurrently
    subject_tasks = [
        client.create_subject(
            identifier="user:charlie",
            display_name="Charlie Brown",
            tenant_id="org:acme",
            metadata={"email": "charlie@acme.com"},
        ),
        client.create_subject(
            identifier="user:diana",
            display_name="Diana Prince",
            tenant_id="org:acme",
            metadata={"email": "diana@acme.com"},
        ),
        client.create_subject(
            identifier="role:editor",
            display_name="Editor Role",
            tenant_id="org:acme",
        ),
    ]

    # Create multiple scopes concurrently
    scope_tasks = [
        client.create_scope(
            identifier="articles.editing",
            display_name="Article Editing",
            description="Permissions for editing articles",
        ),
        client.create_scope(
            identifier="comments.moderation",
            display_name="Comment Moderation",
            description="Permissions for moderating comments",
        ),
    ]

    # Wait for all operations to complete
    subjects, scopes = await asyncio.gather(
        asyncio.gather(*subject_tasks),
        asyncio.gather(*scope_tasks),
    )

    print(f"  Created {len(subjects)} subjects concurrently:")
    for subject in subjects:
        print(f"    - {subject.identifier}: {subject.display_name}")

    print(f"\n  Created {len(scopes)} scopes concurrently:")
    for scope in scopes:
        print(f"    - {scope.identifier}: {scope.display_name}")
    print()


async def pagination_example(client: AsyncPermissionClient) -> None:
    """Demonstrate async pagination through results.

    This shows how to efficiently page through large result sets
    using async/await.
    """
    print("=== Async Pagination Example ===\n")

    filters = PermissionFilter(
        tenant_id="org:acme",
        limit=5,  # Small page size for demonstration
    )

    page_num = 1
    response = await client.list_permissions(filters)

    print(f"  Page {page_num}: {len(response.items)} items")
    print(f"  Total permissions: {response.total}")

    # Page through all results
    while response.has_more:
        page_num += 1
        filters.offset = response.next_offset or 0
        response = await client.list_permissions(filters)
        print(f"  Page {page_num}: {len(response.items)} items")

    print(f"\n  Total pages: {page_num}\n")


async def main() -> None:
    """Run all async examples."""
    # Initialize configuration
    config = SDKConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key-here",
        timeout=30,
    )

    # Use async context manager for automatic cleanup
    async with AsyncPermissionClient(config) as client:
        print("=== Permission SDK Async Usage Examples ===\n")

        # Run examples sequentially (each contains concurrent operations)
        await concurrent_checks_example(client)
        await batch_operations_example(client)
        await concurrent_crud_operations(client)
        await pagination_example(client)

        print("=== All Async Examples Complete ===")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
