# Implementation Strategy: Architecture & Design Patterns

**Date:** November 14, 2025  
**Focus:** Technical approach, patterns, and fixture architecture for E2E tests

## Test Architecture Overview

### Three-Tier Test Strategy

```
┌─────────────────────────────────────────────────────────────┐
│ E2E Tests (tests/e2e/)                                      │
│ Real deployment (mcpdev.atoms.tech), real auth, real DB    │
│ Parametrized: each test runs 3 times (unit/int/e2e)        │
│ Target: 172 tests covering all 48 user stories             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Integration Tests (tests/integration/)                      │
│ Real services (DB, Auth, Cache), local HTTP client         │
│ Target: 40+ tests covering infra layers                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Unit Tests (tests/unit/)                                    │
│ Mock services, in-memory client, fast & deterministic      │
│ Target: Focus on logic, not infrastructure                 │
└─────────────────────────────────────────────────────────────┘
```

### Client Variant Strategy

```python
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """
    Each test using mcp_client runs 3 times automatically:
    1. unit: InMemoryMcpClient() → Fast, mock, deterministic
    2. integration: HttpMcpClient(local) → Real local server, real DB
    3. e2e: HttpMcpClient(mcpdev) → Real deployment, full stack
    """
    if request.param == "unit":
        # Mock all services: DB, auth, cache, relationships
        return InMemoryMcpClient(
            db=MockSupabaseClient(),
            auth=MockAuthProvider(),
            cache=MockRedisClient()
        )
    elif request.param == "integration":
        # Real local services, HTTP client to localhost:8000
        return HttpMcpClient(
            base_url="http://127.0.0.1:8000",
            auth_token=get_local_test_token()
        )
    elif request.param == "e2e":
        # Real deployment services, HTTP client to mcpdev
        return AuthenticatedMcpClient(
            base_url="https://mcpdev.atoms.tech/api/mcp",
            auth_token=await get_e2e_auth_token()
        )
```

**Benefits:**
- ✅ Same test code runs 3 times (coverage × 3)
- ✅ Fast unit tests (milliseconds)
- ✅ Real integration tests (seconds)
- ✅ Full e2e tests against deployment (10-30s)
- ✅ No code duplication
- ✅ Single source of truth per test

### Canonical Test File Organization

**Principle:** File names describe *what's tested* (concern), not *how* (speed/variant)

```
tests/e2e/
├── test_organization_management.py           # Org CRUD + hierarchy
├── test_project_management.py                # Project CRUD + hierarchy
├── test_document_management.py               # Document CRUD + content
├── test_requirements_traceability.py         # Requirement CRUD + linking
├── test_test_case_management.py              # Test case CRUD + results
├── test_workspace_navigation.py              # Workspace context management
├── test_entity_relationships.py              # Relationship operations (all types)
├── test_search_and_discovery.py              # All search operations
├── test_workflow_automation.py               # Workflow execution scenarios
├── test_data_management.py                   # Pagination, sorting, batch
├── test_auth_patterns.py                     # Auth scenarios (by provider)
└── conftest.py                               # Shared fixtures

tests/integration/
├── test_auth_integration.py                  # Auth provider integration
├── test_database_operations.py               # Database layer integration
├── test_cache_integration.py                 # Caching layer integration
├── test_infrastructure.py                    # Middleware, health, config
└── conftest.py                               # Integration fixtures

Total: 11 E2E files + 4 integration files = 15 canonical test files
```

## Fixture Architecture

### Base Fixture: `mcp_client` (Parametrized for Variants)

**Location:** `tests/conftest.py` (root conftest)

