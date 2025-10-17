# Phase 3 Schema Sync Verification Test Suite - Comprehensive Design

## Executive Summary

This document presents a comprehensive test suite design for Phase 3 schema synchronization verification. The suite covers schema validation, RLS policy testing, migration verification, integration testing, and performance benchmarking. It leverages the existing test framework's @harmful decorator, test modes (hot/cold/dry), and provides a parallelizable execution strategy.

## Test Suite Architecture

### 1. Directory Structure

```
tests/
├── phase3/
│   ├── __init__.py
│   ├── conftest.py                    # Phase 3 specific fixtures
│   │
│   ├── schema_validation/
│   │   ├── __init__.py
│   │   ├── test_pydantic_sync.py      # Pydantic model validation
│   │   ├── test_field_types.py        # Field type mapping tests
│   │   ├── test_constraints.py        # Database constraints validation
│   │   ├── test_drift_detection.py    # Schema drift detection
│   │   └── test_enum_sync.py          # Enum synchronization
│   │
│   ├── rls_policies/
│   │   ├── __init__.py
│   │   ├── test_policy_enforcement.py  # RLS enforcement tests
│   │   ├── test_access_control.py     # Access control matrix
│   │   ├── test_edge_cases.py         # Edge case scenarios
│   │   ├── test_policy_migration.py   # Policy migration tests
│   │   └── test_policy_performance.py # RLS performance impact
│   │
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── test_migration_runner.py   # Migration execution tests
│   │   ├── test_rollback.py          # Rollback capability tests
│   │   ├── test_versioning.py        # Schema version tracking
│   │   ├── test_idempotency.py       # Migration idempotency
│   │   └── test_migration_order.py    # Dependency ordering
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_end_to_end.py        # Full workflow tests
│   │   ├── test_client_server.py     # Client-server validation
│   │   ├── test_cascade_flows.py     # Cascade operation tests
│   │   ├── test_transaction_flows.py  # Transaction boundary tests
│   │   └── test_sync_workflow.py     # Schema sync workflow
│   │
│   ├── performance/
│   │   ├── __init__.py
│   │   ├── test_validation_perf.py    # Validation performance
│   │   ├── test_rls_perf.py          # RLS query performance
│   │   ├── test_migration_perf.py    # Migration execution time
│   │   ├── test_bulk_operations.py   # Bulk operation performance
│   │   └── benchmarks.py              # Performance benchmarks
│   │
│   └── fixtures/
│       ├── __init__.py
│       ├── schema_fixtures.py        # Schema test data
│       ├── migration_fixtures.py     # Migration fixtures
│       ├── rls_fixtures.py          # RLS test scenarios
│       └── performance_fixtures.py   # Performance test data
```

## 2. Test Categories and Implementation

### 2.1 Schema Validation Tests

#### Test Count: ~45 tests
#### Coverage Target: 95%

