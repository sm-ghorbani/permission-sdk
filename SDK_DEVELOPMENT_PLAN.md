# Python SDK Development Plan for Permission Service

## 1. SDK Overview and Goals

### Purpose
Create a production-ready Python SDK that simplifies integration with the Permission Service microservice, providing both synchronous and asynchronous client interfaces with full type safety.

### Key Design Principles
- **Type Safety**: Full type hints for IDE autocomplete and static analysis
- **Ease of Use**: Intuitive API that mirrors business logic, not just HTTP calls
- **Reliability**: Built-in retry logic, error handling, and connection management
- **Performance**: Async support, connection pooling, and efficient batch operations
- **Developer Experience**: Comprehensive documentation, examples, and helpful error messages

---

## 2. SDK Architecture

### 2.1 Package Structure
```
permission-sdk/
├── permission_sdk/
│   ├── __init__.py              # Public API exports
│   ├── client.py                # Main PermissionClient class
│   ├── async_client.py          # AsyncPermissionClient class
│   ├── config.py                # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── permissions.py       # Permission-related models
│   │   ├── subjects.py          # Subject models
│   │   ├── scopes.py            # Scope models
│   │   └── common.py            # Shared models (metadata, pagination)
│   ├── exceptions.py            # Custom exceptions
│   ├── transport.py             # HTTP transport layer (requests/httpx)
│   └── utils.py                 # Utilities (retry logic, validation)
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Pytest fixtures
├── examples/                    # Usage examples
│   ├── basic_usage.py
│   ├── async_usage.py
│   ├── batch_operations.py
│   └── error_handling.py
├── docs/                        # Documentation
│   ├── api_reference.md
│   ├── quickstart.md
│   └── advanced_usage.md
├── pyproject.toml               # Package metadata and dependencies
├── README.md                    # Project overview
└── LICENSE                      # License file
```

---

## 3. Core Components Design

### 3.1 Client Classes

#### **PermissionClient** (Synchronous)
```python
class PermissionClient:
    """Synchronous client for Permission Service API.

    Features:
    - Simple request/response model
    - Automatic retry with exponential backoff
    - Connection pooling via requests.Session
    - Type-safe methods for all endpoints
    """

    Methods:
    - __init__(base_url, api_key, timeout, retry_config, **kwargs)
    - grant_permission(subject, scope, action, **kwargs) -> PermissionAssignment
    - grant_many(grants: list[GrantRequest]) -> GrantManyResult
    - revoke_permission(subject, scope, action, **kwargs) -> bool
    - revoke_many(revocations: list[RevokeRequest]) -> RevokeManyResult
    - check_permission(subjects, scope, action, **kwargs) -> bool
    - check_many(checks: list[CheckRequest]) -> list[CheckResult]
    - list_permissions(filters: PermissionFilter) -> PaginatedPermissions
    - create_subject(identifier, **kwargs) -> Subject
    - get_subject(identifier, tenant_id=None) -> Subject
    - list_subjects(filters: SubjectFilter) -> PaginatedSubjects
    - deactivate_subject(identifier) -> bool
    - create_scope(identifier, **kwargs) -> Scope
    - get_scope(identifier) -> Scope
    - list_scopes(filters: ScopeFilter) -> PaginatedScopes
    - deactivate_scope(identifier) -> bool
    - close() -> None  # Cleanup connections
```

#### **AsyncPermissionClient** (Asynchronous)
```python
class AsyncPermissionClient:
    """Async client for Permission Service API.

    Features:
    - All methods are async (use httpx.AsyncClient)
    - Supports concurrent requests
    - Context manager support (async with)
    - Same API as sync client but with await
    """

    Same methods as PermissionClient but async
    - async with support
    - aclose() for cleanup
```

### 3.2 Data Models

#### Permission Models
```python
@dataclass
class PermissionAssignment:
    assignment_id: str
    subject: str
    scope: str
    action: str
    tenant_id: str | None
    object_id: str | None
    granted_at: datetime
    expires_at: datetime | None
    metadata: dict[str, Any] | None

@dataclass
class GrantRequest:
    subject: str
    scope: str
    action: str
    tenant_id: str | None = None
    object_id: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] | None = None

@dataclass
class CheckRequest:
    subjects: list[str]
    scope: str
    action: str
    tenant_id: str | None = None
    object_id: str | None = None
    check_id: str | None = None

@dataclass
class CheckResult:
    allowed: bool
    matched_subject: str | None
    check_id: str | None

@dataclass
class PermissionFilter:
    subject: str | None = None
    scope: str | None = None
    action: str | None = None
    tenant_id: str | None = None
    object_id: str | None = None
    include_expired: bool = False
    limit: int = 100
    offset: int = 0
```