```python
@pytest.fixture(params=["unit", "integration", "e2e"])
@pytest_asyncio.fixture
async def mcp_client(request, monkeypatch):
    """
    Parametrized MCP client for three test variants.
    
    Params:
    - unit: InMemoryMcpClient (mocks all services)
    - integration: HttpMcpClient (localhost:8000)
    - e2e: AuthenticatedMcpClient (mcpdev.atoms.tech)
    """
    if request.param == "unit":
        # Import mock client
        from tests.unit.mocks import InMemoryMcpClient
        return InMemoryMcpClient()
    
    elif request.param == "integration":
        # Setup local test server
        import httpx
        token = await get_local_test_token()
        return HttpMcpClient(
            base_url="http://127.0.0.1:8000",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    elif request.param == "e2e":
        # Setup mcpdev deployment client
        token = await get_e2e_auth_token()
        return AuthenticatedMcpClient(
            base_url="https://mcpdev.atoms.tech/api/mcp",
            auth_token=token
        )
```

### Authentication Fixtures

**Supabase JWT (Primary):**
```python
@pytest_asyncio.fixture
async def e2e_auth_token():
    """Get Supabase JWT for authenticated E2E tests."""
    from supabase import create_client
    
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    client = create_client(url, key)
    response = client.auth.sign_in_with_password({
        "email": "kooshapari@kooshapari.com",
        "password": "118118"
    })
    
    return response.session.access_token
```

**AuthKit OAuth (Secondary):**
```python
@pytest_asyncio.fixture
async def authkit_token():
    """Get AuthKit OAuth token for E2E tests."""
    # Mock implementation for testing
    return {
        "access_token": "authkit-token-xxx",
        "token_type": "Bearer",
        "expires_in": 3600
    }
```

### Workspace Context Fixtures

```python
@pytest_asyncio.fixture
async def org_context(mcp_client):
    """Create and set org workspace context."""
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": f"Test Org {uuid.uuid4().hex[:8]}"}
    )
    org_id = result["data"]["id"]
    
    # Set context
    await mcp_client.workspace_tool(
        operation="set_context",
        context_type="organization",
        entity_id=org_id
    )
    
    yield org_id
    
    # Cleanup: soft delete
    await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=org_id,
        operation="delete",
        soft_delete=True
    )

@pytest_asyncio.fixture
async def project_context(mcp_client, org_context):
    """Create and set project workspace context."""
    result = await mcp_client.entity_tool(
        entity_type="project",
        operation="create",
        data={"name": f"Test Project {uuid.uuid4().hex[:8]}"}
    )
    project_id = result["data"]["id"]
    
    await mcp_client.workspace_tool(
        operation="set_context",
        context_type="project",
        entity_id=project_id
    )
    
    yield project_id
    
    # Cleanup
    await mcp_client.entity_tool(
        entity_type="project",
        entity_id=project_id,
        operation="delete",
        soft_delete=True
    )
```

### Performance Tracking Fixture

```python
@pytest_asyncio.fixture
async def perf_tracker(e2e_performance_tracker):
    """Track operation performance metrics."""
    
    async def track_operation(name: str):
        """Context manager for tracking operation performance."""
        async with e2e_performance_tracker.track_operation(name):
            yield
    
    return track_operation

# Usage in tests:
async def test_entity_creation(mcp_client, perf_tracker):
    async with perf_tracker("create_organization"):
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": "Test Org"}
        )
    assert result["success"]
```

## Test Markers & Categorization

**Marker Strategy:** Use markers instead of file suffixes for categorization

### Test Type Markers
```python
@pytest.mark.unit          # Unit test (mocks all)
@pytest.mark.integration   # Integration test (real services, local)
@pytest.mark.e2e          # E2E test (full deployment)
```

### Speed Markers
```python
@pytest.mark.smoke        # Quick sanity check (<100ms)
@pytest.mark.slow         # Takes >5s (marked for separate runs)
```

### Feature Markers
```python
@pytest.mark.entity
@pytest.mark.workspace
@pytest.mark.relationship
@pytest.mark.query        # data_query tool
@pytest.mark.workflow
@pytest.mark.auth
```

