# Testing Strategy: Approach, Execution, Markers, Fixtures

**Date:** November 14, 2025  
**Focus:** How tests will be organized, executed, and categorized

## Test Execution Workflow

### Local Development
```bash
# Quick smoke tests (unit only, <1min)
python cli.py test run --scope unit -m smoke

# Full suite (all layers, ~5min)
python cli.py test run --scope unit,integration,e2e

# E2E only against deployment
python cli.py test run --scope e2e
```

### CI/CD Pipeline
```bash
# Run by layer in parallel
pytest tests/unit -m "not slow" -n auto         # Parallel unit tests
pytest tests/integration -n auto                 # Parallel integration tests
pytest tests/e2e -m "not slow" -n auto          # Parallel e2e tests

# Performance tests run separately
pytest tests/ -m slow --timeout=30

# Full coverage report
pytest --cov=. --cov-report=html tests/
```

## Test Markers Reference

### Core Markers (Test Type/Scope)

| Marker | Usage | Execution | Notes |
|--------|-------|-----------|-------|
| `@pytest.mark.unit` | In-memory client | Fast (<100ms) | Mocks all services |
| `@pytest.mark.integration` | Local HTTP server | Medium (1-5s) | Real services locally |
| `@pytest.mark.e2e` | Real deployment | Slow (5-30s) | Full production stack |

### Speed Markers

| Marker | Threshold | Usage | Run Command |
|--------|-----------|-------|------------|
| `@pytest.mark.smoke` | <100ms | Quick sanity checks | `pytest -m smoke` |
| `@pytest.mark.slow` | >5s | Slow operations | `pytest -m slow` (separate) |

### Feature Markers

| Marker | Coverage | Example |
|--------|----------|---------|
| `@pytest.mark.entity` | entity_tool operations | test_entity_crud.py |
| `@pytest.mark.workspace` | workspace_tool ops | test_workspace_navigation.py |
| `@pytest.mark.relationship` | relationship_tool ops | test_entity_relationships.py |
| `@pytest.mark.query` | data_query operations | test_search_and_discovery.py |
| `@pytest.mark.workflow` | workflow_execute ops | test_workflow_automation.py |
| `@pytest.mark.auth` | Authentication flows | test_auth_integration.py |

### Service Requirement Markers

| Marker | Service | Skip If Unavailable |
|--------|---------|-------------------|
| `@pytest.mark.requires_db` | Supabase DB | No DB connection |
| `@pytest.mark.requires_auth` | Auth provider | Auth not configured |
| `@pytest.mark.requires_cache` | Upstash Redis | Cache unavailable |

## Fixture Hierarchy

### Session-Level Fixtures (Shared Across Tests)
```python
@pytest.fixture(scope="session")
def e2e_auth_token():
    """Get Supabase JWT once for entire test session."""
    # Avoids rate limiting, re-authentication overhead
    return jwt_token

@pytest.fixture(scope="session")
def shared_http_client(e2e_auth_token):
    """Shared HTTP client for E2E tests."""
    # Single connection pool, efficient reuse
    return httpx.AsyncClient(headers={"Authorization": f"Bearer {e2e_auth_token}"})
```

### Function-Level Fixtures (Fresh Per Test)
```python
@pytest.fixture
async def isolated_org(mcp_client):
    """Create fresh org for each test."""
    # Ensures test isolation
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": f"Org {uuid.uuid4().hex[:8]}"}
    )
    
    yield result["data"]["id"]
    
    # Cleanup after test
    await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=result["data"]["id"],
        operation="delete"
    )
```

### Parametrized Fixtures (Multiple Variants)
```python
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """MCP client in three variants (runs test 3x)."""
    # See 04_IMPLEMENTATION_STRATEGY.md for details
    if request.param == "unit":
        return InMemoryMcpClient()
    # ... other variants
```

## How Parametrization Works (Example)

**Test Definition:**
```python
@pytest.mark.asyncio
async def test_create_organization(mcp_client):
    """This test runs 3 times automatically."""
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": "Test Org"}
    )
    assert result["success"]
```

**Execution:**
```
test_create_organization[unit]         ✅ ~10ms (mock)
test_create_organization[integration]  ✅ ~200ms (real DB)
test_create_organization[e2e]          ✅ ~1000ms (deployment)
```

