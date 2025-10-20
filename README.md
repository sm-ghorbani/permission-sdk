# Permission SDK

Python SDK for the Permission Service API - A type-safe, production-ready client for managing permissions, subjects, scopes, and resource limits.

## Features

- ✨ **Type-Safe**: Full type hints for IDE autocomplete and static analysis
- 🔄 **Automatic Retries**: Built-in retry logic with exponential backoff
- 🚀 **Performance**: Connection pooling and batch operations (`check_many_limits`, `increment_many`, `grant_many`)
- 🎯 **Resource Limits**: Built-in support for quotas and rate limiting with hierarchy enforcement
- 🔄 **Async Support**: Full async/await support with AsyncPermissionClient
- 🛡️ **Robust**: Comprehensive error handling and validation
- 📚 **Well-Documented**: Extensive documentation and examples
- 🧪 **Tested**: High test coverage for reliability

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
  - [Permission Operations](#permission-operations)
  - [Subject Management](#subject-management)
  - [Scope Management](#scope-management)
  - [Resource Limit Management](#resource-limit-management)
- [Async Client](#async-client)
- [Error Handling](#error-handling)
- [Advanced Configuration](#advanced-configuration)
- [SDK-Side Caching](#sdk-side-caching)
- [Best Practices](#best-practices)
- [Development](#development)

## Installation

```bash
pip install permission-sdk
```

## Quick Start

```python
from permission_sdk import PermissionClient, SDKConfig

# Initialize client
config = SDKConfig(
    base_url="https://permissions.example.com",
    api_key="your-api-key"
)

# Simple usage - cleanup happens automatically
client = PermissionClient(config)

# 1. Manage permissions
assignment = client.grant_permission(
    subject="user:123",
    scope="documents.management",
    action="edit",
    tenant_id="org:456"
)
print(f"Permission granted: {assignment.assignment_id}")

# 2. Check permissions
allowed = client.check_permission(
    subjects=["user:123", "role:editor"],
    scope="documents.management",
    action="edit",
    tenant_id="org:456"
)
print(f"Access {'granted' if allowed else 'denied'}!")

# 3. Enforce resource limits
# Set a monthly project creation limit
client.set_limit(
    subject="user:123",
    resource_type="project",
    scope="organization:456",
    limit_value=10,
    window_type="monthly"
)

# Check limit before creating resource
limit_check = client.check_limit(
    subject="user:123",
    resource_type="project",
    scope="organization:456",
    amount=1
)

if limit_check.allowed:
    # Create the project...
    client.increment_usage(
        subject="user:123",
        resource_type="project",
        scope="organization:456",
        amount=1
    )
    print(f"Project created! {limit_check.remaining - 1} remaining")
else:
    print(f"Limit exceeded! Resets at {limit_check.resets_at}")
```

## Configuration

### From Direct Values

```python
from permission_sdk import SDKConfig

config = SDKConfig(
    base_url="https://permissions.example.com",
    api_key="your-api-key",
    timeout=60,
    max_retries=5
)
```

### From Environment Variables

```bash
export PERMISSION_SDK_BASE_URL=https://permissions.example.com
export PERMISSION_SDK_API_KEY=your-api-key
export PERMISSION_SDK_TIMEOUT=60
export PERMISSION_SDK_MAX_RETRIES=5
```

```python
from permission_sdk import SDKConfig

config = SDKConfig.from_env()
```

## Usage Examples

### Permission Operations

#### Grant Permissions

```python
# Grant a single permission
assignment = client.grant_permission(
    subject="user:alice",
    scope="documents.management",
    action="edit",
    tenant_id="org:acme",
    metadata={"granted_by": "admin:1", "reason": "Project access"}
)

# Batch grant permissions
from permission_sdk import GrantRequest

grants = [
    GrantRequest(
        subject="user:alice",
        scope="documents.management",
        action="read",
        tenant_id="org:acme"
    ),
    GrantRequest(
        subject="user:alice",
        scope="documents.management",
        action="write",
        tenant_id="org:acme"
    ),
]

result = client.grant_many(grants)
print(f"Granted {result.granted} permissions")
```

#### Check Permissions

```python
# Check single permission
allowed = client.check_permission(
    subjects=["user:alice", "role:editor"],
    scope="documents.management",
    action="edit",
    tenant_id="org:acme"
)

# Batch check permissions (optimized for UI)
from permission_sdk import CheckRequest

checks = [
    CheckRequest(
        subjects=["user:alice"],
        scope="documents.management",
        action="read",
        check_id="check-1"
    ),
    CheckRequest(
        subjects=["user:alice"],
        scope="reports.viewing",
        action="view",
        check_id="check-2"
    ),
]

results = client.check_many(checks)
for result in results:
    print(f"{result.check_id}: {'Allowed' if result.allowed else 'Denied'}")
```

#### Revoke Permissions

```python
# Revoke a single permission
revoked = client.revoke_permission(
    subject="user:alice",
    scope="documents.management",
    action="edit",
    tenant_id="org:acme"
)

# Batch revoke permissions
from permission_sdk import RevokeRequest

revocations = [
    RevokeRequest(
        subject="user:alice",
        scope="documents.management",
        action="read"
    ),
    RevokeRequest(
        subject="user:alice",
        scope="documents.management",
        action="write"
    ),
]

count = client.revoke_many(revocations)
print(f"Revoked {count} permissions")
```

#### List Permissions

```python
from permission_sdk import PermissionFilter

# List with filters
filters = PermissionFilter(
    subject="user:alice",
    scope="documents.management",
    include_expired=False,
    limit=50,
    offset=0
)

response = client.list_permissions(filters)
print(f"Total permissions: {response.total}")

for perm in response.items:
    print(f"{perm.subject} -> {perm.scope}.{perm.action}")

# Pagination
while response.has_more:
    response = client.list_permissions(
        PermissionFilter(offset=response.next_offset, limit=50)
    )
    # Process next page...
```

### Subject Management

```python
# Create a subject
subject = client.create_subject(
    identifier="user:alice",
    display_name="Alice Smith",
    tenant_id="org:acme",
    metadata={"email": "alice@acme.com"}
)

# Get a subject
subject = client.get_subject("user:alice")
print(f"Display name: {subject.display_name}")

# List subjects
from permission_sdk import SubjectFilter

filters = SubjectFilter(
    subject_type="user",
    tenant_id="org:acme",
    search="alice",
    limit=50
)

response = client.list_subjects(filters)
for subject in response.items:
    print(f"{subject.identifier}: {subject.display_name}")

# Deactivate a subject
client.deactivate_subject("user:alice")
```

### Scope Management

```python
# Create a scope
scope = client.create_scope(
    identifier="documents.management",
    display_name="Document Management",
    description="Permissions for managing documents",
    metadata={"category": "content"}
)

# Get a scope
scope = client.get_scope("documents.management")
print(f"Description: {scope.description}")

# List scopes
from permission_sdk import ScopeFilter

filters = ScopeFilter(
    scope_type="feature",
    search="document",
    limit=50
)

response = client.list_scopes(filters)
for scope in response.items:
    print(f"{scope.identifier}: {scope.display_name}")

# Deactivate a scope
client.deactivate_scope("documents.management")
```

### Resource Limit Management

Resource limits allow you to enforce quota and rate limiting on various resources like API calls, projects, storage, etc. The SDK supports multiple time windows (hourly, daily, monthly, total) and hierarchical limit checking.

#### Set Resource Limits

```python
# Set a monthly project creation limit
limit = client.set_limit(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    limit_value=10,
    window_type="monthly",  # Options: hourly, daily, monthly, total
    tenant_id="org:acme",
    metadata={"plan": "premium", "set_by": "admin:1"}
)

print(f"Limit set: {limit.limit_value} projects/month")
print(f"Current usage: {limit.current_usage}/{limit.limit_value}")

# Set different window types
# Hourly limit for API calls
client.set_limit(
    subject="user:alice",
    resource_type="api_call",
    scope="service:analytics",
    limit_value=1000,
    window_type="hourly"
)

# Total (non-resetting) limit for team members
client.set_limit(
    subject="org:acme",
    resource_type="team_member",
    scope="system",
    limit_value=50,
    window_type="total",
    metadata={"plan": "enterprise"}
)
```

#### Check Resource Limits

```python
# Check if user can create 1 project
result = client.check_limit(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    amount=1,
    tenant_id="org:acme"
)

if result.allowed:
    print(f"Operation allowed! {result.remaining} remaining")
else:
    print(f"Limit exceeded! Resets at: {result.resets_at}")

# Check if creating MULTIPLE resources would exceed limit
# Example: User wants to import 5 projects at once
bulk_check = client.check_limit(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    amount=5  # Checking if user can create 5 projects
)

# The response tells you:
# - allowed: False (if 5 would exceed limit)
# - would_exceed: True (if 5 is more than remaining)
# - remaining: 2 (only 2 slots left)
# - current_usage: 8 (already used 8 out of 10)

if bulk_check.would_exceed:
    print(f"Cannot create 5 projects! Only {bulk_check.remaining} remaining")
    print(f"You have used {bulk_check.current_usage}/{bulk_check.limit}")
else:
    print(f"OK to create 5 projects. {bulk_check.remaining - 5} will remain")
```

**Real-world scenario:**
```python
# Scenario: User has a limit of 10 projects per month
# User has already created 8 projects (current_usage = 8)
# User tries to import 5 projects from another system

import_count = 5

# Check BEFORE starting the import process
check = client.check_limit(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    amount=import_count  # Check if 5 more projects are allowed
)

print(f"Current usage: {check.current_usage}/10")  # Output: 8/10
print(f"Remaining slots: {check.remaining}")       # Output: 2
print(f"Trying to import: {import_count}")         # Output: 5
print(f"Would exceed: {check.would_exceed}")       # Output: True

if check.would_exceed:
    # 8 + 5 = 13, which exceeds limit of 10
    print(f"❌ Import failed! You can only import {check.remaining} more projects.")
    print(f"Limit resets on: {check.resets_at.strftime('%B %d, %Y')}")
else:
    # Safe to proceed with import
    for i in range(import_count):
        create_project(...)

    # Then increment usage by the bulk amount
    client.increment_usage(
        subject="user:alice",
        resource_type="project",
        scope="organization:acme",
        amount=import_count  # Increment by 5 at once
    )
```

**Key Benefits:**
- ✅ **Pre-validation**: Check before starting expensive operations
- ✅ **Better UX**: Tell users exactly how many they can create
- ✅ **Prevents waste**: Don't start bulk operations that will fail mid-way

#### Hierarchy Checking

Check multiple limits in a hierarchy (user → org → system) with a single batch request:

```python
from permission_sdk import SingleCheckLimitRequest

# Check user, org, and system limits together
hierarchy_checks = [
    SingleCheckLimitRequest(
        subject="user:alice",
        resource_type="project",
        scope="organization:acme",
        amount=1,
        check_id="user-limit"
    ),
    SingleCheckLimitRequest(
        subject="org:acme",
        resource_type="project",
        scope="system",
        amount=1,
        check_id="org-limit"
    ),
    SingleCheckLimitRequest(
        subject="system",
        resource_type="project",
        scope="global",
        amount=1,
        check_id="system-limit"
    ),
]

result = client.check_many_limits(hierarchy_checks)

# All must be allowed for operation to proceed
all_allowed = all(check.allowed for check in result.results)

for check in result.results:
    status = "✓" if check.allowed else "✗"
    print(f"{status} {check.check_id}: {check.current_usage}/{check.limit}")
```

#### Increment Usage

```python
# After successfully creating a project, increment usage
increment_result = client.increment_usage(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    amount=1,
    tenant_id="org:acme",
    metadata={"project_id": "proj:123", "action": "created"}
)

print(f"Usage updated: {increment_result.current_usage}/{increment_result.limit}")
print(f"Remaining: {increment_result.remaining}")

if increment_result.remaining == 0:
    print("User has reached their limit!")
```

#### Batch Increment (Hierarchy Updates)

After creating a resource, increment usage at multiple hierarchy levels (user → org → system) atomically:

```python
from permission_sdk import IncrementUsageRequest

# After creating a project, update all hierarchy levels
increments = [
    IncrementUsageRequest(
        subject="user:alice",
        resource_type="project",
        scope="organization:acme",
        amount=1,
        tenant_id="org:acme"
    ),
    IncrementUsageRequest(
        subject="org:acme",
        resource_type="project",
        scope="system",
        amount=1
    ),
]

result = client.increment_many(increments)

# Check all increments succeeded
for i, increment_result in enumerate(result.results):
    print(f"Level {i+1}: {increment_result.current_usage}/{increment_result.limit}")
    print(f"  Remaining: {increment_result.remaining}")

# Batch increment benefits:
# 1. Single HTTP request (faster)
# 2. Atomic operation (all succeed or all fail)
# 3. Maintains hierarchy consistency
```

**When to use batch increment:**
- ✅ Updating multiple hierarchy levels (user + org + system)
- ✅ Tracking usage across multiple resources simultaneously
- ✅ High-throughput applications where performance matters

**Performance comparison:**
```
Sequential increments (N=3):  3 × 50ms = 150ms
Batch increment_many (N=3):   1 × 80ms = 80ms  (2x faster)
```

#### Get Current Usage

```python
# Get current usage statistics
usage = client.get_usage(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    tenant_id="org:acme"
)

print(f"Resource: {usage.resource_type}")
print(f"Current usage: {usage.current_usage}/{usage.limit}")
print(f"Remaining: {usage.remaining}")
print(f"Window: {usage.window_type}")
print(f"Resets at: {usage.resets_at}")
```

#### Reset Usage

```python
# Admin override - reset usage to zero
reset_result = client.reset_usage(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    tenant_id="org:acme",
    metadata={"reason": "billing cycle reset", "admin": "admin:1"}
)

print(f"Reset from {reset_result.previous_usage} to {reset_result.current_usage}")
```

#### List Resource Limits

```python
from permission_sdk import LimitFilter

# List all limits for a subject
filters = LimitFilter(
    subject="user:alice",
    tenant_id="org:acme",
    limit=50
)

response = client.list_limits(filters)
print(f"Total limits: {response.total}")

for lim in response.items:
    percentage = (lim.current_usage / lim.limit_value * 100) if lim.limit_value > 0 else 0
    print(f"{lim.resource_type} @ {lim.scope}: {lim.current_usage}/{lim.limit_value} ({percentage:.1f}% used)")

# List limits by resource type
resource_filters = LimitFilter(
    resource_type="project",
    limit=100
)

response = client.list_limits(resource_filters)
for lim in response.items:
    print(f"{lim.subject} @ {lim.scope}: {lim.current_usage}/{lim.limit_value}")
```

#### Complete Workflow Example

Here's a complete workflow showing all steps together:

```python
from permission_sdk import PermissionClient, SDKConfig

client = PermissionClient(SDKConfig.from_env())

# Step 1: Set limit (typically done during user signup or plan change)
client.set_limit(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    limit_value=10,
    window_type="monthly"
)

# Step 2: Before creating resource, check if operation is allowed
check = client.check_limit(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    amount=1  # Check if user can create 1 more project
)

if not check.allowed:
    # Inform user they've hit their limit
    raise QuotaExceededError(
        f"Monthly project limit reached ({check.current_usage}/{check.limit}). "
        f"Limit resets at {check.resets_at.strftime('%Y-%m-%d %H:%M')}"
    )

# Step 3: Create the resource (your application-specific logic)
# This is where you'd call your database/service to create the resource
project = {
    "id": "proj_123",
    "name": "New Project",
    "owner": "user:alice",
    "created_at": "2024-01-15T10:30:00Z"
}

# Step 4: Increment usage counter to track consumption
client.increment_usage(
    subject="user:alice",
    resource_type="project",
    scope="organization:acme",
    amount=1,
    metadata={
        "project_id": project["id"],
        "project_name": project["name"],
        "action": "created"
    }
)

print(f"✓ Project created successfully! {check.remaining - 1} remaining this month")
```

> **💡 Tip:** For complete working examples, see the `examples/` directory:
> - `examples/basic_usage.py` - Permission operations
> - `examples/resource_limit_usage.py` - Resource limit operations
> - `examples/async_usage.py` - Async client examples
> - `examples/batch_operations.py` - Batch operations
> - `examples/caching_example.py` - SDK-side caching
> - `examples/error_handling.py` - Comprehensive error handling

## Async Client

The SDK provides full async/await support via `AsyncPermissionClient`. All operations are available with identical APIs:

```python
import asyncio
from permission_sdk import AsyncPermissionClient, SDKConfig

async def main():
    config = SDKConfig(
        base_url="https://permissions.example.com",
        api_key="your-api-key"
    )

    # Use async context manager
    async with AsyncPermissionClient(config) as client:
        # All methods are async versions of sync client

        # Check permission
        allowed = await client.check_permission(
            subjects=["user:alice"],
            scope="documents.management",
            action="edit"
        )

        # Grant permission
        assignment = await client.grant_permission(
            subject="user:alice",
            scope="documents.management",
            action="edit"
        )

        # Resource limits
        await client.set_limit(
            subject="user:alice",
            resource_type="api_call",
            scope="service:analytics",
            limit_value=1000,
            window_type="hourly"
        )

        result = await client.check_limit(
            subject="user:alice",
            resource_type="api_call",
            scope="service:analytics",
            amount=10
        )

        if result.allowed:
            await client.increment_usage(
                subject="user:alice",
                resource_type="api_call",
                scope="service:analytics",
                amount=10
            )

        # Batch operations
        from permission_sdk import SingleCheckLimitRequest, IncrementUsageRequest

        # Check multiple limits
        checks = [
            SingleCheckLimitRequest(subject="user:alice", resource_type="project", ...),
            SingleCheckLimitRequest(subject="org:acme", resource_type="project", ...),
        ]
        check_results = await client.check_many_limits(checks)

        # Increment multiple levels
        increments = [
            IncrementUsageRequest(subject="user:alice", resource_type="project", ...),
            IncrementUsageRequest(subject="org:acme", resource_type="project", ...),
        ]
        increment_results = await client.increment_many(increments)

# Run async code
asyncio.run(main())
```

**Key Points:**
- All methods from `PermissionClient` are available in `AsyncPermissionClient`
- Use `async with` for automatic cleanup
- Ideal for async frameworks (FastAPI, aiohttp, etc.)
- Full support for concurrent operations with `asyncio.gather()`
- Batch operations (`check_many_limits`, `increment_many`) work seamlessly with async

## Error Handling

```python
from permission_sdk import (
    PermissionClient,
    AuthenticationError,
    ValidationError,
    ResourceNotFoundError,
    ConflictError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    ServerError,
)

try:
    allowed = client.check_permission(
        subjects=["user:123"],
        scope="documents.management",
        action="edit"
    )
except AuthenticationError:
    print("Invalid API key - please check your credentials")
except ValidationError as e:
    print(f"Invalid request - field: {e.field}, error: {e}")
except ResourceNotFoundError as e:
    print(f"Resource not found: {e.resource_type}")
except ConflictError as e:
    print(f"Resource conflict: {e}")
    # Common for resource limits when trying to change window type
    print("Hint: Cannot change window_type of existing limit")
except RateLimitError as e:
    if e.retry_after:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
        time.sleep(e.retry_after)
except TimeoutError as e:
    print(f"Request timed out after {e.timeout} seconds")
except NetworkError:
    print("Network error - cannot connect to service")
except ServerError as e:
    print(f"Server error: {e}")
```

## Advanced Configuration

```python
from permission_sdk import SDKConfig

config = SDKConfig(
    base_url="https://permissions.example.com",
    api_key="your-api-key",

    # Timeout settings
    timeout=60,  # Request timeout in seconds

    # Retry configuration
    max_retries=5,              # Maximum retry attempts
    retry_backoff=0.5,          # Initial backoff time
    retry_multiplier=2.0,       # Backoff multiplier
    retry_on_status={429, 500, 502, 503, 504},

    # Connection pooling
    pool_maxsize=20,            # Max connections per pool
    pool_connections=20,        # Number of connection pools

    # Validation
    validate_identifiers=True,  # Client-side validation

    # SDK-Side Caching
    cache_enabled=True,         # Enable SDK-side caching
    cache_type="redis",         # "redis", "memory", or "none"
    cache_redis_url="redis://localhost:6379/0",  # Redis URL
    cache_ttl=300,              # Cache TTL in seconds (5 minutes)
    cache_prefix="perm_sdk",    # Cache key prefix
)
```

## SDK-Side Caching

The SDK supports optional client-side caching to dramatically reduce network calls and improve performance. When enabled, permission check results are cached locally.

### Why SDK-Side Caching?

- **Eliminates Network Overhead**: Cached checks don't hit the network at all (~0.1-1ms vs 5-50ms)
- **Automatic Invalidation**: Cache is automatically invalidated when permissions change
- **Two-Layer Caching**: Works alongside service-side caching for maximum performance
- **Optional and Safe**: Disabled by default, gracefully degrades if cache fails

### Enabling Cache

#### Option 1: Direct Configuration

```python
from permission_sdk import SDKConfig, PermissionClient

config = SDKConfig(
    base_url="https://permissions.example.com",
    api_key="your-api-key",
    cache_enabled=True,
    cache_type="redis",
    cache_redis_url="redis://localhost:6379/0",
    cache_ttl=300,  # 5 minutes
)

client = PermissionClient(config)
```

#### Option 2: Environment Variables

```bash
export PERMISSION_SDK_BASE_URL=https://permissions.example.com
export PERMISSION_SDK_API_KEY=your-api-key
export PERMISSION_SDK_CACHE_ENABLED=true
export PERMISSION_SDK_CACHE_TYPE=redis
export PERMISSION_SDK_CACHE_REDIS_URL=redis://localhost:6379/0
export PERMISSION_SDK_CACHE_TTL=300
```

```python
from permission_sdk import SDKConfig, PermissionClient

config = SDKConfig.from_env()
client = PermissionClient(config)
```

### Cache Types

#### Redis Cache (Production)
Best for multi-process/multi-server deployments:

```python
config = SDKConfig(
    ...
    cache_enabled=True,
    cache_type="redis",
    cache_redis_url="redis://localhost:6379/0",
)
```

#### In-Memory Cache (Development)
Best for single-process applications or testing:

```python
config = SDKConfig(
    ...
    cache_enabled=True,
    cache_type="memory",
)
```

#### No Cache (Default)
Caching disabled:

```python
config = SDKConfig(
    ...
    cache_enabled=False,  # or omit cache settings
)
```

### How Caching Works

#### Check Permission Flow

```python
# First check - cache miss
allowed = client.check_permission(
    subjects=["user:alice"],
    scope="documents.management",
    action="edit"
)
# → Calls API (~50ms)
# → Caches result for 5 minutes

# Subsequent checks - cache hit
allowed = client.check_permission(
    subjects=["user:alice"],
    scope="documents.management",
    action="edit"
)
# → Returns from cache (~0.5ms)
# → No network call!
```

#### Automatic Invalidation

When permissions change, the cache is automatically invalidated:

```python
# Grant permission
client.grant_permission(
    subject="user:alice",
    scope="documents.management",
    action="edit"
)
# → Calls API to grant permission
# → Automatically invalidates ALL cached checks for "user:alice"

# Next check - cache miss (was invalidated)
allowed = client.check_permission(
    subjects=["user:alice"],
    scope="documents.management",
    action="edit"
)
# → Calls API (cache was invalidated)
# → Returns True
# → Re-caches result
```

#### Batch Operations

Batch operations also trigger cache invalidation:

```python
# Batch grant
grants = [
    GrantRequest(subject="user:alice", scope="docs", action="read"),
    GrantRequest(subject="user:alice", scope="docs", action="write"),
    GrantRequest(subject="user:bob", scope="docs", action="read"),
]
client.grant_many(grants)
# → Invalidates cache for "user:alice" and "user:bob"
```

### Performance Comparison

| Operation | Without SDK Cache | With SDK Cache (Hit) | Improvement |
|-----------|------------------|---------------------|-------------|
| check_permission | ~50ms (API call) | ~0.5ms (local) | **100x faster** |
| Cached check | ~5ms (service cache) | ~0.5ms (SDK cache) | **10x faster** |
| grant_permission | ~50ms | ~50ms | Same (write operation) |

### Cache Configuration Strategies

#### High-Traffic Applications
Maximum performance with short-lived cache:

```python
config = SDKConfig(
    cache_enabled=True,
    cache_type="redis",
    cache_ttl=300,  # 5 minutes
)
```

**Use case**: Apps with high permission check volume that can tolerate 5-minute staleness.

#### Real-Time Applications
Shorter TTL for fresher data:

```python
config = SDKConfig(
    cache_enabled=True,
    cache_type="redis",
    cache_ttl=60,  # 1 minute
)
```

**Use case**: Apps requiring near-real-time permission updates.

#### Development/Testing
In-memory cache for local development:

```python
config = SDKConfig(
    cache_enabled=True,
    cache_type="memory",
    cache_ttl=60,
)
```

**Use case**: Local development without Redis dependency.

### Cache Behavior Summary

| Operation | Network Call | Cache Action | Result |
|-----------|-------------|--------------|--------|
| `check_permission` (first time) | ✅ Yes | Store result | Cached for TTL |
| `check_permission` (cached) | ❌ No | Return cached | Instant response |
| `grant_permission` | ✅ Yes | Invalidate subject | Subject cache cleared |
| `revoke_permission` | ✅ Yes | Invalidate subject | Subject cache cleared |
| `grant_many` | ✅ Yes | Invalidate all subjects | All subjects cleared |
| `list_permissions` | ✅ Yes | No caching | Pass-through |
| Resource limit operations | ✅ Yes | No caching | Pass-through |

### Important Notes

- **Only `check_permission` is cached** - Write operations always go to the API
- **Graceful degradation** - If cache fails, falls back to API calls
- **Automatic cleanup** - Cache connections are properly closed
- **Thread-safe** - Safe for concurrent use
- **Transparent** - No code changes needed, works with existing SDK calls

## Best Practices

### 1. Resource Management

The client automatically cleans up connections when garbage collected, but you can explicitly manage resources for better control:

```python
# Simple usage - automatic cleanup on garbage collection
client = PermissionClient(config)
client.check_permission(...)

# Context manager - explicit cleanup (recommended for production)
with PermissionClient(config) as client:
    client.check_permission(...)
# Connections are cleaned up immediately

# Manual cleanup - for long-running applications
client = PermissionClient(config)
try:
    client.check_permission(...)
finally:
    client.close()
```

### 2. Batch Operations

Use batch operations for better performance:

```python
# ❌ Bad: Multiple individual calls
for grant in grants:
    client.grant_permission(grant.subject, grant.scope, grant.action)

# ✅ Good: Single batch call
client.grant_many(grants)
```

### 3. Error Handling

Always handle specific exceptions:

```python
try:
    allowed = client.check_permission(...)
except ValidationError as e:
    # Handle validation errors specifically
    logger.error(f"Invalid input: {e}")
except PermissionSDKError:
    # Catch all SDK errors as fallback
    logger.error("Permission check failed")
```

### 4. Pagination

Handle pagination properly for large result sets:

```python
filters = PermissionFilter(limit=100)
response = client.list_permissions(filters)

all_permissions = response.items
while response.has_more:
    response = client.list_permissions(
        filters.copy(offset=response.next_offset)
    )
    all_permissions.extend(response.items)
```

### 5. Resource Limit Workflow

Follow the check-create-increment pattern for resource limits:

```python
# ❌ Bad: Create resource without checking limit
project = create_project()
client.increment_usage(...)  # Might exceed limit!

# ✅ Good: Check limit before creating resource
check = client.check_limit(
    subject="user:alice",
    resource_type="project",
    scope="org:acme",
    amount=1
)

if not check.allowed:
    raise QuotaExceededError(f"Limit exceeded. Resets at {check.resets_at}")

# Now safe to create
project = create_project()

# Track usage
client.increment_usage(
    subject="user:alice",
    resource_type="project",
    scope="org:acme",
    amount=1,
    metadata={"project_id": project.id}
)
```

### 6. Hierarchy Enforcement

Use batch operations for hierarchical limits:

```python
# ✅ Good: Check all hierarchy levels in one request
from permission_sdk import SingleCheckLimitRequest, IncrementUsageRequest

checks = [
    SingleCheckLimitRequest(subject="user:alice", ...),
    SingleCheckLimitRequest(subject="org:acme", ...),
    SingleCheckLimitRequest(subject="system", ...),
]
result = client.check_many_limits(checks)

# All must pass
if not all(check.allowed for check in result.results):
    # Find which level blocked
    blocked = [c for c in result.results if not c.allowed]
    raise LimitError(f"Blocked by: {blocked[0].check_id}")

# After creating resource, update all levels atomically
increments = [
    IncrementUsageRequest(subject="user:alice", resource_type="project", ...),
    IncrementUsageRequest(subject="org:acme", resource_type="project", ...),
]
client.increment_many(increments)
```

### 7. Complete Hierarchy Workflow

Here's a complete example showing check + create + increment pattern with hierarchy:

```python
from permission_sdk import SingleCheckLimitRequest, IncrementUsageRequest

# Step 1: Check all hierarchy levels before creating
hierarchy_checks = [
    SingleCheckLimitRequest(
        check_id="user",
        subject="user:alice",
        resource_type="project",
        scope="organization:acme",
        amount=1,
        tenant_id="org:acme"
    ),
    SingleCheckLimitRequest(
        check_id="org",
        subject="org:acme",
        resource_type="project",
        scope="system",
        amount=1
    ),
]

check_result = client.check_many_limits(hierarchy_checks)

# Ensure ALL levels allow the operation
if not all(c.allowed for c in check_result.results):
    blocked = [c for c in check_result.results if not c.allowed][0]
    raise QuotaExceededError(
        f"Limit exceeded at {blocked.check_id} level: "
        f"{blocked.current_usage}/{blocked.limit}"
    )

# Step 2: Create the resource (your application logic)
project = create_project(name="New Project", owner="user:alice")

# Step 3: Increment ALL hierarchy levels atomically
hierarchy_increments = [
    IncrementUsageRequest(
        subject="user:alice",
        resource_type="project",
        scope="organization:acme",
        amount=1,
        tenant_id="org:acme"
    ),
    IncrementUsageRequest(
        subject="org:acme",
        resource_type="project",
        scope="system",
        amount=1
    ),
]

increment_result = client.increment_many(hierarchy_increments)

print(f"✓ Project created!")
print(f"  User: {increment_result.results[0].remaining} remaining")
print(f"  Org:  {increment_result.results[1].remaining} remaining")
```

## Development

### Setup

```bash
git clone https://github.com/example/permission-sdk.git
cd permission-sdk
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=permission_sdk --cov-report=html

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration
```

### Type Checking

```bash
mypy permission_sdk
```

### Linting

```bash
ruff check permission_sdk
black --check permission_sdk
```

## Requirements

- Python >= 3.11
- httpx >= 0.25.0
- pydantic >= 2.0.0

## License

MIT License - see LICENSE file for details