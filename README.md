# Permission SDK

Python SDK for the Permission Service API - A type-safe, production-ready client for managing permissions, subjects, and scopes.

## Features

- ✨ **Type-Safe**: Full type hints for IDE autocomplete and static analysis
- 🔄 **Automatic Retries**: Built-in retry logic with exponential backoff
- 🚀 **Performance**: Connection pooling and batch operations
- 🛡️ **Robust**: Comprehensive error handling and validation
- 📚 **Well-Documented**: Extensive documentation and examples
- 🧪 **Tested**: High test coverage for reliability

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

# Grant a permission
assignment = client.grant_permission(
    subject="user:123",
    scope="documents.management",
    action="edit",
    tenant_id="org:456"
)
print(f"Permission granted: {assignment.assignment_id}")

# Check if user has permission
allowed = client.check_permission(
    subjects=["user:123", "role:editor"],
    scope="documents.management",
    action="edit",
    tenant_id="org:456"
)

if allowed:
    print("Access granted!")
else:
    print("Access denied!")
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

## Error Handling

```python
from permission_sdk import (
    PermissionClient,
    AuthenticationError,
    ValidationError,
    ResourceNotFoundError,
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

    # SDK-Side Caching (NEW)
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