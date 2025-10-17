# Phase 3 Database Migration Tests

Comprehensive test suite for database migration functionality with 30 production-ready tests covering migration runners, rollback mechanisms, versioning, and idempotency.

## Overview

This test suite provides complete coverage of the database migration system including:

- **Migration Runner** (10 tests): Core migration application and tracking
- **Rollback** (8 tests): Rollback functionality and data preservation
- **Versioning** (6 tests): Version numbering and dependency management
- **Idempotency** (6 tests): Safe re-execution and recovery patterns

## Test Files

### 1. test_migration_runner.py (10 tests)

Tests core migration engine functionality:

- ✅ Migration applies without errors (COLD/HOT)
- ✅ Version tracking in migrations table
- ✅ Migration ordering (topological sort)
- ✅ Idempotent migration execution (tracking level)
- ✅ Error handling and recovery
- ✅ Partial migration to target version
- ✅ Migration status reporting
- ✅ Checksum validation
- ✅ Edge cases: empty migrations, no rollback functions

### 2. test_rollback.py (8 tests)

Tests rollback mechanisms:

- ✅ Single-step rollback (COLD/HOT)
- ✅ Multi-step rollback in reverse order
- ✅ Rollback without down function handling
- ✅ Data preservation during rollback
- ✅ Complex migration rollback
- ✅ Rollback status updates
- ✅ Failed rollback error handling
- ✅ Edge cases: no migrations, excessive steps

### 3. test_versioning.py (6 tests)

Tests version management:

- ✅ Sequential version numbering (001, 002, 003)
- ✅ Timestamp version format (YYYYMMDD_HHMMSS)
- ✅ Version dependency ordering
- ✅ Skipped version handling (gaps in sequence)
- ✅ Version history tracking in database
- ✅ Version checksum integrity
- ✅ Edge cases: special characters, case sensitivity, empty versions

### 4. test_idempotency.py (6 tests)

Tests idempotent migration patterns:

- ✅ Running migration twice produces same result
- ✅ CREATE IF NOT EXISTS pattern
- ✅ ON CONFLICT DO NOTHING pattern
- ✅ Table creation idempotency (HOT)
- ✅ Data insertion idempotency (HOT)
- ✅ Partial migration recovery
- ✅ Edge cases: non-idempotent detection, concurrent safety

## Test Modes

All tests support two execution modes:

### COLD Mode (Unit Tests)
- Uses mocked database adapter
- No external dependencies
- Fast execution (< 2s per test)
- Runs in parallel
- Perfect for CI/CD pipelines

```bash
pytest tests/phase3/migrations -m cold -v
```

### HOT Mode (Integration Tests)
- Uses real database connection
- Tests actual database operations
- Slower execution (< 30s per test)
- Requires database setup
- Validates real-world behavior

```bash
pytest tests/phase3/migrations -m hot -v
```

## Running Tests

### Prerequisites

1. **For COLD mode (no setup needed)**:
   ```bash
   # Install dependencies
   pip install pytest pytest-asyncio
   ```

2. **For HOT mode (requires database)**:
   ```bash
   # Set database connection
   export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
   ```

### Run All Tests

```bash
# Run all 30 tests (COLD + HOT)
pytest tests/phase3/migrations -v

# Run only COLD mode tests (fast)
pytest tests/phase3/migrations -m cold -v

# Run only HOT mode tests (requires database)
pytest tests/phase3/migrations -m hot -v
```

### Run Specific Test Files

```bash
# Run migration runner tests only
pytest tests/phase3/migrations/test_migration_runner.py -v

# Run rollback tests only
pytest tests/phase3/migrations/test_rollback.py -v

# Run versioning tests only
pytest tests/phase3/migrations/test_versioning.py -v

# Run idempotency tests only
pytest tests/phase3/migrations/test_idempotency.py -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/phase3/migrations --cov=pheno_vendor.db_kit.migrations --cov-report=html -v

# View coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Run single test by name
pytest tests/phase3/migrations/test_migration_runner.py::TestMigrationRunnerCOLD::test_01_migration_applies_without_errors_cold -v

# Run tests matching pattern
pytest tests/phase3/migrations -k "rollback" -v

# Run tests with specific marker
pytest tests/phase3/migrations -m "cold and not integration" -v
```

## Test Output

Each test provides detailed logging:

```
TEST: Migration applies without errors (COLD)
PASS: Migration applied successfully (COLD)
```

Failed tests include full error traces:

```
FAIL: Migration application failed: RuntimeError: Intentional migration failure
Traceback (most recent call last):
  ...
```

## Database Setup for HOT Mode

### PostgreSQL

