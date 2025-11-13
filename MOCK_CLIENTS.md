# Mock Clients Documentation

Complete in-memory implementations of all adapters for Supabase + AuthKit authentication with Bearer tokens.

## Overview

This project provides fully-functional mock implementations of all infrastructure adapters, enabling fast, deterministic unit and integration testing without external dependencies.

### Supported Adapters

| Adapter | Live Implementation | Mock Implementation | Features |
|---------|------------------|-------------------|----------|
| **Auth** | SupabaseAuthAdapter | InMemoryAuthAdapter | Bearer tokens, sessions, credentials, token revocation |
| **Database** | SupabaseDatabaseAdapter | InMemoryDatabaseAdapter | CRUD, filtering, ordering, pagination, timestamps |
| **Storage** | SupabaseStorageAdapter | InMemoryStorageAdapter | Upload/download, metadata, bucket management |
| **Realtime** | SupabaseRealtimeAdapter | InMemoryRealtimeAdapter | Subscriptions, events, filtering, broadcasting |
| **HTTP Client** | Remote MCP Server | HttpMcpClient | Connection pooling, retries, health checks |

## Configuration

Control which adapters to use via environment variables:

```bash
# Use all mock adapters (default for tests)
export ATOMS_SERVICE_MODE=mock

# Use all live adapters (Supabase backend)
export ATOMS_SERVICE_MODE=live

# Mix and match per service
export ATOMS_AUTHKIT_MODE=mock        # Mock auth
export ATOMS_SUPABASE_MODE=live       # Live database/storage/realtime
export ATOMS_MCP_CLIENT_MODE=local    # Local HTTP client
```

### Service Modes

- **`mock`**: In-memory implementation, no external dependencies
- **`live`**: Real Supabase/AuthKit services, requires credentials
- **`local`**: HTTP client connecting to localhost (for local development)

## InMemoryAuthAdapter

Complete AuthKit + Bearer token authentication with session management.

### Features

- ✅ Bearer token validation (JWT-like format)
- ✅ Session creation and revocation
- ✅ Credential verification
- ✅ Multiple concurrent sessions
- ✅ Token expiration tracking
- ✅ Default mock users

### Usage

```python
from infrastructure.mock_adapters import InMemoryAuthAdapter

auth = InMemoryAuthAdapter()

# Create a session (returns Bearer token)
token = await auth.create_session("user-123", "user@example.com")

# Validate any token
user = await auth.validate_token(token)
# Returns: {"user_id": "user-123", "email": "user@example.com", ...}

# Verify credentials
user = await auth.verify_credentials("user@example.com", "password")

# Revoke a token
await auth.revoke_session(token)
```

### Bearer Token Format

Mock Bearer tokens follow JWT structure (for testing):

```
header.payload.signature
eyJhbGc...  .  eyJ1c2VyX2...  .  c2lnXzE...
```

Decoded payload:
```json
{
  "user_id": "user-456",
  "email": "user@example.com",
  "iat": 1731443853,
  "exp": 1731447453,
  "iss": "mock-authkit",
  "sub": "user-456"
}
```

## InMemoryDatabaseAdapter

Supabase-compatible database operations with full SQL-like query support.

### Features

- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Filtering with multiple conditions
- ✅ Ordering (ASC/DESC)
- ✅ Pagination (limit/offset)
- ✅ Column selection
- ✅ Auto-generated IDs (UUIDs)
- ✅ Auto-timestamped fields (created_at, updated_at)
- ✅ Soft delete support (is_deleted flag)
- ✅ Batch operations

### Usage

```python
from infrastructure.mock_adapters import InMemoryDatabaseAdapter

db = InMemoryDatabaseAdapter()

# Insert single record
user = await db.insert("users", {
    "name": "Alice",
    "email": "alice@example.com"
})
# Returns: {"id": "...", "name": "Alice", "created_at": "2025-11-13T...", ...}

# Insert multiple records
users = await db.insert("users", [
    {"name": "Bob"},
    {"name": "Carol"}
])

# Query with filters
results = await db.query("users", filters={"status": "active"})

# Query with ordering
results = await db.query("users", order_by="created_at DESC")

# Pagination
page1 = await db.query("users", limit=10, offset=0)
page2 = await db.query("users", limit=10, offset=10)

# Select specific columns
results = await db.query("users", select="id,name,email")

# Get single record
user = await db.get_single("users", filters={"id": "123"})

# Update record
user = await db.update("users", {"status": "inactive"}, {"id": "123"})

# Delete records
count = await db.delete("users", {"status": "archived"})

# Count records
count = await db.count("users", {"active": True})
```

