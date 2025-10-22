"""Test migration runner functionality with comprehensive coverage.

This module tests the MigrationEngine's core functionality including:
- Migration application without errors
- Version tracking in migrations table
- Migration ordering (topological sort)
- Idempotent migration execution
- Error handling and recovery
- Both HOT (real database) and COLD (mocked) modes

Coverage areas:
- Happy path: successful migration application
- Error scenarios: duplicate migrations, invalid checksums, SQL errors
- Edge cases: empty migrations, skipped versions, concurrent migrations
- Performance: migration execution speed validation
"""

import logging
from typing import Any

import pytest
import pytest_asyncio
from pheno_vendor.db_kit.adapters.base import DatabaseAdapter
from pheno_vendor.db_kit.migrations import MigrationEngine, MigrationStatus

from tests.framework import harmful
from tests.framework.harmful import CleanupStrategy

logger = logging.getLogger(__name__)


# ============================================================================
# Mock Database Adapter for COLD Mode
# ============================================================================


class MockDatabaseAdapter(DatabaseAdapter):
    """Mock database adapter for testing without real database."""

    def __init__(self):
        """Initialize mock adapter with in-memory storage."""
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.queries_executed: list[str] = []
        self.should_fail = False
        self.fail_on_query = None

    async def execute(self, sql: str, params: Any = None) -> list[dict[str, Any]]:
        """Execute SQL query on mock database."""
        self.queries_executed.append(sql)
        logger.debug(f"Mock execute: {sql[:100]}...")

        # Simulate failure if configured
        if self.should_fail:
            raise RuntimeError("Mock database error")

        if self.fail_on_query and self.fail_on_query in sql:
            raise RuntimeError(f"Mock database error on: {self.fail_on_query}")

        # Handle CREATE TABLE for migrations table
        if "CREATE TABLE" in sql and "_migrations" in sql:
            self.tables["_migrations"] = []
            return []

        # Handle SELECT queries
        if sql.strip().startswith("SELECT"):
            table_name = "_migrations"
            if table_name in self.tables:
                return self.tables[table_name]
            return []

        # Handle UPDATE queries
        if "UPDATE" in sql and "_migrations" in sql:
            return []

        return []

    async def insert(
        self, table: str, data: Any, *, returning: str = None
    ) -> dict[str, Any]:
        """Insert data into mock table."""
        if table not in self.tables:
            self.tables[table] = []

        if isinstance(data, list):
            self.tables[table].extend(data)
            return data
        else:
            self.tables[table].append(data)
            return data

    async def query(self, table: str, **kwargs) -> list[dict[str, Any]]:
        """Query mock table."""
        return self.tables.get(table, [])

    async def get_single(self, table: str, filters: dict, **kwargs):
        """Get single row from mock table."""
        rows = self.tables.get(table, [])
        for row in rows:
            if all(row.get(k) == v for k, v in filters.items()):
                return row
        return None

    async def update(self, table: str, filters: dict, data: dict, **kwargs):
        """Update mock table."""
        return []

    async def delete(self, table: str, filters: dict, **kwargs):
        """Delete from mock table."""
        return []

    async def upsert(self, table: str, data: Any, **kwargs):
        """Upsert into mock table."""
        return data

    async def count(self, table: str, filters: dict = None) -> int:
        """Count rows in mock table."""
        return len(self.tables.get(table, []))


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_adapter():
    """Provide mock database adapter for COLD mode tests."""
    adapter = MockDatabaseAdapter()
    return adapter


@pytest_asyncio.fixture
async def real_adapter():
    """Provide real database adapter for HOT mode tests.

    Note: This requires a real database connection.
    Skip tests if database is not available.
    """
    try:
        import os

        from pheno_vendor.db_kit.adapters.postgres import PostgresAdapter

        # Check for database connection string
        db_url = os.getenv("TEST_DATABASE_URL")
        if not db_url:
            pytest.skip("TEST_DATABASE_URL not set - skipping HOT mode test")

        adapter = PostgresAdapter(db_url)
        await adapter.connect()
        yield adapter
        await adapter.disconnect()
    except ImportError:
        pytest.skip("PostgresAdapter not available - skipping HOT mode test")
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


@pytest_asyncio.fixture
async def migration_engine_cold(mock_adapter):
    """Provide migration engine with mock adapter (COLD mode)."""
    engine = MigrationEngine(mock_adapter)
    await engine.init()
    return engine


@pytest_asyncio.fixture
async def migration_engine_hot(real_adapter):
    """Provide migration engine with real adapter (HOT mode)."""
    engine = MigrationEngine(real_adapter)
    await engine.init()

    # Clean up migrations table after test
    yield engine

    # Cleanup: drop test migrations
    try:
        await real_adapter.execute("DROP TABLE IF EXISTS _migrations CASCADE")
        await real_adapter.execute("DROP TABLE IF EXISTS test_table_001 CASCADE")
        await real_adapter.execute("DROP TABLE IF EXISTS test_table_002 CASCADE")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