```python
# tests/phase3/schema_validation/test_pydantic_sync.py
"""Verify Pydantic models match Supabase schema exactly."""

import pytest
from typing import Type, Any
from pydantic import BaseModel
from schemas.generated import OrganizationRow, ProjectRow, DocumentRow
from scripts.sync_schema import SchemaSync
from tests.framework.harmful import harmful, CleanupStrategy


class TestPydanticModelSync:
    """Test suite for Pydantic model synchronization."""

    @pytest.fixture
    async def schema_sync(self):
        """Create SchemaSync instance with test database."""
        sync = SchemaSync(project_id="test-project")
        await sync.connect()
        yield sync
        await sync.disconnect()

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.NONE)
    async def test_all_tables_have_models(self, schema_sync):
        """Verify all database tables have corresponding Pydantic models."""
        db_schema = await schema_sync.get_supabase_schema()
        local_models = schema_sync.get_local_models()

        missing_models = []
        for table_name in db_schema["tables"]:
            model_name = schema_sync._table_name_to_class(table_name)
            if model_name not in local_models:
                missing_models.append(table_name)

        assert not missing_models, f"Missing Pydantic models for tables: {missing_models}"

    @pytest.mark.cold
    @pytest.mark.parametrize("model_class,table_name", [
        (OrganizationRow, "organizations"),
        (ProjectRow, "projects"),
        (DocumentRow, "documents"),
    ])
    async def test_model_field_types(self, schema_sync, model_class: Type[BaseModel], table_name: str):
        """Verify model field types match database column types."""
        db_schema = await schema_sync.get_supabase_schema()
        table_schema = db_schema["tables"][table_name]

        model_fields = model_class.__fields__

        for column in table_schema["columns"]:
            column_name = column["column_name"]
            if column_name in model_fields:
                field = model_fields[column_name]
                expected_type = schema_sync._sql_to_python_type(column)

                # Handle Optional types
                actual_type = str(field.annotation)
                assert expected_type in actual_type, (
                    f"Field {column_name} type mismatch: "
                    f"expected {expected_type}, got {actual_type}"
                )

    @pytest.mark.hot
    async def test_required_fields_validation(self, schema_sync):
        """Verify required fields are properly marked."""
        db_schema = await schema_sync.get_supabase_schema()

        for table_name, table_schema in db_schema["tables"].items():
            model_class = schema_sync.get_model_class(table_name)
            if not model_class:
                continue

            for column in table_schema["columns"]:
                if column["is_nullable"] == "NO":
                    field_name = column["column_name"]
                    if field_name in model_class.__fields__:
                        field = model_class.__fields__[field_name]
                        assert field.required or field.default is not None, (
                            f"Non-nullable field {field_name} in {table_name} "
                            f"should be required or have default"
                        )


class TestSchemaConstraints:
    """Test database constraints are reflected in models."""

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_unique_constraints(self, schema_sync):
        """Test unique constraints are enforced."""
        # Implementation here
        pass

    @pytest.mark.cold
    async def test_foreign_key_constraints(self, schema_sync):
        """Test foreign key relationships."""
        # Implementation here
        pass

    @pytest.mark.hot
    async def test_check_constraints(self, schema_sync):
        """Test check constraints validation."""
        # Implementation here
        pass


class TestDriftDetection:
    """Test schema drift detection capabilities."""

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.TRANSACTION_ROLLBACK)
    async def test_detect_new_columns(self, schema_sync, mock_db_schema):
        """Test detection of new database columns."""
        schema_sync.db_schema = mock_db_schema
        differences = schema_sync.compare_schemas()

        new_columns = [
            d for d in differences
            if d["type"] == "column" and d["change"] == "added"
        ]

        assert len(new_columns) > 0, "Should detect new columns"

    @pytest.mark.dry
    async def test_detect_type_changes(self, schema_sync):
        """Test detection of column type changes."""
        # Implementation here
        pass

    @pytest.mark.cold
    async def test_severity_classification(self, schema_sync):
        """Test proper severity assignment to schema changes."""
        # Implementation here
        pass
```

### 2.2 RLS Policy Tests

#### Test Count: ~35 tests
#### Coverage Target: 90%

```python
# tests/phase3/rls_policies/test_policy_enforcement.py
"""Test Row-Level Security policy enforcement."""

import pytest
from schemas.rls import PolicyValidator, PermissionDeniedError
from tests.framework.harmful import harmful, CleanupStrategy
from tests.framework.test_modes import TestMode


class TestRLSEnforcement:
    """Test RLS policy enforcement across entities."""

    @pytest.fixture
    async def policy_validator(self, user_context, db_adapter):
        """Create policy validator with user context."""
        return PolicyValidator(user_context.id, db_adapter)

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_organization_access_control(self, policy_validator, test_org):
        """Test organization-level access control."""
        # Owner should have full access
        can_read = await policy_validator.can_select("organizations", test_org)
        assert can_read, "Owner should be able to read organization"

        can_update = await policy_validator.can_update(
            "organizations",
            test_org,
            {"name": "Updated Name"}
        )
        assert can_update, "Owner should be able to update organization"

    @pytest.mark.cold
    @pytest.mark.parametrize("role,can_read,can_write", [
        ("owner", True, True),
        ("admin", True, True),
        ("member", True, False),
        ("viewer", True, False),
        (None, False, False),
    ])
    async def test_project_role_matrix(
        self, policy_validator, role, can_read, can_write
    ):
        """Test project access based on role matrix."""
        # Set up user role
        await self.setup_user_role(role)

        # Test read access
        result = await policy_validator.can_select("projects", {"id": "test-project"})
        assert result == can_read, f"Role {role} read access mismatch"

        # Test write access
        result = await policy_validator.can_update(
            "projects",
            {"id": "test-project"},
            {"name": "Updated"}
        )
        assert result == can_write, f"Role {role} write access mismatch"

    @pytest.mark.hot
    async def test_cascade_permission_inheritance(self, policy_validator):
        """Test permissions cascade through entity hierarchy."""
        # Implementation here
        pass


class TestRLSEdgeCases:
    """Test edge cases and complex RLS scenarios."""

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_cross_organization_access(self):
        """Test user cannot access resources across organizations."""
        # Implementation here
        pass

    @pytest.mark.cold
    async def test_public_project_access(self):
        """Test public project accessibility."""
        # Implementation here
        pass

    @pytest.mark.dry
    async def test_super_admin_override(self):
        """Test super admin can bypass RLS policies."""
        # Implementation here
        pass
```