### Requirements Markers
```python
@pytest.mark.requires_db
@pytest.mark.requires_auth
@pytest.mark.requires_cache
```

### Example: Applying Multiple Markers
```python
@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.entity
@pytest.mark.slow
async def test_batch_create_1000_entities(mcp_client):
    """Create 1000 entities in batch (slow test)."""
    entities = [{"name": f"Entity {i}"} for i in range(1000)]
    
    result = await mcp_client.entity_tool(
        entity_type="project",
        operation="create",
        batch=entities
    )
    assert len(result["data"]) == 1000
```

## Assertion Patterns & Error Classification

### Standard Success Assertion
```python
async def test_create_org(mcp_client):
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": "Acme Corp"}
    )
    
    # Standard assertions
    assert result["success"] is True
    assert "id" in result["data"]
    assert result["data"]["name"] == "Acme Corp"
    assert result["data"]["created_by"] == authenticated_user
```

### Error Classification (from existing infrastructure)
```python
async def test_invalid_entity_type(mcp_client):
    result = await mcp_client.entity_tool(
        entity_type="invalid_type",
        operation="create",
        data={}
    )
    
    # Check error type
    assert result["success"] is False
    assert result["error_type"] == "PRODUCT"  # Business logic error
    # or: "INFRASTRUCTURE" (DB/network), "TEST_DATA", "ASSERTION"
```

### Fuzzy Matching Assertion
```python
async def test_fuzzy_entity_read(mcp_client):
    # Create entity
    create_result = await mcp_client.entity_tool(
        entity_type="project",
        operation="create",
        data={"name": "Vehicle Project"}
    )
    
    # Read by fuzzy name
    read_result = await mcp_client.entity_tool(
        entity_type="project",
        entity_id="Vehicle",  # Fuzzy match
        operation="read"
    )
    
    assert read_result["success"]
    assert read_result["data"]["id"] == create_result["data"]["id"]
```

### RLS Enforcement Assertion
```python
async def test_rls_prevents_cross_user_access(mcp_client, other_user_token):
    # Create org as current user
    create_result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": "Private Org"}
    )
    org_id = create_result["data"]["id"]
    
    # Try to read as other user
    other_client = HttpMcpClient(
        base_url="https://mcpdev.atoms.tech/api/mcp",
        auth_token=other_user_token
    )
    
    read_result = await other_client.entity_tool(
        entity_type="organization",
        entity_id=org_id,
        operation="read"
    )
    
    assert read_result["success"] is False
    assert read_result["error_type"] == "INFRASTRUCTURE"  # 403 Forbidden
```

## Test Data Management

### Isolation Strategy

**Each test gets isolated data:**
```python
@pytest_asyncio.fixture
async def isolated_org(mcp_client):
    """Create org with unique name for test isolation."""
    org_name = f"Test Org {uuid.uuid4().hex[:8]}"
    
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": org_name}
    )
    
    yield result["data"]["id"]
    
    # Cleanup: soft delete
    await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=result["data"]["id"],
        operation="delete",
        soft_delete=True
    )
```

### Cleanup Strategy

**Automatic cleanup via fixtures:**
```python
@pytest_asyncio.fixture
async def test_project_stack(mcp_client):
    """Create complete org→project→doc stack for testing."""
    
    # Create org
    org_result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": f"Org {uuid.uuid4().hex[:8]}"}
    )
    org_id = org_result["data"]["id"]
    
    # Create project
    project_result = await mcp_client.entity_tool(
        entity_type="project",
        operation="create",
        data={"name": f"Project {uuid.uuid4().hex[:8]}"}
    )
    project_id = project_result["data"]["id"]
    
    # Create document
    doc_result = await mcp_client.entity_tool(
        entity_type="document",
        operation="create",
        data={"name": f"Doc {uuid.uuid4().hex[:8]}"}
    )
    doc_id = doc_result["data"]["id"]
    
    yield {
        "org_id": org_id,
        "project_id": project_id,
        "document_id": doc_id
    }
    
    # Cleanup all (cascade)
    for entity_id in [org_id, project_id, doc_id]:
        try:
            await mcp_client.entity_tool(
                entity_type="organization",  # Delete org cascades
                entity_id=entity_id,
                operation="delete",
                soft_delete=True
            )
        except:
            pass  # Already deleted via cascade
```

