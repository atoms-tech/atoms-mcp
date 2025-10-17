# Phase 3 Test Suite Implementation Quick Start Guide

## Immediate Action Items for Parallel Execution

This guide provides concrete starting points for multiple agents to begin implementing the Phase 3 test suite in parallel.

## Agent Assignment Matrix

### Agent 1: Schema Validation Tests
**Focus**: Pydantic model sync, field type validation, constraints

**Start with**:
```bash
# Create directory structure
mkdir -p tests/phase3/schema_validation
cd tests/phase3/schema_validation

# Create initial test files
touch __init__.py
touch test_pydantic_sync.py
touch test_field_types.py
touch test_constraints.py
```

**First test to implement**:
```python
# test_pydantic_sync.py
async def test_all_tables_have_models():
    """Verify all DB tables have Pydantic models."""
    # Start here - compare database tables with local models
```

**Key files to reference**:
- `/schemas/__init__.py` - Pydantic models
- `/scripts/sync_schema.py` - Schema sync logic
- `/tests/test_schema_sync.py` - Existing schema tests

---

### Agent 2: RLS Policy Tests
**Focus**: Policy enforcement, access control matrix, edge cases

**Start with**:
```bash
# Create RLS test structure
mkdir -p tests/phase3/rls_policies
cd tests/phase3/rls_policies

# Create test files
touch __init__.py
touch test_policy_enforcement.py
touch test_access_control.py
```

**First test to implement**:
```python
# test_policy_enforcement.py
async def test_organization_access_control():
    """Test organization-level RLS enforcement."""
    # Start here - test owner/admin/member access patterns
```

**Key files to reference**:
- `/schemas/rls.py` - RLS policy implementations
- `/tests/unit/test_rls_policies.py` - Existing RLS tests
- `/schemas/rls_policies.md` - RLS documentation

---

### Agent 3: Migration Tests
**Focus**: Migration runner, rollback, versioning

**Start with**:
```bash
# Create migration test structure
mkdir -p tests/phase3/migrations
cd tests/phase3/migrations

# Create test files
touch __init__.py
touch test_migration_runner.py
touch test_rollback.py
```

**First test to implement**:
```python
# test_migration_runner.py
async def test_migration_execution():
    """Test migration applies successfully."""
    # Start here - create and execute test migration
```

**Key files to reference**:
- `/schemas/schema_version.py` - Version tracking
- Database migration patterns from Supabase docs

---

### Agent 4: Integration Tests
**Focus**: End-to-end workflows, cascade operations

**Start with**:
```bash
# Create integration test structure
mkdir -p tests/phase3/integration
cd tests/phase3/integration

# Create test files
touch __init__.py
touch test_end_to_end.py
touch test_cascade_flows.py
```

**First test to implement**:
```python
# test_end_to_end.py
async def test_full_sync_workflow():
    """Test complete schema sync workflow."""
    # Start here - implement full sync cycle
```

**Key files to reference**:
- `/tests/framework/harmful.py` - @harmful decorator
- `/tests/framework/pytest_atoms_modes.py` - Test modes
- Existing integration patterns in `/tests/`

---

### Agent 5: Performance Tests
**Focus**: Validation performance, RLS overhead, benchmarks

**Start with**:
```bash
# Create performance test structure
mkdir -p tests/phase3/performance
cd tests/phase3/performance

# Create test files
touch __init__.py
touch test_validation_perf.py
touch benchmarks.py
```

**First test to implement**:
```python
# test_validation_perf.py
async def test_bulk_validation_speed():
    """Test validation speed for 1000 entities."""
    # Start here - benchmark validation performance
```

**Key files to reference**:
- `/schemas/validation.py` - Validation logic
- Performance patterns from existing tests

---

## Shared Fixtures Setup

### All Agents: Create shared fixtures first

```python
# tests/phase3/conftest.py
"""Shared fixtures for Phase 3 tests."""

import pytest
from scripts.sync_schema import SchemaSync

@pytest.fixture
async def schema_sync():
    """Shared schema sync instance."""
    sync = SchemaSync(project_id="test-project")
    await sync.connect()
    yield sync
    await sync.disconnect()

@pytest.fixture
def mock_db_schema():
    """Mock database schema for testing."""
    return {
        "tables": {
            "organizations": {
                "columns": [
                    {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                    {"column_name": "name", "data_type": "text", "is_nullable": "NO"},
                ]
            }
        },
        "enums": {
            "organization_type": ["personal", "team", "enterprise"]
        }
    }
```