### 2.3 Migration Tests

#### Test Count: ~30 tests
#### Coverage Target: 85%

```python
# tests/phase3/migrations/test_migration_runner.py
"""Test database migration execution."""

import pytest
from pathlib import Path
from tests.framework.harmful import harmful, CleanupStrategy


class TestMigrationRunner:
    """Test migration execution and tracking."""

    @pytest.fixture
    async def migration_runner(self):
        """Create migration runner instance."""
        from scripts.migrations import MigrationRunner
        return MigrationRunner()

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.TRANSACTION_ROLLBACK)
    async def test_migration_execution(self, migration_runner, temp_migration):
        """Test migration applies successfully."""
        # Create temporary migration
        migration_file = temp_migration("""
            -- Create test table
            CREATE TABLE IF NOT EXISTS test_migration_table (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Execute migration
        result = await migration_runner.run(migration_file)

        assert result.success, f"Migration failed: {result.error}"
        assert result.applied_at is not None

        # Verify table exists
        table_exists = await migration_runner.check_table_exists("test_migration_table")
        assert table_exists, "Migration table should exist"

    @pytest.mark.cold
    async def test_migration_idempotency(self, migration_runner, temp_migration):
        """Test migrations are idempotent."""
        migration_file = temp_migration("""
            CREATE TABLE IF NOT EXISTS idempotent_test (
                id UUID PRIMARY KEY
            );
        """)

        # Run migration twice
        result1 = await migration_runner.run(migration_file)
        result2 = await migration_runner.run(migration_file)

        assert result1.success and result2.success
        assert result2.skipped, "Second run should be skipped"

    @pytest.mark.hot
    async def test_migration_rollback(self, migration_runner):
        """Test migration rollback capability."""
        # Implementation here
        pass


class TestSchemaVersioning:
    """Test schema version tracking."""

    @pytest.mark.hot
    async def test_version_increment(self):
        """Test version increments on schema change."""
        # Implementation here
        pass

    @pytest.mark.cold
    async def test_version_history(self):
        """Test version history tracking."""
        # Implementation here
        pass
```

### 2.4 Integration Tests

#### Test Count: ~25 tests
#### Coverage Target: 80%

```python
# tests/phase3/integration/test_end_to_end.py
"""End-to-end schema synchronization tests."""

import pytest
from tests.framework.harmful import harmful, CleanupStrategy
from tests.framework.test_modes import TestMode


class TestEndToEndSync:
    """Test complete schema sync workflow."""

    @pytest.mark.hot
    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_full_sync_workflow(self, schema_sync, test_database):
        """Test complete schema synchronization workflow."""
        # 1. Detect drift
        differences = await schema_sync.detect_drift()
        initial_diff_count = len(differences)

        # 2. Generate update code
        if differences:
            update_code = schema_sync.generate_updates(differences)
            assert update_code, "Should generate update code"

        # 3. Apply updates
        result = await schema_sync.apply_updates()
        assert result.success, f"Update failed: {result.error}"

        # 4. Verify sync
        post_differences = await schema_sync.detect_drift()
        assert len(post_differences) < initial_diff_count, (
            "Should have fewer differences after sync"
        )

        # 5. Update version
        version_updated = await schema_sync.update_version()
        assert version_updated, "Version should be updated"

    @pytest.mark.cold
    async def test_client_server_validation(self, client, server):
        """Test validation consistency between client and server."""
        test_data = {
            "name": "Test Entity",
            "type": "invalid_type"  # Should fail validation
        }

        # Client-side validation
        client_errors = client.validate_entity(test_data)

        # Server-side validation
        server_response = await server.create_entity(test_data)

        assert client_errors, "Client should detect validation errors"
        assert not server_response.success, "Server should reject invalid data"
        assert client_errors[0] in server_response.error, (
            "Client and server should report similar errors"
        )
```

### 2.5 Performance Tests

#### Test Count: ~20 tests
#### Coverage Target: 75%

