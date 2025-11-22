# Test Patterns & Implementation Guide

## Pattern 1: Canonical Test File Organization

### Problem
Test files with non-canonical names (speed/variant-based) are hard to discover and maintain.

### Solution
Use concern-based naming that describes "what's tested":

```python
# ✅ GOOD: test_entity_crud.py
class TestEntityCreation:
    async def test_create_organization(self, end_to_end_client):
        """Create organization with metadata."""
        ...

class TestEntityUpdate:
    async def test_update_project_name(self, end_to_end_client):
        """Update project name."""
        ...

# ❌ BAD: test_entity_fast.py, test_entity_unit.py, test_entity_v2.py
```

### Benefits
- File name immediately tells what's tested
- Detects duplication (similar names = consolidate)
- Enables automation (tools can understand structure)
- Reduces clutter (no `_old`, `_new`, `_fast`, `_slow` suffixes)

## Pattern 2: Fixture Parametrization

### Problem
Creating separate test files for unit/integration/e2e variants causes code duplication.

### Solution
Use `@pytest.fixture(params=[...])` to parametrize test variants:

```python
# ✅ GOOD: One file, multiple variants
@pytest.fixture(params=["unit", "integration", "e2e"])
def mcp_client(request):
    """Parametrized client fixture."""
    if request.param == "unit":
        return InMemoryMcpClient()
    elif request.param == "integration":
        return HttpMcpClient("http://localhost:8000")
    elif request.param == "e2e":
        return HttpMcpClient("https://mcpdev.atoms.tech")

async def test_entity_creation(mcp_client):
    """Runs 3 times automatically: unit, integration, e2e."""
    result = await mcp_client.call_tool("entity_tool", {...})
    assert result.success

# ❌ BAD: Three separate files with identical test logic
# test_entity_unit.py, test_entity_integration.py, test_entity_e2e.py
```

### Benefits
- Single source of truth (one test file)
- Same logic runs across variants automatically
- Change test once, all variants update
- No code duplication

## Pattern 3: Test Markers for Categorization

### Problem
Using file names to categorize tests (speed, type, etc.) creates clutter.

### Solution
Use pytest markers for categorization:

```python
# ✅ GOOD: Use markers
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.story("User can create organizations")
async def test_create_organization(end_to_end_client):
    """Create organization with full workflow."""
    ...

# ❌ BAD: Use file names
# test_entity_slow.py, test_entity_fast.py, test_entity_smoke.py
```

### Marker Categories

| Marker | Purpose | Example |
|--------|---------|---------|
| `@pytest.mark.e2e` | End-to-end test | Full workflow test |
| `@pytest.mark.unit` | Unit test | In-memory test |
| `@pytest.mark.integration` | Integration test | HTTP client test |
| `@pytest.mark.slow` | Slow test (>5s) | Performance test |
| `@pytest.mark.flaky` | Potentially flaky | Retry logic test |
| `@pytest.mark.story` | User story mapping | Feature test |
| `@pytest.mark.security` | Security test | Permission test |

## Pattern 4: Deterministic Tests

### Problem
Tests with timing dependencies, randomness, or race conditions are flaky.

### Solution
Make tests deterministic:

```python
# ✅ GOOD: Deterministic
@pytest.mark.asyncio
async def test_workflow_with_retry(end_to_end_client):
    """Workflow retries on transient failure."""
    # First create an organization to ensure valid context
    org_result = await end_to_end_client.entity_create(
        "organization",
        {"name": f"Retry Org {uuid.uuid4().hex[:4]}"}
    )
    
    # Only proceed if organization creation succeeded
    if org_result.get("success"):
        org_id = org_result["data"]["id"]
        result = await end_to_end_client.entity_create(
            "project",
            {"name": f"Project {uuid.uuid4().hex[:4]}", "organization_id": org_id}
        )
        assert "success" in result or "error" in result

# ❌ BAD: Flaky (timing dependency)
async def test_workflow_with_retry(end_to_end_client):
    """Workflow retries on transient failure."""
    # Random delay causes flakiness
    await asyncio.sleep(random.random() * 5)
    result = await end_to_end_client.entity_create(
        "project",
        {"name": f"Project {uuid.uuid4().hex[:4]}", "organization_id": str(uuid.uuid4())}
    )
    assert result["success"]  # Fails if org doesn't exist
```