**Result:**
- Same test code
- Three execution contexts
- Three coverage points
- No duplication

## Test Consolidation Rules

### Rule 1: One File Per Concern, Not Per Speed
❌ **Bad:** Separate files for variants
```
test_entity_unit.py
test_entity_integration.py
test_entity_e2e.py
```

✅ **Good:** One file, parametrized variants
```
test_entity_crud.py  (with @pytest.fixture(params=[...]))
```

### Rule 2: No Temporal Suffixes
❌ **Bad:** Temporal metadata in names
```
test_entity_old.py
test_entity_new.py
test_entity_final.py
test_entity_v2.py
```

✅ **Good:** Canonical names describing content
```
test_entity_crud.py
```

### Rule 3: No Speed Suffixes (Use Markers Instead)
❌ **Bad:** Speed in file names
```
test_entity_fast.py
test_entity_slow.py
```

✅ **Good:** Speed in markers
```
@pytest.mark.smoke  # Fast
@pytest.mark.slow   # Slow
```

### Rule 4: No Variant Suffixes (Use Fixtures Instead)
❌ **Bad:** Variant in file names
```
test_entity_mock.py
test_entity_with_real_db.py
```

✅ **Good:** Variants in fixtures
```
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    ...
```

## Test Execution Patterns

### Pattern 1: Simple CRUD Test
```python
@pytest.mark.asyncio
@pytest.mark.entity
async def test_create_organization(mcp_client):
    """Create organization and verify response."""
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": "Acme Corp"}
    )
    
    assert result["success"] is True
    assert result["data"]["name"] == "Acme Corp"
    assert "id" in result["data"]
```

### Pattern 2: Full Lifecycle Test
```python
@pytest.mark.asyncio
@pytest.mark.entity
async def test_organization_lifecycle(mcp_client):
    """Test org create, read, update, delete."""
    # Create
    create = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": "Lifecycle Org"}
    )
    org_id = create["data"]["id"]
    
    # Read
    read = await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=org_id,
        operation="read"
    )
    assert read["data"]["name"] == "Lifecycle Org"
    
    # Update
    update = await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=org_id,
        operation="update",
        data={"name": "Updated Org"}
    )
    assert update["data"]["name"] == "Updated Org"
    
    # Delete
    delete = await mcp_client.entity_tool(
        entity_type="organization",
        entity_id=org_id,
        operation="delete"
    )
    assert delete["success"]
```

### Pattern 3: RLS/Access Control Test
```python
@pytest.mark.asyncio
@pytest.mark.auth
@pytest.mark.requires_auth
async def test_rls_prevents_unauthorized_access(mcp_client, other_user_token):
    """Verify RLS prevents cross-user access."""
    # Create as user A
    org = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": "Private Org"}
    )
    org_id = org["data"]["id"]
    
    # Try to read as user B
    other_client = get_authenticated_client(other_user_token)
    result = await other_client.entity_tool(
        entity_type="organization",
        entity_id=org_id,
        operation="read"
    )
    
    # Should be denied
    assert result["success"] is False
    assert result["error_type"] in ["INFRASTRUCTURE", "AUTHORIZATION"]
```

### Pattern 4: Error Handling Test
```python
@pytest.mark.asyncio
@pytest.mark.entity
async def test_create_with_validation_failure(mcp_client):
    """Creating with invalid data should fail with validation error."""
    result = await mcp_client.entity_tool(
        entity_type="organization",
        operation="create",
        data={"name": ""}  # Empty name not allowed
    )
    
    assert result["success"] is False
    assert "name" in result["error"]
    assert result["error_type"] == "PRODUCT"  # Validation error
```

### Pattern 5: Performance Baseline Test
```python
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.performance
async def test_batch_create_1000_performance(mcp_client, perf_tracker):
    """Verify batch create performance baseline."""
    entities = [{"name": f"Entity {i}"} for i in range(1000)]
    
    async with perf_tracker("batch_create_1000"):
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="create",
            batch=entities
        )
    
    assert result["success"]
    assert len(result["data"]) == 1000
    
    # Performance assertions (test framework will measure)
    # Unit: <1s
    # Integration: <10s
    # E2E: <30s
```

## Test Organization Standards