```python
# tests/phase3/performance/test_validation_perf.py
"""Performance tests for schema validation."""

import pytest
import time
from tests.framework.harmful import harmful, CleanupStrategy


class TestValidationPerformance:
    """Test schema validation performance."""

    @pytest.mark.hot
    @pytest.mark.performance
    async def test_bulk_validation_speed(self, schema_validator, performance_fixtures):
        """Test validation speed for bulk operations."""
        entities = performance_fixtures.generate_entities(count=1000)

        start_time = time.perf_counter()

        for entity in entities:
            errors = schema_validator.validate(entity)
            assert not errors, f"Validation failed: {errors}"

        elapsed = time.perf_counter() - start_time

        # Performance assertion: 1000 validations under 1 second
        assert elapsed < 1.0, f"Validation too slow: {elapsed:.2f}s for 1000 entities"

        # Calculate throughput
        throughput = len(entities) / elapsed
        print(f"Validation throughput: {throughput:.0f} entities/second")

    @pytest.mark.cold
    async def test_rls_query_performance(self, db_adapter, user_context):
        """Test RLS doesn't significantly impact query performance."""
        # Baseline: Query without RLS
        start = time.perf_counter()
        await db_adapter.query_raw("SELECT * FROM projects LIMIT 100")
        baseline_time = time.perf_counter() - start

        # With RLS: Query with user context
        start = time.perf_counter()
        await db_adapter.query_with_rls(
            "SELECT * FROM projects LIMIT 100",
            user_context
        )
        rls_time = time.perf_counter() - start

        # RLS overhead should be under 20%
        overhead = (rls_time - baseline_time) / baseline_time
        assert overhead < 0.2, f"RLS overhead too high: {overhead:.0%}"
```

## 3. Test Fixtures and Utilities

### 3.1 Core Fixtures

```python
# tests/phase3/fixtures/schema_fixtures.py
"""Schema-specific test fixtures."""

import pytest
from typing import Dict, Any
from pathlib import Path


@pytest.fixture
def mock_db_schema() -> Dict[str, Any]:
    """Provide mock database schema for testing."""
    return {
        "tables": {
            "organizations": {
                "columns": [
                    {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                    {"column_name": "name", "data_type": "text", "is_nullable": "NO"},
                    {"column_name": "type", "data_type": "USER-DEFINED",
                     "is_nullable": "NO", "udt_name": "organization_type"},
                ]
            },
            "projects": {
                "columns": [
                    {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
                    {"column_name": "name", "data_type": "text", "is_nullable": "NO"},
                    {"column_name": "organization_id", "data_type": "uuid",
                     "is_nullable": "NO"},
                ]
            }
        },
        "enums": {
            "organization_type": ["personal", "team", "enterprise"],
            "project_status": ["active", "archived", "deleted"],
        }
    }


@pytest.fixture
async def test_database(db_adapter):
    """Create isolated test database."""
    # Create test schema
    await db_adapter.execute("""
        CREATE SCHEMA IF NOT EXISTS test_schema;
        SET search_path TO test_schema;
    """)

    yield db_adapter

    # Cleanup
    await db_adapter.execute("DROP SCHEMA test_schema CASCADE;")


@pytest.fixture
def temp_migration(tmp_path):
    """Create temporary migration files."""
    def _create_migration(sql_content: str, name: str = "test_migration"):
        migration_dir = tmp_path / "migrations"
        migration_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{name}.sql"
        filepath = migration_dir / filename

        filepath.write_text(sql_content)
        return filepath

    return _create_migration
```

### 3.2 RLS Test Utilities

```python
# tests/phase3/fixtures/rls_fixtures.py
"""RLS testing utilities and fixtures."""

import pytest
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class UserContext:
    """Test user context for RLS testing."""
    id: str
    email: str
    roles: list[str]
    organizations: list[str]


@pytest.fixture
async def user_contexts():
    """Provide various user contexts for testing."""
    return {
        "owner": UserContext(
            id="owner-123",
            email="owner@test.com",
            roles=["owner"],
            organizations=["org-123"]
        ),
        "admin": UserContext(
            id="admin-456",
            email="admin@test.com",
            roles=["admin"],
            organizations=["org-123"]
        ),
        "member": UserContext(
            id="member-789",
            email="member@test.com",
            roles=["member"],
            organizations=["org-123"]
        ),
        "external": UserContext(
            id="external-000",
            email="external@test.com",
            roles=[],
            organizations=[]
        ),
    }


@pytest.fixture
async def setup_rls_test_data(db_adapter):
    """Set up test data for RLS testing."""
    # Create test organizations
    org_id = await db_adapter.create("organizations", {
        "name": "Test Org",
        "slug": "test-org",
        "type": "team"
    })

    # Create test projects
    project_id = await db_adapter.create("projects", {
        "name": "Test Project",
        "organization_id": org_id
    })

    return {
        "organization_id": org_id,
        "project_id": project_id
    }
```