### Benefits
- Tests pass consistently
- No retry logic needed
- Easier to debug failures
- Faster CI/CD

## Pattern 5: Test Consolidation

### Problem
Multiple test files with overlapping concerns cause duplication and maintenance burden.

### Solution
Consolidate files with same component/tool focus:

```
Before (duplication):
- test_auth.py (10 tests)
- test_auth_patterns.py (5 tests)
- test_error_recovery.py (8 tests)
- test_resilience.py (10 tests)
- test_concurrent_workflows.py (6 tests)
- test_project_workflow.py (7 tests)
- test_workflow_automation.py (11 tests)

After (consolidated):
- test_auth_integration.py (15 tests)
- test_resilience.py (18 tests)
- test_workflow_automation.py (24 tests)
```

### Benefits
- Reduced file count (7 → 3)
- Eliminated duplication
- Easier to maintain
- Better organization

## Pattern 6: Mock vs Real Services

### Problem
Deciding when to mock vs use real services.

### Solution
Use this decision tree:

```
Is it a unit test?
├─ YES → Mock all external services
│        (database, auth, cache, HTTP)
└─ NO → Is it an integration test?
       ├─ YES → Use real services (local)
       │        (Supabase, Redis, HTTP)
       └─ NO → Is it an E2E test?
              ├─ YES → Use real deployment
              │        (production-like setup)
              └─ NO → Use mocks
```

### Example

```python
# Unit test: Mock everything
@pytest.mark.unit
async def test_entity_creation_unit(mock_database):
    """Unit test with mocked database."""
    mock_database.create.return_value = {"id": "123"}
    result = await entity_service.create(...)
    assert result["id"] == "123"

# Integration test: Real database, mock auth
@pytest.mark.integration
async def test_entity_creation_integration(real_database, mock_auth):
    """Integration test with real database."""
    result = await entity_service.create(...)
    assert result["id"] in real_database.list()

# E2E test: Real everything
@pytest.mark.e2e
async def test_entity_creation_e2e(end_to_end_client):
    """E2E test with real deployment."""
    result = await end_to_end_client.call_tool("entity_tool", {...})
    assert result.success
```

## Pattern 7: Test Cleanup

### Problem
Tests leave behind data that affects subsequent tests.

### Solution
Use fixtures for cleanup:

```python
@pytest.fixture
async def cleanup_entities(end_to_end_client):
    """Fixture for test cleanup."""
    entities_to_cleanup = []
    
    def track_entity(entity_type, entity_id):
        entities_to_cleanup.append((entity_type, entity_id))
    
    yield track_entity
    
    # Cleanup after test
    for entity_type, entity_id in entities_to_cleanup:
        try:
            await end_to_end_client.call_tool(
                "entity_tool",
                {
                    "operation": "delete",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "soft_delete": True,
                },
            )
        except Exception:
            pass  # Ignore cleanup errors

async def test_create_organization(cleanup_entities):
    """Create organization and cleanup after test."""
    result = await end_to_end_client.entity_create(
        "organization",
        {"name": "Test Org"}
    )
    cleanup_entities("organization", result["id"])
    assert result.success
```

## Consolidation Decision Tree

When multiple test files have overlapping concerns:

| Question | Answer | Action |
|----------|--------|--------|
| Same component/tool? | Yes | Merge into single canonical file |
| Different clients? | Yes | Use `@pytest.fixture(params=[...])` |
| Different test types? | Yes | Use `@pytest.mark.slow`, `@pytest.mark.smoke` |
| Different subsystems? | Yes | Keep separate, ensure canonical names |
| Different subsystems? | No | Merge; duplicate concerns |