### File Structure
```
tests/
├── conftest.py                          # Root fixtures
├── unit/
│   ├── conftest.py                      # Unit-specific fixtures
│   ├── mocks/                           # Mock clients
│   └── ...
├── integration/
│   ├── conftest.py                      # Integration fixtures
│   ├── test_auth_integration.py
│   └── ...
├── e2e/
│   ├── conftest.py                      # E2E fixtures
│   ├── test_organization_management.py
│   ├── test_project_management.py
│   └── ... (11 E2E test files)
└── fixtures/                            # Shared fixture data
    └── sample_data.py
```

### Class Organization
```python
class TestOrganizationManagement:
    """All organization management tests."""
    
    # Organize by operation type
    class TestCreate:
        """Create operation tests."""
        async def test_minimal_data(self, mcp_client):
            ...
        async def test_full_metadata(self, mcp_client):
            ...
    
    class TestRead:
        """Read operation tests."""
        async def test_by_id(self, mcp_client):
            ...
        async def test_fuzzy_match(self, mcp_client):
            ...
    
    # Or organize flat if <10 tests
    async def test_create(self, mcp_client):
        ...
    async def test_read(self, mcp_client):
        ...
```

## Running Tests by Marker

### Run only unit tests
```bash
pytest tests/ -m unit
```

### Run only smoke tests
```bash
pytest tests/ -m smoke
```

### Run entity tests only
```bash
pytest tests/ -m entity
```

### Run everything except slow
```bash
pytest tests/ -m "not slow"
```

### Run auth tests only
```bash
pytest tests/ -m auth
```

### Run performance tests (separate, longer timeout)
```bash
pytest tests/ -m slow --timeout=60
```

## Expected Test Execution Times

### By Variant (Per Test)
| Variant | Time | Count | Total |
|---------|------|-------|-------|
| Unit (mock) | ~10ms | 172 | ~2s |
| Integration (local) | ~300ms | 172 | ~50s |
| E2E (mcpdev) | ~1000ms | 172 | ~3min |
| **Single Run** | — | 172×3 | **~3.5min** |

### By Scope
| Scope | Files | Tests | Time |
|-------|-------|-------|------|
| Unit | - | - | <1min |
| Unit + Integration | - | - | ~1.5min |
| Unit + Integration + E2E | 15 | 172×3 | ~3.5min |
| E2E only (mcpdev) | 11 | 172 | ~3min |

### CI/CD Optimization
```
Run in parallel:
- Unit tests: 30s
- Integration tests: 1m (parallel batches)
- E2E tests: 2m (parallel batches)

Sequential:
- Performance tests: 2m (marked slow)
- Coverage reporting: 30s

Total CI time: ~4 minutes (with parallelization)
```

## Handling Test Failures

### Classification
```
INFRASTRUCTURE
├─ Database connection failed
├─ Network timeout
├─ Auth provider unavailable
└─ Cache service down

PRODUCT
├─ Validation error
├─ Business logic failure
├─ Authorization denial
└─ Data integrity violation

TEST_DATA
├─ Fixture setup failed
├─ Test isolation broken
└─ Cleanup incomplete

ASSERTION
├─ Expected value mismatch
├─ Unexpected exception
└─ Assertion error
```

### Recovery Strategy
```
INFRASTRUCTURE failures
→ Retry with backoff
→ Skip if persistent
→ Alert infrastructure team

PRODUCT failures
→ Debug (unit vs integration gap)
→ Fix code or test
→ No retry

TEST_DATA failures
→ Fix fixture isolation
→ Improve cleanup
→ Use unique test data

ASSERTION failures
→ Fix test expectation
→ Update test logic
→ Ensure reproducible
```

## Continuous Improvement

### Metrics to Track
- ✅ Test pass rate (target: 100%)
- ✅ Execution time per test (alert if >2× baseline)
- ✅ Flaky tests (should be 0)
- ✅ Coverage trend (should increase)
- ✅ User story coverage (track 0→48)

### Regular Review (Weekly)
1. Identify slow tests (>5s)
2. Identify flaky tests (retry rate >5%)
3. Review new test patterns
4. Update benchmarks if needed
5. Refactor consolidation candidates

---

**Last Updated:** 2025-11-14 (Testing Strategy)