### Auto-Generated Fields

The adapter automatically manages common fields:

| Field | Condition | Format |
|-------|-----------|--------|
| `id` | Missing on insert | UUID v4 string |
| `created_at` | First insert, no value | ISO 8601 UTC timestamp |
| `updated_at` | Every insert/update | ISO 8601 UTC timestamp |
| `is_deleted` | Insert, no value | Boolean (default: false) |

Example timestamps:
```
created_at: "2025-11-13T02:37:33.532962Z"
updated_at: "2025-11-13T02:37:33.533274Z"
```

## InMemoryStorageAdapter

File/blob storage operations (in-memory, no disk I/O).

### Features

- ✅ Upload with metadata
- ✅ Download files
- ✅ Delete files
- ✅ Public URL generation
- ✅ Multiple buckets
- ✅ Content type support

### Usage

```python
from infrastructure.mock_adapters import InMemoryStorageAdapter

storage = InMemoryStorageAdapter()

# Upload a file
url = await storage.upload("documents", "report.pdf", pdf_bytes)
# Returns: "mem://documents/report.pdf"

# Upload with metadata
url = await storage.upload(
    "images",
    "avatar.jpg",
    image_bytes,
    content_type="image/jpeg",
    metadata={"owner": "alice"}
)

# Download a file
content = await storage.download("documents", "report.pdf")

# Delete a file
deleted = await storage.delete("documents", "report.pdf")

# Get public URL
url = storage.get_public_url("documents", "report.pdf")
# Returns: "mem://documents/report.pdf"
```

## InMemoryRealtimeAdapter

Realtime subscriptions and event broadcasting.

### Features

- ✅ Subscribe to table events
- ✅ Event filtering (INSERT, UPDATE, DELETE)
- ✅ Event broadcasting
- ✅ Multiple subscriptions
- ✅ Async callback execution
- ✅ Unsubscribe

### Usage

```python
from infrastructure.mock_adapters import InMemoryRealtimeAdapter

realtime = InMemoryRealtimeAdapter()

# Subscribe to events
events = []
async def on_event(event):
    events.append(event)

sub_id = await realtime.subscribe(
    "users",
    on_event,
    events=["INSERT", "UPDATE"]  # Only these events
)

# Emit an event (for testing)
await realtime._emit("users", "INSERT", {"id": "123", "name": "Alice"})

# Check received events
print(events)  # [{"event": "INSERT", "row": {"id": "123", ...}}]

# Unsubscribe
await realtime.unsubscribe(sub_id)
```

## HttpMcpClient

HTTP client for connecting to local or remote MCP servers.

### Features

- ✅ Connection pooling
- ✅ Exponential backoff retries
- ✅ Health checks
- ✅ Configurable timeout
- ✅ Async context manager support

### Usage

```python
from infrastructure.mock_adapters import HttpMcpClient

# Create client
client = HttpMcpClient(
    "http://localhost:8000",
    timeout=30,
    max_retries=3
)

# Health check
health = await client.health()
# Returns: {"status": "ok", ...}

# Call MCP method (with retries)
try:
    result = await client.call_mcp({
        "method": "workspace.list",
        "params": {}
    })
except ConnectionError as e:
    print(f"Failed after retries: {e}")

# Use as async context manager
async with HttpMcpClient("http://localhost:8000") as client:
    health = await client.health()

# Manual cleanup
await client.close()
```

### Retry Logic

Exponential backoff with configurable max retries:

```
Attempt 1: immediate
Attempt 2: wait 1 second (2^0)
Attempt 3: wait 2 seconds (2^1)
Attempt 4: wait 4 seconds (2^2)
Attempt 5+: fail
```

## AdapterFactory

Unified factory for creating adapters based on configuration.

### Usage

