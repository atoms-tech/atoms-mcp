# Live and Mock Implementation Variants

This document describes the architecture for supporting both live (production) and mock variants of all services in the Atoms MCP Server project.

## Overview

The project supports three categories of implementation variants for each service:
- **Live**: Connects to actual production services (e.g., production Supabase, AuthKit)
- **Local**: Connects to locally running instances (e.g., local HTTP server on port 8000)
- **Mock**: Uses in-memory implementations for testing and offline development

## Supported Services

### 1. MCP Client
- **Mock**: InMemoryMcpClient (echo responses for testing)
- **Local**: HttpMcpClient against localhost:8000 (run locally)
- **Live**: HttpMcpClient against https://mcp.atoms.tech or https://mcpdev.atoms.tech

### 2. Supabase 
- **Mock**: InMemoryDatabaseAdapter with optional JSON seed data, InMemoryStorageAdapter, InMemoryRealtimeAdapter
- **Live**: SupabaseDatabaseAdapter, SupabaseStorageAdapter, SupabaseRealtimeAdapter

### 3. AuthKit
- **Mock**: InMemoryAuthAdapter using simple session tokens and default user
- **Live**: SupabaseAuthAdapter via WorkOS AuthKit OAuth

## Configuration

### Environment Variables

- `ATOMS_SERVICE_MODE`: Global default mode ("live", "local", "mock") [default: "live"]
- `ATOMS_MCP_CLIENT_MODE`: Override for MCP client only
- `ATOMS_SUPABASE_MODE`: Override for Supabase only  
- `ATOMS_AUTHKIT_MODE`: Override for AuthKit only

- `ATOMS_MCP_LIVE_ENDPOINT`: Production MCP endpoint [default: "https://mcp.atoms.tech"]
- `ATOMS_MCP_DEV_ENDPOINT`: Dev MCP endpoint [default: "https://mcpdev.atoms.tech"]
- `ATOMS_MCP_LOCAL_PORT`: Local MCP port [default: "8001"]

### Example Configurations

```bash
# All services in mock mode (for offline testing)
export ATOMS_SERVICE_MODE=mock

# Use live MCP with local Supabase and AuthKit mocks  
export ATOMS_SERVICE_MODE=mock
export ATOMS_MCP_CLIENT_MODE=live

# Use dev MCP with local databases
export ATOMS_MCP_CLIENT_MODE=local
export ATOMS_SUPABASE_MODE=mock
export ATOMS_AUTHKIT_MODE=mock
```

## Usage

### Getting Adapters

```python
from infrastructure.factory import AdapterFactory
factory = AdapterFactory()
adapters = factory.get_all_adapters()
# dict with "auth", "database", "storage", "realtime" keys
```

### Getting MCP Client

```python
from infrastructure.mcp_client_adapter import McpClientFactory
mcp_client = McpClientFactory().get()
# Returns either InMemoryMcpClient or HttpMcpClient based on config
```

### Checking Current Mode

```python
from infrastructure.mock_config import get_service_config
config = get_service_config()
print(config.is_service_mock("supabase"))
print(config.get_mcp_endpoint())
```

## Testing

Tests automatically use mock implementations via fixtures defined in `tests/fixtures/mock_services.py`. The root `conftest.py` forces mock mode for all tests unless overridden.

### Test Fixtures Available
- `mock_database`: Empty in-memory database adapter
- `mock_database_with_data`: In-memory database seeded with test data from `tests/fixtures/supabase_mock_data.json`
- `mock_auth`: In-memory auth adapter with default mock user
- `mock_storage`: In-memory storage adapter
- `mock_realtime`: In-memory realtime adapter
- `mock_mcp_client`: In-memory MCP client
- `mock_adapters`: Bundle of all the above
- `mock_adapter_factory`: AdapterFactory configured to return mock implementations
- `persistent_session_token`: Valid session token for test operations

### Example Test

```python
@pytest.mark.asyncio
async def test_workspace_operations(mock_database_with_data, mock_auth):
    # Test database operations
    workspaces = await mock_database_with_data.query("workspaces")
    assert len(workspaces) > 0
    
    # Test auth operations  
    token = await mock_auth.create_session("user-123", "test@example.com")
    user = await mock_auth.validate_token(token)
    assert user["user_id"] == "user-123"
```

## Implementation Files

### Configuration
- `infrastructure/mock_config.py`: ServiceConfig and ServiceMode classes

### Mock Implementations
- `infrastructure/mock_adapters.py`: InMemoryDatabaseAdapter, InMemoryAuthAdapter, etc.

### Factory Updates
- `infrastructure/factory.py`: Updated to use ServiceConfig to select implementations

### MCP Client
- `infrastructure/mcp_client_adapter.py`: InMemoryMcpClient and McpClientFactory

### Test Support
- `tests/fixtures/mock_services.py`: Test fixtures for using mock implementations
- `tests/fixtures/supabase_mock_data.json`: Sample data for seeded database tests
- `tests/conftest.py`: Forces mock mode for all tests unless explicitly overridden

This architecture allows for completely isolated unit tests while still supporting integration tests against local or production services when needed.