```bash
# Create test database
createdb migration_test

# Set connection string
export TEST_DATABASE_URL="postgresql://localhost:5432/migration_test"

# Run HOT tests
pytest tests/phase3/migrations -m hot -v
```

### Cleanup

HOT mode tests use `@harmful` decorator for automatic cleanup:

- Creates tables/data during test
- Automatically cleans up after test completion
- Handles cleanup even on test failure
- Uses cascade delete pattern

## Test Architecture

### Mock Database Adapter

```python
class MockDatabaseAdapter(DatabaseAdapter):
    """In-memory mock for COLD mode testing."""

    def __init__(self):
        self.tables = {}  # In-memory storage
        self.queries_executed = []  # Query log
        self.should_fail = False  # Failure simulation
```

### Test Migration Functions

```python
async def migration_001_up(adapter: DatabaseAdapter):
    """Test migration - creates table."""
    await adapter.execute("""
        CREATE TABLE IF NOT EXISTS test_table_001 (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        )
    """)

async def migration_001_down(adapter: DatabaseAdapter):
    """Test migration rollback."""
    await adapter.execute("DROP TABLE IF EXISTS test_table_001")
```

### Fixtures

```python
@pytest_asyncio.fixture
async def migration_engine_cold(mock_adapter):
    """Provide migration engine for COLD mode."""
    engine = MigrationEngine(mock_adapter)
    await engine.init()
    return engine

@pytest_asyncio.fixture
async def migration_engine_hot(real_adapter):
    """Provide migration engine for HOT mode with cleanup."""
    engine = MigrationEngine(real_adapter)
    await engine.init()
    yield engine
    # Automatic cleanup after test
    await cleanup_tables(real_adapter)
```

## Coverage Goals

- **Line Coverage**: 100%
- **Branch Coverage**: 100%
- **Function Coverage**: 100%
- **Error Paths**: All error scenarios tested
- **Edge Cases**: Comprehensive edge case coverage

## Test Quality Standards

### Each Test Includes:

1. **Given-When-Then** structure in docstrings
2. **Detailed logging** with TEST/PASS/FAIL markers
3. **Error handling** with try-except and proper logging
4. **Assertions** with descriptive failure messages
5. **Cleanup** using @harmful decorator (HOT mode)

### Example Test Structure:

```python
async def test_migration_applies_without_errors_cold(self, migration_engine_cold):
    """Test that migrations apply successfully in COLD mode.

    Given: A migration engine with mock database
    When: A valid migration is registered and applied
    Then: Migration executes without errors
    And: Migration is recorded in migrations table
    """
    logger.info("TEST: Migration applies without errors (COLD)")

    try:
        # Arrange
        migration = migration_engine_cold.register(...)

        # Act
        applied = await migration_engine_cold.migrate()

        # Assert
        assert len(applied) == 1, "Expected 1 migration to be applied"
        assert applied[0].status == MigrationStatus.APPLIED

        logger.info("PASS: Migration applied successfully (COLD)")
    except Exception as e:
        logger.error(f"FAIL: Migration application failed: {e}", exc_info=True)
        raise
```

## CI/CD Integration

### GitHub Actions Example:

```yaml
name: Migration Tests

on: [push, pull_request]

jobs:
  test-cold:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: uv sync
      - run: pytest tests/phase3/migrations -m cold -v

  test-hot:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: uv sync
      - run: pytest tests/phase3/migrations -m hot -v
        env:
          TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres
```

## Troubleshooting

### Common Issues:

1. **"TEST_DATABASE_URL not set"**
   - Solution: Export database URL before running HOT tests
   - `export TEST_DATABASE_URL="postgresql://..."`

2. **"PostgresAdapter not available"**
   - Solution: Install PostgreSQL adapter
   - `pip install asyncpg`

3. **"Database connection failed"**
   - Solution: Verify database is running
   - `pg_isready -h localhost -p 5432`

4. **"Migration already applied"**
   - Solution: Clean up test database
   - `DROP TABLE _migrations CASCADE;`

## Best Practices

1. **Always run COLD tests first** (fast feedback)
2. **Use HOT tests before deployment** (validate real database)
3. **Review logs for warnings** (non-idempotent migrations, etc.)
4. **Monitor test duration** (COLD < 2s, HOT < 30s)
5. **Keep database clean** (use @harmful decorator)

## Contributing

When adding new tests:

1. Follow existing test structure (Given-When-Then)
2. Add both COLD and HOT variants when applicable
3. Include comprehensive error handling
4. Add detailed logging (TEST/PASS/FAIL)
5. Update this README with new test descriptions
6. Ensure 100% coverage for new code paths

## License

See project root LICENSE file.

## Support

For issues or questions:
- Open GitHub issue
- Check existing test examples
- Review migration engine documentation