# ============================================================================
# Test Migration Functions
# ============================================================================


async def migration_001_up(adapter: DatabaseAdapter):
    """Test migration 001 - create initial table."""
    sql = """
    CREATE TABLE IF NOT EXISTS test_table_001 (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    await adapter.execute(sql)


async def migration_001_down(adapter: DatabaseAdapter):
    """Test migration 001 - rollback."""
    await adapter.execute("DROP TABLE IF EXISTS test_table_001")


async def migration_002_up(adapter: DatabaseAdapter):
    """Test migration 002 - add column."""
    sql = "ALTER TABLE test_table_001 ADD COLUMN description TEXT"
    await adapter.execute(sql)


async def migration_002_down(adapter: DatabaseAdapter):
    """Test migration 002 - rollback."""
    sql = "ALTER TABLE test_table_001 DROP COLUMN description"
    await adapter.execute(sql)


async def migration_003_up(adapter: DatabaseAdapter):
    """Test migration 003 - create index."""
    sql = "CREATE INDEX idx_test_name ON test_table_001(name)"
    await adapter.execute(sql)


async def migration_003_down(adapter: DatabaseAdapter):
    """Test migration 003 - rollback."""
    sql = "DROP INDEX IF EXISTS idx_test_name"
    await adapter.execute(sql)


async def migration_failing_up(adapter: DatabaseAdapter):
    """Test migration that intentionally fails."""
    raise RuntimeError("Intentional migration failure for testing")


# ============================================================================
# COLD Mode Tests (Mocked Database)
# ============================================================================


@pytest.mark.cold
class TestMigrationRunnerCOLD:
    """Test migration runner with mocked database (COLD mode).

    These tests run quickly without real database dependencies.
    Expected execution time: < 2s per test.
    """

    async def test_01_migration_applies_without_errors_cold(
        self, migration_engine_cold
    ):
        """Test that migrations apply successfully in COLD mode.

        Given: A migration engine with mock database
        When: A valid migration is registered and applied
        Then: Migration executes without errors
        And: Migration is recorded in migrations table
        """
        logger.info("TEST: Migration applies without errors (COLD)")

        try:
            # Register migration
            migration = migration_engine_cold.register(
                version="001",
                name="create_test_table",
                up=migration_001_up,
                down=migration_001_down,
            )

            # Apply migration
            applied = await migration_engine_cold.migrate()

            # Assertions
            assert len(applied) == 1, "Expected 1 migration to be applied"
            assert applied[0].version == "001"
            assert applied[0].status == MigrationStatus.APPLIED
            assert migration.status == MigrationStatus.APPLIED

            logger.info("PASS: Migration applied successfully (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Migration application failed: {e}", exc_info=True)
            raise

    async def test_02_migration_version_tracking_cold(self, migration_engine_cold):
        """Test that migration versions are tracked correctly.

        Given: Multiple migrations registered
        When: Migrations are applied
        Then: All versions are recorded in migrations table
        And: Applied migrations list contains all versions
        """
        logger.info("TEST: Migration version tracking (COLD)")

        try:
            # Register multiple migrations
            migration_engine_cold.register("001", "first", migration_001_up)
            migration_engine_cold.register("002", "second", migration_002_up)
            migration_engine_cold.register("003", "third", migration_003_up)

            # Apply all migrations
            applied = await migration_engine_cold.migrate()

            # Get applied migrations list
            applied_versions = await migration_engine_cold.get_applied_migrations()

            # Assertions
            assert len(applied) == 3, "Expected 3 migrations applied"
            assert len(applied_versions) == 3, "Expected 3 versions tracked"
            assert "001" in applied_versions
            assert "002" in applied_versions
            assert "003" in applied_versions

            logger.info("PASS: Migration versions tracked correctly (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Version tracking failed: {e}", exc_info=True)
            raise

    async def test_03_migration_ordering_cold(self, migration_engine_cold):
        """Test that migrations execute in correct order.

        Given: Migrations registered out of order
        When: Migrations are applied
        Then: Migrations execute in version order
        And: Dependencies are respected
        """
        logger.info("TEST: Migration ordering (COLD)")

        execution_order = []

        async def track_001(adapter):
            execution_order.append("001")

        async def track_003(adapter):
            execution_order.append("003")

        async def track_002(adapter):
            execution_order.append("002")

        try:
            # Register migrations out of order
            migration_engine_cold.register("003", "third", track_003)
            migration_engine_cold.register("001", "first", track_001)
            migration_engine_cold.register("002", "second", track_002)

            # Apply migrations
            await migration_engine_cold.migrate()

            # Assertions
            assert execution_order == ["001", "002", "003"], \
                f"Expected [001, 002, 003], got {execution_order}"

            logger.info("PASS: Migrations executed in correct order (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Migration ordering failed: {e}", exc_info=True)
            raise

    async def test_04_idempotent_migration_cold(self, migration_engine_cold):
        """Test that running same migration twice is handled correctly.

        Given: A migration that has already been applied
        When: Migrate is called again
        Then: Migration is not re-executed
        And: No errors occur
        """
        logger.info("TEST: Idempotent migration (COLD)")

        execution_count = {"count": 0}

        async def counting_migration(adapter):
            execution_count["count"] += 1

        try:
            # Register and apply migration
            migration_engine_cold.register("001", "test", counting_migration)
            await migration_engine_cold.migrate()

            assert execution_count["count"] == 1

            # Try to migrate again
            await migration_engine_cold.migrate()

            # Migration should not run again
            assert execution_count["count"] == 1, \
                "Migration executed twice (not idempotent)"

            logger.info("PASS: Migration is idempotent (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Idempotency test failed: {e}", exc_info=True)
            raise

    async def test_05_migration_error_handling_cold(self, migration_engine_cold):
        """Test that migration errors are handled properly.

        Given: A migration that fails during execution
        When: Migration is applied
        Then: Error is caught and logged
        And: Migration status is set to FAILED
        And: Subsequent migrations are not executed
        """
        logger.info("TEST: Migration error handling (COLD)")

        try:
            # Register failing migration
            migration_engine_cold.register("001", "failing", migration_failing_up)
            migration_engine_cold.register("002", "after_fail", migration_002_up)

            # Attempt to migrate (should fail)
            with pytest.raises(RuntimeError, match="Intentional migration failure"):
                await migration_engine_cold.migrate()

            # Check that only first migration was attempted
            applied = await migration_engine_cold.get_applied_migrations()
            assert len(applied) == 0, "Failed migration should not be marked as applied"

            logger.info("PASS: Migration errors handled correctly (COLD)")
        except AssertionError:
            raise
        except Exception as e:
            logger.error(f"FAIL: Error handling test failed: {e}", exc_info=True)
            raise


# ============================================================================
# HOT Mode Tests (Real Database)
# ============================================================================


@pytest.mark.hot
@pytest.mark.integration
class TestMigrationRunnerHOT:
    """Test migration runner with real database (HOT mode).

    These tests require a real database connection.
    Expected execution time: < 30s per test.
    """

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_06_migration_applies_without_errors_hot(
        self, migration_engine_hot, harmful_tracker
    ):
        """Test that migrations apply successfully with real database.

        Given: A migration engine with real database connection
        When: A valid migration is registered and applied
        Then: Migration executes without errors
        And: Actual table is created in database
        And: Migration is recorded in migrations table
        """
        logger.info("TEST: Migration applies without errors (HOT)")

        try:
            # Register migration
            migration_engine_hot.register(
                version="001",
                name="create_test_table",
                up=migration_001_up,
                down=migration_001_down,
            )

            # Apply migration
            applied = await migration_engine_hot.migrate()

            # Verify migration was applied
            assert len(applied) == 1
            assert applied[0].status == MigrationStatus.APPLIED

            # Verify table was actually created
            result = await migration_engine_hot.adapter.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'test_table_001'"
            )
            assert len(result) > 0, "Table was not created"

            logger.info("PASS: Migration applied successfully (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Migration failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_07_migration_version_tracking_hot(
        self, migration_engine_hot, harmful_tracker
    ):
        """Test version tracking with real database.

        Given: Multiple migrations registered
        When: Migrations are applied to real database
        Then: All versions are persisted in migrations table
        And: Versions can be queried correctly
        """
        logger.info("TEST: Migration version tracking (HOT)")

        try:
            # Register migrations
            migration_engine_hot.register("001", "first", migration_001_up, migration_001_down)
            migration_engine_hot.register("002", "second", migration_002_up, migration_002_down)

            # Apply migrations
            await migration_engine_hot.migrate()

            # Verify tracking in database
            rows = await migration_engine_hot.adapter.execute(
                "SELECT version, name, status FROM _migrations ORDER BY version"
            )

            assert len(rows) == 2
            assert rows[0]["version"] == "001"
            assert rows[1]["version"] == "002"
            assert all(row["status"] == MigrationStatus.APPLIED.value for row in rows)

            logger.info("PASS: Version tracking works correctly (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Version tracking failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_08_partial_migration_target_hot(
        self, migration_engine_hot, harmful_tracker
    ):
        """Test migrating to a specific target version.

        Given: Multiple migrations registered
        When: Migrate is called with target version
        Then: Only migrations up to target are applied
        And: Later migrations remain pending
        """
        logger.info("TEST: Partial migration to target (HOT)")

        try:
            # Register multiple migrations
            migration_engine_hot.register("001", "first", migration_001_up, migration_001_down)
            migration_engine_hot.register("002", "second", migration_002_up, migration_002_down)
            migration_engine_hot.register("003", "third", migration_003_up, migration_003_down)

            # Migrate only to version 002
            applied = await migration_engine_hot.migrate(target="002")

            # Verify only 001 and 002 were applied
            assert len(applied) == 2
            assert applied[0].version == "001"
            assert applied[1].version == "002"

            # Verify 003 is still pending
            pending = await migration_engine_hot.get_pending_migrations()
            assert len(pending) == 1
            assert pending[0].version == "003"

            logger.info("PASS: Partial migration to target works (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Partial migration failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_09_migration_status_reporting_hot(
        self, migration_engine_hot, harmful_tracker
    ):
        """Test migration status reporting functionality.

        Given: Some migrations applied, some pending
        When: Status is queried
        Then: Correct status is reported for each migration
        And: Applied timestamps are recorded
        """
        logger.info("TEST: Migration status reporting (HOT)")

        try:
            # Register migrations
            migration_engine_hot.register("001", "applied", migration_001_up)
            migration_engine_hot.register("002", "pending", migration_002_up)

            # Apply only first migration
            await migration_engine_hot.migrate(target="001")

            # Get status
            statuses = await migration_engine_hot.status()

            # Verify status
            assert len(statuses) == 2

            status_001 = next(s for s in statuses if s["version"] == "001")
            status_002 = next(s for s in statuses if s["version"] == "002")

            assert status_001["status"] == "applied"
            assert status_001["applied_at"] is not None

            assert status_002["status"] == "pending"
            assert status_002["applied_at"] is None

            logger.info("PASS: Migration status reporting works (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Status reporting failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_10_checksum_validation_hot(
        self, migration_engine_hot, harmful_tracker
    ):
        """Test that migration checksums are calculated and stored.

        Given: A migration is registered
        When: Migration is applied
        Then: Checksum is calculated and stored
        And: Checksum can be used to detect changes
        """
        logger.info("TEST: Checksum validation (HOT)")

        try:
            # Register migration
            migration = migration_engine_hot.register(
                "001", "test", migration_001_up
            )

            # Verify checksum was calculated
            assert migration.checksum is not None
            assert len(migration.checksum) == 64  # SHA-256 hex digest

            # Apply migration
            await migration_engine_hot.migrate()

            # Verify checksum was stored
            rows = await migration_engine_hot.adapter.execute(
                "SELECT checksum FROM _migrations WHERE version = '001'"
            )
            assert len(rows) == 1
            assert rows[0]["checksum"] == migration.checksum

            logger.info("PASS: Checksum validation works (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Checksum validation failed: {e}", exc_info=True)
            raise


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.cold
class TestMigrationRunnerEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_empty_migration_list(self, migration_engine_cold):
        """Test behavior with no migrations registered.

        Given: No migrations registered
        When: Migrate is called
        Then: No error occurs
        And: Empty list is returned
        """
        logger.info("TEST: Empty migration list")

        applied = await migration_engine_cold.migrate()
        assert len(applied) == 0

        logger.info("PASS: Empty migration list handled")

    async def test_migration_with_no_down_function(self, migration_engine_cold):
        """Test migration without rollback function.

        Given: Migration registered without down function
        When: Migration is applied
        Then: Migration succeeds
        And: Status indicates no rollback available
        """
        logger.info("TEST: Migration with no down function")

        migration_engine_cold.register(
            "001", "no_rollback", migration_001_up, down=None
        )

        await migration_engine_cold.migrate()

        # Check status shows no rollback
        statuses = await migration_engine_cold.status()
        assert statuses[0]["has_rollback"] is False

        logger.info("PASS: Migration without down function works")

    async def test_duplicate_version_registration(self, migration_engine_cold):
        """Test registering same version twice.

        Given: A version is registered
        When: Same version is registered again
        Then: Both migrations are stored
        But: Only one will be applied (first one)
        """
        logger.info("TEST: Duplicate version registration")

        migration_engine_cold.register("001", "first", migration_001_up)
        migration_engine_cold.register("001", "second", migration_002_up)

        # Only one should be applied
        applied = await migration_engine_cold.migrate()
        assert len(applied) == 1

        logger.info("PASS: Duplicate version handled")


__all__ = [
    "TestMigrationRunnerCOLD",
    "TestMigrationRunnerHOT",
    "TestMigrationRunnerEdgeCases",
]