## Performance Testing Patterns

### Latency Baseline Test
```python
async def test_single_operation_latency(mcp_client, perf_tracker):
    """Baseline latency for single entity creation."""
    async with perf_tracker("create_org_latency"):
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": "Test"}
        )
    
    assert result["success"]
    # Performance assertion
    # E2E: <2s expected
    # Integration: <500ms expected
    # Unit: <10ms expected
```

### Throughput Test
```python
@pytest.mark.slow
async def test_batch_throughput_1000(mcp_client, perf_tracker):
    """Test throughput for batch create 1000 items."""
    entities = [
        {"name": f"Entity {i}"} for i in range(1000)
    ]
    
    async with perf_tracker("batch_create_1000"):
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="create",
            batch=entities
        )
    
    assert result["success"]
    assert len(result["data"]) == 1000
    # Expected: <30s for e2e
```

## Coverage Target Strategy

### Coverage Tiers
| Layer | Target | Tools |
|-------|--------|-------|
| Tools | ≥95% | entity, workspace, relationship, query, workflow |
| Services | ≥95% | embedding, search, auth helpers |
| Infrastructure | ≥95% | adapters, middleware, config |
| Overall | ≥95% | all modules combined |

### Coverage Measurement
```bash
# Generate coverage report
uv run pytest --cov=. --cov-report=html tests/e2e tests/integration

# View report
open htmlcov/index.html
```

### Handling Untestable Code
```python
# Mark as intentionally untestable
def legacy_system_interface():
    pass  # pragma: no cover - External system integration

# Document why
def mock_only_feature():  # pragma: no cover
    """Feature only testable with mocks due to external dependency.
    
    Real integration tested via manual verification.
    """
    pass
```

## Error Handling Patterns

### Expected Error Assertion
```python
async def test_create_with_invalid_data(mcp_client):
    """Creating entity with invalid data should fail."""
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": ""}  # Empty name invalid
    )
    
    assert result["success"] is False
    assert "name" in result["error"]  # Validation error
    assert result["error_type"] == "PRODUCT"
```

### Network Error Resilience
```python
async def test_retry_on_transient_failure(mcp_client, monkeypatch):
    """Test that transient errors are retried."""
    # This would require network simulation
    # For now, test via mock
    pass
```

## Test Organization Best Practices

### File Size Target
- **Each file:** ≤300 lines (encourages focused concerns)
- **Each test class:** ≤10 tests per class
- **Each test:** ≤30 lines (focus on single scenario)

### Class Organization
```python
class TestOrganizationManagement:
    """All organization CRUD and management tests."""
    
    # Create tests
    async def test_create_organization_minimal(self, mcp_client):
        """Create org with minimal data."""
        ...
    
    async def test_create_organization_full(self, mcp_client):
        """Create org with full metadata."""
        ...
    
    # Read tests
    async def test_read_organization_by_id(self, mcp_client):
        """Read org by UUID."""
        ...
    
    async def test_read_organization_fuzzy(self, mcp_client):
        """Read org by fuzzy name match."""
        ...
    
    # ... Update, Delete, List tests follow
```

### Docstring Convention
```python
async def test_create_organization_full(self, mcp_client):
    """Create organization with full metadata.
    
    Validates:
    - Name is stored correctly
    - Description is preserved
    - Type is set
    - created_by set to authenticated user
    - created_at timestamp is set
    
    Expected behavior: Success
    """
    ...
```

---

**Last Updated:** 2025-11-14 (Implementation Strategy)
