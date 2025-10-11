"""Basic usage example for the Permission SDK.

This example demonstrates the most common operations:
- Configuring the client
- Granting permissions
- Checking permissions
- Listing permissions
- Managing subjects and scopes
"""

from permission_sdk import (
    CheckRequest,
    GrantRequest,
    PermissionClient,
    PermissionFilter,
    ScopeFilter,
    SDKConfig,
    SubjectFilter,
)


def main() -> None:
    """Run basic SDK examples."""
    # Initialize configuration
    config = SDKConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key-here",
        timeout=30,
    )

    # Use context manager for automatic cleanup
    with PermissionClient(config) as client:
        print("=== Permission SDK Basic Usage Examples ===\n")

        # Example 1: Create subjects and scopes
        print("1. Creating subjects and scopes...")
        subject = client.create_subject(
            identifier="user:alice",
            display_name="Alice Smith",
            tenant_id="org:acme",
            metadata={"email": "alice@acme.com", "department": "Engineering"},
        )
        print(f"   Created subject: {subject.identifier}")

        scope = client.create_scope(
            identifier="documents.management",
            display_name="Document Management",
            description="Permissions for managing documents",
            metadata={"category": "content"},
        )
        print(f"   Created scope: {scope.identifier}\n")

        # Example 2: Grant a single permission
        print("2. Granting a single permission...")
        assignment = client.grant_permission(
            subject="user:alice",
            scope="documents.management",
            action="read",
            tenant_id="org:acme",
            metadata={"granted_by": "admin:1", "reason": "Initial access"},
        )
        print(f"   Granted permission: {assignment.assignment_id}\n")

        # Example 3: Grant multiple permissions in batch
        print("3. Granting multiple permissions in batch...")
        grants = [
            GrantRequest(
                subject="user:alice",
                scope="documents.management",
                action="write",
                tenant_id="org:acme",
            ),
            GrantRequest(
                subject="user:alice",
                scope="documents.management",
                action="delete",
                tenant_id="org:acme",
            ),
        ]
        result = client.grant_many(grants)
        print(f"   Granted {result.granted} permissions\n")

        # Example 4: Check a single permission
        print("4. Checking a single permission...")
        allowed = client.check_permission(
            subjects=["user:alice"],
            scope="documents.management",
            action="read",
            tenant_id="org:acme",
        )
        print(f"   Can user:alice read documents? {allowed}\n")

        # Example 5: Check multiple permissions in batch
        print("5. Checking multiple permissions in batch...")
        checks = [
            CheckRequest(
                subjects=["user:alice"],
                scope="documents.management",
                action="read",
                tenant_id="org:acme",
                check_id="check-read",
            ),
            CheckRequest(
                subjects=["user:alice"],
                scope="documents.management",
                action="write",
                tenant_id="org:acme",
                check_id="check-write",
            ),
            CheckRequest(
                subjects=["user:alice"],
                scope="documents.management",
                action="admin",
                tenant_id="org:acme",
                check_id="check-admin",
            ),
        ]
        check_results = client.check_many(checks)
        for check_result in check_results:
            status = "✓ Allowed" if check_result.allowed else "✗ Denied"
            print(f"   {check_result.check_id}: {status}")
        print()

        # Example 6: List permissions with filters
        print("6. Listing permissions with filters...")
        filters = PermissionFilter(
            subject="user:alice",
            tenant_id="org:acme",
            limit=10,
        )
        response = client.list_permissions(filters)
        print(f"   Total permissions for user:alice: {response.total}")
        for perm in response.items:
            print(f"   - {perm.scope}.{perm.action} (valid: {perm.is_valid})")
        print()

        # Example 7: List subjects
        print("7. Listing subjects...")
        subject_filters = SubjectFilter(
            subject_type="user",
            tenant_id="org:acme",
            limit=10,
        )
        subjects_response = client.list_subjects(subject_filters)
        print(f"   Total subjects: {subjects_response.total}")
        for subj in subjects_response.items:
            print(f"   - {subj.identifier}: {subj.display_name}")
        print()

        # Example 8: List scopes
        print("8. Listing scopes...")
        scope_filters = ScopeFilter(
            search="document",
            limit=10,
        )
        scopes_response = client.list_scopes(scope_filters)
        print(f"   Total scopes: {scopes_response.total}")
        for scp in scopes_response.items:
            print(f"   - {scp.identifier}: {scp.display_name}")
        print()

        # Example 9: Revoke permissions
        print("9. Revoking a permission...")
        revoked = client.revoke_permission(
            subject="user:alice",
            scope="documents.management",
            action="delete",
            tenant_id="org:acme",
        )
        print(f"   Permission revoked: {revoked}\n")

        # Example 10: Pagination
        print("10. Handling pagination...")
        page_filters = PermissionFilter(limit=2, offset=0)
        first_page = client.list_permissions(page_filters)
        print(f"   Page 1: {len(first_page.items)} items")
        print(f"   Has more pages: {first_page.has_more}")
        if first_page.has_more:
            print(f"   Next offset: {first_page.next_offset}")
        print()

        print("=== Examples Complete ===")


if __name__ == "__main__":
    main()