#### Subject Models
```python
@dataclass
class Subject:
    id: str
    identifier: str
    subject_type: str
    subject_id: str
    display_name: str | None
    tenant_id: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

@dataclass
class SubjectFilter:
    subject_type: str | None = None
    tenant_id: str | None = None
    search: str | None = None
    include_inactive: bool = False
    limit: int = 100
    offset: int = 0
```

#### Scope Models
```python
@dataclass
class Scope:
    id: str
    identifier: str
    display_name: str | None
    description: str | None
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

@dataclass
class ScopeFilter:
    scope_type: str | None = None
    search: str | None = None
    include_inactive: bool = False
    limit: int = 100
    offset: int = 0
```

#### Pagination Models
```python
@dataclass
class PaginatedPermissions:
    total: int
    limit: int
    offset: int
    permissions: list[PermissionDetail]

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.permissions) < self.total

    @property
    def next_offset(self) -> int | None:
        return self.offset + self.limit if self.has_more else None

# Similar for PaginatedSubjects, PaginatedScopes
```

### 3.3 Exception Hierarchy
```python
class PermissionSDKError(Exception):
    """Base exception for all SDK errors"""

class ConfigurationError(PermissionSDKError):
    """Invalid configuration (missing API key, bad URL, etc.)"""

class AuthenticationError(PermissionSDKError):
    """API key authentication failed (401)"""

class ValidationError(PermissionSDKError):
    """Request validation failed (400)"""
    def __init__(self, message: str, field: str | None = None)

class ResourceNotFoundError(PermissionSDKError):
    """Resource not found (404)"""

class ServerError(PermissionSDKError):
    """Server error (500)"""

class NetworkError(PermissionSDKError):
    """Network/connection errors"""

class RateLimitError(PermissionSDKError):
    """Rate limit exceeded (429)"""
    def __init__(self, message: str, retry_after: int | None = None)

class TimeoutError(PermissionSDKError):
    """Request timeout"""
```

### 3.4 Configuration Management
```python
@dataclass
class SDKConfig:
    """SDK configuration with sensible defaults"""

    # Connection
    base_url: str
    api_key: str
    timeout: int = 30  # seconds

    # Retry configuration
    max_retries: int = 3
    retry_backoff: float = 0.5  # seconds
    retry_multiplier: float = 2.0
    retry_on_status: set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})

    # Connection pooling
    pool_maxsize: int = 10
    pool_connections: int = 10

    # Validation
    validate_identifiers: bool = True  # Client-side validation

    @classmethod
    def from_env(cls) -> 'SDKConfig':
        """Load configuration from environment variables"""
        return cls(
            base_url=os.getenv('PERMISSION_SERVICE_URL', 'http://localhost:8000'),
            api_key=os.getenv('PERMISSION_SERVICE_API_KEY', ''),
        )
```

### 3.5 Transport Layer
```python
class HTTPTransport:
    """Abstraction for HTTP operations with retry logic"""

    def __init__(self, config: SDKConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers['X-API-Key'] = config.api_key

        # Connection pooling
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=config.max_retries,
                backoff_factor=config.retry_backoff,
                status_forcelist=list(config.retry_on_status),
            ),
            pool_maxsize=config.pool_maxsize,
            pool_connections=config.pool_connections,
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request with error handling"""
        # Implementation with comprehensive error handling
        # Converts HTTP errors to SDK exceptions
```

---

## 4. Implementation Phases

### Phase 1: Foundation (Days 1-2)
**Goal**: Set up project structure and core infrastructure

1. **Project Setup**
   - Initialize package structure
   - Configure `pyproject.toml` with dependencies
   - Set up linting (ruff/black), type checking (mypy)
   - Configure pytest with fixtures

2. **Core Components**
   - Implement `SDKConfig` configuration management
   - Implement exception hierarchy
   - Create base data models (use `dataclasses` or `pydantic`)
   - Implement `HTTPTransport` layer

3. **Testing Infrastructure**
   - Set up pytest with fixtures
   - Configure mock server for testing (respx/httpretty)
   - Write initial test cases for transport layer

**Deliverable**: Working project skeleton with config, exceptions, and transport

---

### Phase 2: Synchronous Client (Days 3-4)
**Goal**: Implement full sync client with all endpoints

1. **Permission Operations**
   - Implement `grant_permission` and `grant_many`
   - Implement `revoke_permission` and `revoke_many`
   - Implement `check_permission` and `check_many`
   - Implement `list_permissions`
   - Write comprehensive unit tests

2. **Subject Operations**
   - Implement CRUD operations for subjects
   - Write unit tests