## 4. Test Execution Strategy

### 4.1 Test Modes Integration

```python
# tests/phase3/conftest.py
"""Phase 3 test configuration."""

import pytest
from tests.framework.test_modes import TestMode, TestModeConfig


def pytest_configure(config):
    """Configure Phase 3 specific test settings."""
    config.addinivalue_line(
        "markers",
        "schema: marks test as schema validation test"
    )
    config.addinivalue_line(
        "markers",
        "rls: marks test as RLS policy test"
    )
    config.addinivalue_line(
        "markers",
        "migration: marks test as migration test"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks test as performance test"
    )


@pytest.fixture
def phase3_mode_config(atoms_test_mode) -> TestModeConfig:
    """Phase 3 specific mode configuration."""
    base_config = TestModeConfig.for_mode(atoms_test_mode)

    # Adjust for Phase 3 requirements
    if atoms_test_mode == TestMode.HOT:
        base_config.max_duration_seconds = 5.0  # Allow longer for DB operations
    elif atoms_test_mode == TestMode.COLD:
        base_config.max_duration_seconds = 1.0
    elif atoms_test_mode == TestMode.DRY:
        base_config.max_duration_seconds = 0.5

    return base_config
```

### 4.2 Parallel Execution Plan

```yaml
# .github/workflows/phase3-tests.yml
name: Phase 3 Schema Sync Tests

on:
  push:
    branches: [main, phase3/*]
  pull_request:
    branches: [main]

jobs:
  test-matrix:
    strategy:
      matrix:
        test-suite: [schema, rls, migration, integration, performance]
        test-mode: [hot, cold, dry]
        exclude:
          # Performance tests only in hot mode
          - test-suite: performance
            test-mode: cold
          - test-suite: performance
            test-mode: dry
          # Migration tests not in dry mode
          - test-suite: migration
            test-mode: dry

    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          uv sync
          uv sync --group dev

      - name: Run ${{ matrix.test-suite }} tests in ${{ matrix.test-mode }} mode
        run: |
          pytest tests/phase3/${{ matrix.test-suite }} \
            --mode ${{ matrix.test-mode }} \
            --mode-strict \
            --mode-validate \
            -v \
            --cov=schemas \
            --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: phase3-${{ matrix.test-suite }}-${{ matrix.test-mode }}
```

### 4.3 Local Development Commands

```bash
# Run all Phase 3 tests
pytest tests/phase3/ -v

# Run specific test suite
pytest tests/phase3/schema_validation/ -v

# Run with specific mode
pytest tests/phase3/ --mode hot -v

# Run with coverage
pytest tests/phase3/ --cov=schemas --cov-report=html

# Run performance tests only
pytest tests/phase3/ -m performance -v

# Run in parallel (requires pytest-xdist)
pytest tests/phase3/ -n auto -v

# Run with harmful tracking
pytest tests/phase3/ --harmful-track --harmful-report
```

## 5. Coverage and Quality Metrics

### 5.1 Expected Coverage

| Component | Target Coverage | Critical Paths |
|-----------|----------------|----------------|
| Schema Validation | 95% | Field type mapping, constraint validation |
| RLS Policies | 90% | Access control matrix, policy enforcement |
| Migrations | 85% | Execution, rollback, versioning |
| Integration | 80% | End-to-end workflows, cascade operations |
| Performance | 75% | Validation speed, RLS overhead |

### 5.2 Test Count Summary

| Category | Unit Tests | Integration Tests | Performance Tests | Total |
|----------|-----------|------------------|-------------------|--------|
| Schema Validation | 30 | 10 | 5 | 45 |
| RLS Policies | 25 | 8 | 2 | 35 |
| Migrations | 20 | 8 | 2 | 30 |
| Integration | 5 | 15 | 5 | 25 |
| Performance | 0 | 5 | 15 | 20 |
| **Total** | **80** | **46** | **29** | **155** |

## 6. Integration with Phase 2 Framework

### 6.1 @harmful Decorator Usage

