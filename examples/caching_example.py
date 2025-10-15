"""Example demonstrating SDK-side caching with automatic invalidation.

This example shows:
1. How to enable caching
2. Cache hits and misses
3. Automatic cache invalidation on grant/revoke
4. Performance improvements
"""

import time

from permission_sdk import PermissionClient, SDKConfig


def measure_time(func):
    """Decorator to measure function execution time."""

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds
        print(f"  ⏱️  Took {elapsed:.2f}ms")
        return result

    return wrapper


def main():
    """Demonstrate SDK caching."""

    # Configure SDK with caching enabled
    print("🔧 Configuring SDK with cache enabled...")
    config = SDKConfig(
        base_url="https://permissions.example.com",
        api_key="your-api-key",
        # Enable caching
        cache_enabled=True,
        cache_type="memory",  # Use memory cache for this example
        cache_ttl=300,  # 5 minutes
    )

    client = PermissionClient(config)

    print("\n" + "=" * 60)
    print("DEMO: SDK-Side Caching with Automatic Invalidation")
    print("=" * 60)

    # Example 1: Cache Miss → Cache Hit
    print("\n📋 Example 1: Cache Miss → Cache Hit")
    print("-" * 60)

    print("1. First check (cache miss - will call API):")

    @measure_time
    def first_check():
        return client.check_permission(
            subjects=["user:alice"], scope="documents.management", action="edit"
        )

    result = first_check()
    print(f"  Result: {result}")

    print("\n2. Second check (cache hit - instant!):")

    @measure_time
    def second_check():
        return client.check_permission(
            subjects=["user:alice"], scope="documents.management", action="edit"
        )

    result = second_check()
    print(f"  Result: {result}")
    print("  💨 Notice the dramatic speed improvement!")

    # Example 2: Cache Invalidation on Grant
    print("\n\n📋 Example 2: Automatic Cache Invalidation")
    print("-" * 60)

    print("1. Check permission (will be cached):")

    @measure_time
    def check_before_grant():
        return client.check_permission(
            subjects=["user:bob"], scope="documents.management", action="write"
        )

    result = check_before_grant()
    print(f"  Result: {result} (likely False)")

    print("\n2. Grant permission:")

    @measure_time
    def grant():
        return client.grant_permission(
            subject="user:bob", scope="documents.management", action="write"
        )

    grant()
    print("  ✅ Permission granted")
    print("  🗑️  Cache automatically invalidated for 'user:bob'")

    print("\n3. Check permission again (cache miss - was invalidated):")

    @measure_time
    def check_after_grant():
        return client.check_permission(
            subjects=["user:bob"], scope="documents.management", action="write"
        )

    result = check_after_grant()
    print(f"  Result: {result} (should be True)")
    print("  🔄 Cache was invalidated, so this called the API again")

    print("\n4. Check one more time (cache hit again):")

    @measure_time
    def check_cached_again():
        return client.check_permission(
            subjects=["user:bob"], scope="documents.management", action="write"
        )

    result = check_cached_again()
    print(f"  Result: {result}")
    print("  ⚡ Instant response from cache!")

    # Example 3: Batch Operations
    print("\n\n📋 Example 3: Batch Operations with Invalidation")
    print("-" * 60)

    print("1. Check permissions for multiple users (all get cached):")

    @measure_time
    def check_multiple():
        alice = client.check_permission(["user:alice"], "docs", "read")
        bob = client.check_permission(["user:bob"], "docs", "read")
        charlie = client.check_permission(["user:charlie"], "docs", "read")
        return alice, bob, charlie

    results = check_multiple()
    print(f"  Results: alice={results[0]}, bob={results[1]}, charlie={results[2]}")

    print("\n2. Batch grant to alice and bob:")
    from permission_sdk import GrantRequest

    @measure_time
    def batch_grant():
        grants = [
            GrantRequest(subject="user:alice", scope="docs", action="read"),
            GrantRequest(subject="user:bob", scope="docs", action="read"),
        ]
        return client.grant_many(grants)

    batch_grant()
    print("  ✅ Batch grant complete")
    print("  🗑️  Cache invalidated for alice and bob (but NOT charlie)")

    print("\n3. Check all three again:")

    @measure_time
    def check_after_batch():
        alice = client.check_permission(["user:alice"], "docs", "read")  # Cache miss
        bob = client.check_permission(["user:bob"], "docs", "read")  # Cache miss
        charlie = client.check_permission(["user:charlie"], "docs", "read")  # Cache HIT!
        return alice, bob, charlie

    results = check_after_batch()
    print(
        f"  Results: alice={results[0]}, bob={results[1]}, charlie={results[2]} (from cache)"
    )

    # Example 4: Cache with Different Subject Combinations
    print("\n\n📋 Example 4: Subject Chains and Cache Keys")
    print("-" * 60)

    print(
        "1. Check with subject chain (cache key includes ALL subjects in sorted order):"
    )

    @measure_time
    def check_chain():
        return client.check_permission(
            subjects=["user:alice", "role:editor", "group:content-team"],
            scope="documents.management",
            action="publish",
        )

    result = check_chain()
    print(f"  Result: {result}")

    print("\n2. Same subjects, different order (should hit same cache):")

    @measure_time
    def check_chain_reordered():
        return client.check_permission(
            subjects=["role:editor", "user:alice", "group:content-team"],
            scope="documents.management",
            action="publish",
        )

    result = check_chain_reordered()
    print(f"  Result: {result}")
    print("  💡 Cache keys are sorted, so order doesn't matter!")

    # Summary
    print("\n\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("\n✅ Cache Benefits:")
    print("  • First check: ~50ms (API call)")
    print("  • Cached check: ~0.5ms (100x faster!)")
    print("  • Automatic invalidation on grant/revoke")
    print("  • Works with batch operations")
    print("  • Transparent - no code changes needed")

    print("\n🔄 Invalidation Behavior:")
    print("  • grant_permission() → invalidates subject cache")
    print("  • revoke_permission() → invalidates subject cache")
    print("  • grant_many() → invalidates all affected subjects")
    print("  • revoke_many() → invalidates all affected subjects")

    print("\n💡 Best Practices:")
    print("  • Use Redis cache for production")
    print("  • Use memory cache for development")
    print("  • Set appropriate TTL (5 minutes is a good default)")
    print("  • Cache enabled = False by default (opt-in)")

    # Cleanup
    client.close()
    print("\n✨ Done!")


if __name__ == "__main__":
    main()