3. **Scope Operations**
   - Implement CRUD operations for scopes
   - Write unit tests

4. **Error Handling & Validation**
   - Implement client-side validation helpers
   - Test error handling for all error scenarios

**Deliverable**: Fully functional `PermissionClient` with 90%+ test coverage

---

### Phase 3: Async Client (Days 5-6)
**Goal**: Implement async client with same API

1. **Async Transport**
   - Implement `AsyncHTTPTransport` using `httpx`
   - Async retry logic
   - Async connection pooling

2. **Async Client Implementation**
   - Port all methods to async versions
   - Implement context manager support
   - Test concurrent operations

3. **Integration Tests**
   - Test against real microservice (Docker Compose)
   - Verify sync/async clients have identical behavior

**Deliverable**: `AsyncPermissionClient` with full test coverage

---

### Phase 4: Developer Experience (Days 7-8)
**Goal**: Polish SDK for production use

1. **Documentation**
   - Write comprehensive README
   - Create API reference documentation
   - Write quickstart guide
   - Document advanced usage patterns

2. **Examples**
   - Basic CRUD operations
   - Batch operations optimization
   - Error handling patterns
   - Async usage examples
   - Integration with FastAPI/Django

3. **Utilities & Helpers**
   - Identifier validation utilities
   - Batch operation helpers (auto-chunking)
   - Debug logging integration
   - Performance optimization tips

4. **Packaging**
   - Configure pyproject.toml for PyPI
   - Write CHANGELOG
   - Set up semantic versioning
   - Create GitHub Actions for CI/CD

**Deliverable**: Production-ready SDK with documentation and examples

---

## 5. Testing Strategy

### Unit Tests
- Test all data models (serialization/deserialization)
- Test exception handling
- Mock HTTP responses for all client methods
- Test retry logic and backoff
- Test configuration validation

### Integration Tests
- Test against live service (Docker Compose)
- Test all endpoints with real data
- Test concurrent operations (async client)
- Test error scenarios (network failures, timeouts)
- Test pagination and filtering

### Coverage Goals
- Minimum 90% code coverage
- 100% coverage for critical paths (check, grant, revoke)
- All error paths tested

---

## 6. Dependencies

### Core Dependencies
```toml
[project]
dependencies = [
    "requests>=2.31.0",           # Sync HTTP client
    "httpx>=0.25.0",              # Async HTTP client
    "pydantic>=2.0.0",            # Data validation (optional: dataclasses)
    "python-dateutil>=2.8.0",     # Datetime handling
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "respx>=0.20.0",              # HTTP mocking for httpx
    "requests-mock>=1.11.0",       # HTTP mocking for requests
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
]
```

---

## 7. Usage Examples

### Basic Example
```python
from permission_sdk import PermissionClient, SDKConfig

# Initialize client
config = SDKConfig(
    base_url="https://permissions.example.com",
    api_key="your-api-key"
)
client = PermissionClient(config)

# Grant permission
assignment = client.grant_permission(
    subject="user:123",
    scope="documents.management",
    action="edit",
    tenant_id="org:456"
)

# Check permission
allowed = client.check_permission(
    subjects=["user:123", "role:editor"],
    scope="documents.management",
    action="edit",
    tenant_id="org:456"
)

if allowed:
    print("Access granted")
```

### Async Example
```python
from permission_sdk import AsyncPermissionClient, SDKConfig

async def check_permissions():
    async with AsyncPermissionClient(config) as client:
        # Concurrent checks
        results = await client.check_many([
            CheckRequest(subjects=["user:123"], scope="docs", action="read"),
            CheckRequest(subjects=["user:123"], scope="docs", action="write"),
            CheckRequest(subjects=["user:123"], scope="admin", action="manage"),
        ])

        for result in results:
            print(f"Check {result.check_id}: {result.allowed}")
```

### Batch Operations Example
```python
from permission_sdk import GrantRequest

# Batch grant permissions
grants = [
    GrantRequest(
        subject="user:123",
        scope="documents.management",
        action="read",
        tenant_id="org:456"
    ),
    GrantRequest(
        subject="user:123",
        scope="documents.management",
        action="write",
        tenant_id="org:456"
    ),
    GrantRequest(
        subject="user:123",
        scope="reports.viewing",
        action="read",
        tenant_id="org:456"
    ),
]

result = client.grant_many(grants)
print(f"Granted {result.granted} permissions")
```

### Error Handling Example
```python
from permission_sdk import (
    PermissionClient,
    AuthenticationError,
    ValidationError,
    ResourceNotFoundError,
    NetworkError
)

try:
    allowed = client.check_permission(
        subjects=["user:123"],
        scope="documents.management",
        action="edit"
    )
except AuthenticationError:
    print("API key is invalid")
except ValidationError as e:
    print(f"Invalid request: {e}")
except ResourceNotFoundError:
    print("Resource not found")
except NetworkError:
    print("Network connection failed")
```