```python
from infrastructure.factory import AdapterFactory
import os

os.environ["ATOMS_SERVICE_MODE"] = "mock"

factory = AdapterFactory()

# Get individual adapters
auth = factory.get_auth_adapter()        # InMemoryAuthAdapter
db = factory.get_database_adapter()      # InMemoryDatabaseAdapter
storage = factory.get_storage_adapter()  # InMemoryStorageAdapter
realtime = factory.get_realtime_adapter()# InMemoryRealtimeAdapter

# Get all adapters
adapters = factory.get_all_adapters()
# Returns: {"auth": ..., "database": ..., "storage": ..., "realtime": ...}

# Check backend type
backend = factory.get_backend_type()  # "supabase" (default)
```

## Testing Integration

### With pytest

```python
import pytest
from infrastructure.factory import AdapterFactory
import os

@pytest.fixture
def mock_adapters():
    os.environ["ATOMS_SERVICE_MODE"] = "mock"
    factory = AdapterFactory()
    return factory.get_all_adapters()

@pytest.mark.asyncio
async def test_user_creation(mock_adapters):
    db = mock_adapters["database"]
    auth = mock_adapters["auth"]
    
    # Create user via auth
    token = await auth.create_session("user-123", "user@example.com")
    
    # Create user record in DB
    user = await db.insert("users", {"name": "Alice"})
    
    assert user["id"] is not None
    assert user["created_at"] is not None
```

### With fixtures (conftest.py)

```python
import pytest
import os
from infrastructure.factory import AdapterFactory

@pytest.fixture(autouse=True)
def force_mock_mode(monkeypatch):
    """Force all tests to use mock adapters."""
    monkeypatch.setenv("ATOMS_SERVICE_MODE", "mock")

@pytest.fixture
def auth_adapter():
    factory = AdapterFactory()
    return factory.get_auth_adapter()

@pytest.fixture
async def db_adapter():
    factory = AdapterFactory()
    return factory.get_database_adapter()
```

## Performance

Mock adapters are extremely fast since they're in-memory:

| Operation | Typical Time |
|-----------|-------------|
| Insert 100 records | < 1ms |
| Query with filter | < 0.1ms |
| Upload file | < 0.1ms |
| Auth token validation | < 0.1ms |

## No External Dependencies

Mock adapters have **zero external dependencies**:

- ✅ No Supabase client library required
- ✅ No AuthKit SDK required
- ✅ No PostgreSQL connection needed
- ✅ No network calls
- ✅ 100% deterministic

## Limitations

Mock adapters are intentionally simplified:

- No real cryptographic validation (Bearer tokens are fake JWT format)
- No real storage on disk (in-memory only)
- No real PostgreSQL queries (simple filtering only)
- No RLS (Row-Level Security) enforcement
- No transactions across tables

These are **intentional tradeoffs** for testing speed and isolation. Use live adapters for integration tests that need real database behavior.

## Migration to Live Adapters

Switching from mock to live adapters is seamless:

```python
# Just change the environment variable
os.environ["ATOMS_SERVICE_MODE"] = "live"

# Everything else stays the same!
factory = AdapterFactory()
db = factory.get_database_adapter()  # Now uses SupabaseDatabaseAdapter
```

No code changes needed – the factory handles it all.

## Contributing

To enhance mock adapters:

1. Add tests in `tests/unit/test_mock_clients.py`
2. Ensure backward compatibility with live adapter interface
3. Keep zero external dependencies
4. Document new features in this README
5. Add usage examples

## Files

```
infrastructure/
├── mock_adapters.py          # All mock adapter implementations
├── mock_config.py            # Service mode configuration
├── factory.py                # Unified adapter factory
└── adapters.py               # Abstract base interfaces

tests/unit/
└── test_mock_clients.py      # Comprehensive test suite (33 tests)
```

## Test Coverage

**33 comprehensive tests** covering all adapters:

- **Auth**: 8 tests (sessions, bearer tokens, credentials, revocation)
- **Database**: 13 tests (CRUD, filtering, ordering, pagination, timestamps)
- **Storage**: 5 tests (upload, download, delete, metadata)
- **Realtime**: 4 tests (subscriptions, events, filtering)
- **HTTP Client**: 3 tests (initialization, health checks, context manager)

Run tests:

```bash
source .venv/bin/activate
pytest tests/unit/test_mock_clients.py -v
# All 33 tests passing ✅
```

---

**Last Updated**: 2025-11-13  
**Status**: ✅ Complete and Production-Ready