## Coordination Points

### 1. Naming Conventions
- Test functions: `test_<what>_<condition>`
- Fixtures: `<resource>_<modifier>` (e.g., `user_context`, `mock_db_schema`)
- Files: `test_<feature>.py`

### 2. Marker Usage
```python
@pytest.mark.hot     # Real database operations
@pytest.mark.cold    # Mocked operations
@pytest.mark.dry     # Pure validation
@pytest.mark.performance  # Performance tests
@harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)  # Auto cleanup
```

### 3. Import Structure
```python
# Standard imports
import pytest
from typing import Type, Any

# Framework imports
from tests.framework.harmful import harmful, CleanupStrategy
from tests.framework.test_modes import TestMode

# Schema imports
from schemas import OrganizationRow, ProjectRow
from schemas.rls import PolicyValidator

# Script imports
from scripts.sync_schema import SchemaSync
```

## Quick Test Execution

### Run your tests immediately:
```bash
# Run all Phase 3 tests
pytest tests/phase3/ -v

# Run specific agent's tests
pytest tests/phase3/schema_validation/ -v  # Agent 1
pytest tests/phase3/rls_policies/ -v       # Agent 2
pytest tests/phase3/migrations/ -v         # Agent 3
pytest tests/phase3/integration/ -v        # Agent 4
pytest tests/phase3/performance/ -v        # Agent 5

# Run with specific mode
pytest tests/phase3/ --mode hot -v
pytest tests/phase3/ --mode cold -v
pytest tests/phase3/ --mode dry -v
```

## Initial Test Templates

### Template 1: Basic Test Structure
```python
import pytest
from tests.framework.harmful import harmful, CleanupStrategy

class TestFeatureName:
    """Test suite for <feature>."""

    @pytest.fixture
    async def setup_data(self):
        """Set up test data."""
        # Setup
        yield data
        # Teardown (if not using @harmful)

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_feature_behavior(self, setup_data):
        """Test <specific behavior>."""
        # Arrange
        data = setup_data

        # Act
        result = await perform_action(data)

        # Assert
        assert result.success, f"Failed: {result.error}"
```

### Template 2: Parametrized Test
```python
@pytest.mark.parametrize("input,expected", [
    ("valid_input", True),
    ("invalid_input", False),
    ("edge_case", True),
])
async def test_validation_cases(self, input, expected):
    """Test various validation scenarios."""
    result = validator.validate(input)
    assert result == expected
```

### Template 3: Performance Test
```python
import time

@pytest.mark.performance
async def test_operation_performance(self, performance_fixtures):
    """Test operation completes within time limit."""
    entities = performance_fixtures.generate_entities(1000)

    start = time.perf_counter()
    for entity in entities:
        await process_entity(entity)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"Too slow: {elapsed:.2f}s"
    print(f"Throughput: {len(entities)/elapsed:.0f} ops/sec")
```

## Common Gotchas to Avoid

1. **Always use absolute paths** in test files
2. **Clean up resources** using @harmful or manual cleanup
3. **Mock external dependencies** in cold/dry modes
4. **Use proper async/await** for all database operations
5. **Check test isolation** - tests should not depend on each other

## Progress Tracking

### Daily Sync Points:
1. Morning: Share test count and coverage metrics
2. Afternoon: Resolve any blocking issues
3. EOD: Commit working tests, even if incomplete

### Success Metrics:
- [ ] 30+ tests per agent minimum
- [ ] 80%+ code coverage per module
- [ ] All tests pass in all modes (hot/cold/dry)
- [ ] Performance benchmarks established
- [ ] CI/CD integration working

## Need Help?

Reference these key files:
- Test framework: `/tests/framework/`
- Existing examples: `/tests/unit/`, `/tests/test_*.py`
- Schema definitions: `/schemas/`
- Sync logic: `/scripts/sync_schema.py`

Start implementing immediately - even simple tests provide value!