All tests that create database entities use the @harmful decorator for automatic cleanup:

```python
@harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
async def test_with_cleanup(fast_http_client):
    # Test creates entities
    org = await create_organization()
    project = await create_project(org.id)

    # Automatic cleanup in reverse order:
    # 1. Delete project
    # 2. Delete organization
```

### 6.2 Test Mode Compatibility

- **HOT Mode**: Full database operations, real RLS enforcement
- **COLD Mode**: Mocked database, simulated RLS
- **DRY Mode**: Pure validation, no database calls

### 6.3 Cascade Flow Testing

Integration with existing cascade flow patterns:

```python
@pytest.mark.hot
@harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
async def test_cascade_schema_validation(cascade_flow_runner):
    """Test schema validation in cascade operations."""
    flow = cascade_flow_runner.create_flow("schema_cascade")

    # Add schema validation steps
    flow.add_step("validate_parent", validate_parent_schema)
    flow.add_step("validate_children", validate_children_schema)
    flow.add_step("validate_relationships", validate_relationships)

    result = await flow.execute()
    assert result.success
```

## 7. CI/CD Integration

### 7.1 GitHub Actions Workflow

The provided workflow runs tests in parallel across different modes and suites, providing:
- Matrix testing across all combinations
- Coverage aggregation
- Performance benchmarking
- Failure reporting

### 7.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: schema-sync-check
        name: Check Schema Sync
        entry: python scripts/sync_schema.py --check
        language: system
        pass_filenames: false

      - id: phase3-tests-fast
        name: Phase 3 Fast Tests
        entry: pytest tests/phase3/ --mode dry -m "not slow"
        language: system
        pass_filenames: false
```

## 8. Monitoring and Reporting

### 8.1 Test Reports

Generate comprehensive HTML reports:

```bash
# Generate detailed HTML report
pytest tests/phase3/ --html=report.html --self-contained-html

# Generate performance benchmark report
pytest tests/phase3/performance/ --benchmark-only --benchmark-autosave
```

### 8.2 Schema Drift Dashboard

Monitor schema drift over time:

```python
# scripts/schema_monitor.py
"""Monitor and report schema drift metrics."""

async def generate_drift_report():
    """Generate schema drift report."""
    sync = SchemaSync()

    report = {
        "timestamp": datetime.now().isoformat(),
        "differences": await sync.detect_drift(),
        "severity_summary": {},
        "affected_tables": [],
        "affected_enums": []
    }

    # Analyze differences
    for diff in report["differences"]:
        severity = diff["severity"]
        report["severity_summary"][severity] = (
            report["severity_summary"].get(severity, 0) + 1
        )

    return report
```

## 9. Implementation Timeline

### Phase 3A: Foundation (Week 1-2)
- Set up test structure
- Implement core fixtures
- Basic schema validation tests

### Phase 3B: RLS & Migration (Week 2-3)
- RLS policy tests
- Migration runner tests
- Version tracking

### Phase 3C: Integration (Week 3-4)
- End-to-end workflows
- Client-server validation
- Cascade operations

### Phase 3D: Performance (Week 4-5)
- Performance benchmarks
- Optimization tests
- Load testing

### Phase 3E: Polish (Week 5-6)
- Documentation
- CI/CD integration
- Monitoring setup

## 10. Success Criteria

1. **Coverage**: Achieve minimum coverage targets for each component
2. **Performance**: All performance tests pass within defined thresholds
3. **Reliability**: Zero flaky tests in CI/CD pipeline
4. **Documentation**: Complete test documentation and examples
5. **Integration**: Seamless integration with existing test framework
6. **Parallelization**: Tests can run in parallel without interference
7. **Monitoring**: Automated drift detection and reporting

## Conclusion

This comprehensive test suite design provides thorough coverage of Phase 3 schema synchronization requirements. It leverages the existing test framework's strengths while adding specialized capabilities for schema validation, RLS testing, and migration verification. The parallel execution strategy enables efficient CI/CD integration, while the monitoring and reporting capabilities ensure ongoing schema integrity.

The test suite is designed to be:
- **Comprehensive**: 155+ tests covering all critical paths
- **Maintainable**: Clear structure and reusable fixtures
- **Performant**: Parallel execution and mode-based optimization
- **Integrated**: Seamless fit with Phase 2 framework
- **Actionable**: Clear metrics and reporting

This design can be executed by multiple agents working in parallel, with each agent focusing on a specific test category while maintaining consistency through shared fixtures and utilities.