---

## 8. Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes breaking SDK | High | Version SDK to match API versions, support multiple API versions |
| Performance issues with large batches | Medium | Implement auto-chunking for batch operations |
| Memory leaks in long-running clients | Medium | Proper connection cleanup, context managers |
| Type errors in production | Low | Comprehensive mypy coverage, runtime validation |
| Network failures | Medium | Robust retry logic, exponential backoff |

---

## 9. Success Criteria

1. **Functionality**: All API endpoints covered with type-safe methods
2. **Reliability**: 90%+ test coverage, all error paths handled
3. **Performance**: Batch operations 10x faster than individual calls
4. **Developer Experience**: Clear documentation, intuitive API, helpful errors
5. **Production Ready**: Published to PyPI, CI/CD pipeline, semantic versioning

---

## 10. Timeline Estimate

- **Phase 1** (Foundation): 2 days
- **Phase 2** (Sync Client): 2 days
- **Phase 3** (Async Client): 2 days
- **Phase 4** (Documentation & Polish): 2 days

**Total**: ~8 working days for v1.0.0 release

---

## 11. Future Enhancements (Post v1.0)

1. **Caching Layer**: Optional client-side caching for check operations
2. **Middleware Support**: Hooks for logging, metrics, custom headers
3. **CLI Tool**: Command-line interface for testing and debugging
4. **Django Integration**: Django middleware for permission checks
5. **FastAPI Integration**: FastAPI dependency injection helpers
6. **Observability**: OpenTelemetry tracing support
7. **Code Generation**: Auto-generate SDK from OpenAPI spec
8. **Bulk Import/Export**: Tools for migrating permissions between environments
9. **Permission Templates**: Reusable permission sets for common use cases
10. **Audit Log Client**: Query and analyze permission changes

---

## 12. API Endpoint Coverage

### Permissions Endpoints
- `POST /api/v1/permissions/grant` - Grant single permission
- `POST /api/v1/permissions/grant-many` - Grant multiple permissions
- `POST /api/v1/permissions/revoke` - Revoke single permission
- `POST /api/v1/permissions/revoke-many` - Revoke multiple permissions
- `POST /api/v1/permissions/check` - Check single permission
- `POST /api/v1/permissions/check-many` - Check multiple permissions
- `GET /api/v1/permissions` - List permissions with filters

### Subjects Endpoints
- `POST /api/v1/subjects` - Create or update subject
- `GET /api/v1/subjects/{identifier}` - Get subject by identifier
- `GET /api/v1/subjects` - List subjects with filters
- `DELETE /api/v1/subjects/{identifier}` - Deactivate subject

### Scopes Endpoints
- `POST /api/v1/scopes` - Create or update scope
- `GET /api/v1/scopes/{identifier}` - Get scope by identifier
- `GET /api/v1/scopes` - List scopes with filters
- `DELETE /api/v1/scopes/{identifier}` - Deactivate scope

---

## 13. Development Best Practices

### Code Quality
- Use type hints throughout (PEP 484)
- Follow PEP 8 style guide (enforced by ruff/black)
- Write docstrings for all public methods (Google style)
- Keep methods focused and under 50 lines
- Use meaningful variable names

### Testing
- Write tests before implementation (TDD)
- Use fixtures for common test data
- Mock external dependencies
- Test happy path and error scenarios
- Maintain high test coverage

### Documentation
- Keep README up to date
- Include runnable code examples
- Document breaking changes in CHANGELOG
- Use clear, concise language
- Provide migration guides for version updates

### Version Management
- Follow Semantic Versioning (SemVer)
- Tag releases in git
- Maintain backward compatibility in minor versions
- Clearly communicate breaking changes

---

## Appendix: Technical Decisions

### Why Requests + HTTPX?
- **Requests**: Battle-tested, widely used, excellent for sync operations
- **HTTPX**: Modern async support, compatible API with requests, HTTP/2 support

### Why Dataclasses vs Pydantic?
- **Option 1 - Dataclasses**: Stdlib, lightweight, fast
- **Option 2 - Pydantic**: Better validation, JSON serialization, OpenAPI integration
- **Recommendation**: Use Pydantic for better DX and validation

### Retry Strategy
- Exponential backoff prevents thundering herd
- Retry only on idempotent operations (GET, PUT) or known-safe operations
- Configurable retry logic per use case

### Connection Pooling
- Reuse connections for better performance
- Configure pool size based on expected concurrency
- Properly clean up connections on shutdown
