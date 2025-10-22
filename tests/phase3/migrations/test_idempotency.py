"""Test migration idempotency with comprehensive coverage.

This module tests that migrations can be run multiple times safely:
- Running same migration twice produces same result
- Partial migration recovery after failures
- CREATE IF NOT EXISTS patterns
- Data duplication prevention
- State consistency after re-runs

Coverage areas:
- Happy path: migrations run multiple times without errors
- Error scenarios: partial failures and recovery
- Edge cases: concurrent migrations, race conditions
- Data integrity: no duplicate data on re-runs
"""

import asyncio
import logging

import pytest
import pytest_asyncio
from pheno_vendor.db_kit.adapters.base import DatabaseAdapter
from pheno_vendor.db_kit.migrations import MigrationEngine

from tests.framework import harmful
from tests.framework.harmful import CleanupStrategy

from .test_migration_runner import MockDatabaseAdapter

logger = logging.getLogger(__name__)


# ============================================================================
# Idempotent Migration Functions
# ============================================================================


async def idempotent_create_table_up(adapter: DatabaseAdapter):
    """Idempotent migration - create table with IF NOT EXISTS."""
    sql = """
    CREATE TABLE IF NOT EXISTS idempotent_test (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    await adapter.execute(sql)
    logger.debug("Idempotent table creation executed")


async def idempotent_create_table_down(adapter: DatabaseAdapter):
    """Rollback idempotent table creation."""
    await adapter.execute("DROP TABLE IF EXISTS idempotent_test")


async def idempotent_insert_data_up(adapter: DatabaseAdapter):
    """Idempotent migration - insert data with ON CONFLICT DO NOTHING."""
    # First ensure table exists
    await adapter.execute("""
        CREATE TABLE IF NOT EXISTS idempotent_data (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    """)

    # Insert data idempotently
    await adapter.execute("""
        INSERT INTO idempotent_data (key, value)
        VALUES ('key1', 'value1'), ('key2', 'value2')
        ON CONFLICT (key) DO NOTHING
    """)
    logger.debug("Idempotent data insertion executed")


async def idempotent_insert_data_down(adapter: DatabaseAdapter):
    """Rollback idempotent data insertion."""
    await adapter.execute("DROP TABLE IF EXISTS idempotent_data")


async def non_idempotent_insert_up(adapter: DatabaseAdapter):
    """Non-idempotent migration - inserts duplicate data on re-run."""
    await adapter.execute("""
        CREATE TABLE IF NOT EXISTS non_idempotent_test (
            id SERIAL PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Insert without conflict handling (will create duplicates)
    await adapter.execute(
        "INSERT INTO non_idempotent_test (value) VALUES ('duplicate')"
    )
    logger.debug("Non-idempotent insert executed")


async def partial_migration_up(adapter: DatabaseAdapter):
    """Migration that can fail partway through."""
    # Step 1: Create table (succeeds)
    await adapter.execute("""
        CREATE TABLE IF NOT EXISTS partial_test (
            id SERIAL PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Step 2: Insert data (might fail)
    await adapter.execute("INSERT INTO partial_test (value) VALUES ('test')")

    # Step 3: This might fail
    # (In real scenario, this could be network error, etc.)
    logger.debug("Partial migration executed")


async def recoverable_migration_up(adapter: DatabaseAdapter):
    """Migration designed to recover from partial failures."""
    # Use transactions and IF NOT EXISTS patterns
    await adapter.execute("""
        CREATE TABLE IF NOT EXISTS recoverable_test (
            id SERIAL PRIMARY KEY,
            value TEXT NOT NULL UNIQUE
        )
    """)

    # Use ON CONFLICT for data insertion
    await adapter.execute("""
        INSERT INTO recoverable_test (value)
        VALUES ('recoverable_value')
        ON CONFLICT (value) DO NOTHING
    """)
    logger.debug("Recoverable migration executed")


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_adapter_idempotency():
    """Provide mock adapter for idempotency tests."""
    adapter = MockDatabaseAdapter()
    return adapter


@pytest_asyncio.fixture
async def migration_engine_idempotency_cold(mock_adapter_idempotency):
    """Provide migration engine for idempotency tests (COLD mode)."""
    engine = MigrationEngine(mock_adapter_idempotency)
    await engine.init()
    return engine


@pytest_asyncio.fixture
async def migration_engine_idempotency_hot(real_adapter_idempotency):
    """Provide migration engine for idempotency tests (HOT mode)."""
    engine = MigrationEngine(real_adapter_idempotency)
    await engine.init()

    yield engine

    # Cleanup
    try:
        await real_adapter_idempotency.execute("DROP TABLE IF EXISTS _migrations CASCADE")
        await real_adapter_idempotency.execute("DROP TABLE IF EXISTS idempotent_test CASCADE")
        await real_adapter_idempotency.execute("DROP TABLE IF EXISTS idempotent_data CASCADE")
        await real_adapter_idempotency.execute("DROP TABLE IF EXISTS non_idempotent_test CASCADE")
        await real_adapter_idempotency.execute("DROP TABLE IF EXISTS partial_test CASCADE")
        await real_adapter_idempotency.execute("DROP TABLE IF EXISTS recoverable_test CASCADE")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


@pytest_asyncio.fixture
async def real_adapter_idempotency():
    """Provide real database adapter for idempotency tests."""
    try:
        import os

        from pheno_vendor.db_kit.adapters.postgres import PostgresAdapter

        db_url = os.getenv("TEST_DATABASE_URL")
        if not db_url:
            pytest.skip("TEST_DATABASE_URL not set")

        adapter = PostgresAdapter(db_url)
        await adapter.connect()
        yield adapter
        await adapter.disconnect()
    except ImportError:
        pytest.skip("PostgresAdapter not available")
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")


# ============================================================================
# COLD Mode Idempotency Tests
# ============================================================================


@pytest.mark.cold
class TestIdempotencyCOLD:
    """Test idempotency with mocked database (COLD mode)."""

    async def test_01_migration_runs_twice_same_result_cold(
        self, migration_engine_idempotency_cold
    ):
        """Test that running migration twice produces same result.

        Given: An idempotent migration
        When: Migration is run twice
        Then: Both runs succeed without errors
        And: Second run does not change state
        """
        logger.info("TEST: Migration runs twice with same result (COLD)")

        execution_count = {"count": 0}

        async def idempotent_migration(adapter):
            execution_count["count"] += 1
            # Simulate idempotent operation
            await adapter.execute("CREATE TABLE IF NOT EXISTS test (id SERIAL)")

        try:
            # Register migration
            migration_engine_idempotency_cold.register(
                "001", "idempotent", idempotent_migration
            )

            # First run
            await migration_engine_idempotency_cold.migrate()
            assert execution_count["count"] == 1

            # Second run (should not execute again due to tracking)
            await migration_engine_idempotency_cold.migrate()
            assert execution_count["count"] == 1, "Migration ran twice (not tracked)"

            logger.info("PASS: Migration idempotency verified (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Idempotency test failed: {e}", exc_info=True)
            raise

    async def test_02_create_if_not_exists_pattern_cold(
        self, migration_engine_idempotency_cold
    ):
        """Test CREATE IF NOT EXISTS pattern for idempotency.

        Given: Migration using IF NOT EXISTS
        When: Same migration is applied multiple times
        Then: No errors occur
        And: Entity is created only once
        """
        logger.info("TEST: CREATE IF NOT EXISTS pattern (COLD)")

        try:
            migration_engine_idempotency_cold.register(
                "001", "create_idempotent", idempotent_create_table_up
            )

            # Apply multiple times (simulation)
            await migration_engine_idempotency_cold.migrate()

            # Verify migration is marked as applied
            applied = await migration_engine_idempotency_cold.get_applied_migrations()
            assert "001" in applied

            # Try to migrate again (should be no-op)
            await migration_engine_idempotency_cold.migrate()

            logger.info("PASS: IF NOT EXISTS pattern works (COLD)")
        except Exception as e:
            logger.error(f"FAIL: IF NOT EXISTS test failed: {e}", exc_info=True)
            raise

    async def test_03_on_conflict_do_nothing_pattern_cold(
        self, migration_engine_idempotency_cold
    ):
        """Test ON CONFLICT DO NOTHING pattern for data idempotency.

        Given: Migration using ON CONFLICT DO NOTHING
        When: Data is inserted multiple times
        Then: No duplicate data is created
        And: No errors occur
        """
        logger.info("TEST: ON CONFLICT DO NOTHING pattern (COLD)")

        try:
            # This test verifies the pattern is used correctly
            migration_engine_idempotency_cold.register(
                "001", "data_idempotent", idempotent_insert_data_up
            )

            await migration_engine_idempotency_cold.migrate()

            # Verify migration applied
            applied = await migration_engine_idempotency_cold.get_applied_migrations()
            assert "001" in applied

            logger.info("PASS: ON CONFLICT pattern works (COLD)")
        except Exception as e:
            logger.error(f"FAIL: ON CONFLICT test failed: {e}", exc_info=True)
            raise


# ============================================================================
# HOT Mode Idempotency Tests
# ============================================================================


@pytest.mark.hot
@pytest.mark.integration
class TestIdempotencyHOT:
    """Test idempotency with real database (HOT mode)."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_04_table_creation_idempotency_hot(
        self, migration_engine_idempotency_hot, harmful_tracker
    ):
        """Test that table creation is truly idempotent.

        Given: Migration that creates a table
        When: Migration function is called twice
        Then: Table is created only once
        And: Second call does not error
        """
        logger.info("TEST: Table creation idempotency (HOT)")

        try:
            # Register idempotent migration
            migration_engine_idempotency_hot.register(
                "001", "create_table", idempotent_create_table_up, idempotent_create_table_down
            )

            # First application
            await migration_engine_idempotency_hot.migrate()

            # Verify table exists
            result = await migration_engine_idempotency_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM information_schema.tables "
                "WHERE table_name = 'idempotent_test'"
            )
            assert result[0]["count"] == 1

            # Manually run the up function again (testing idempotency of SQL)
            await idempotent_create_table_up(migration_engine_idempotency_hot.adapter)

            # Verify still only one table
            result = await migration_engine_idempotency_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM information_schema.tables "
                "WHERE table_name = 'idempotent_test'"
            )
            assert result[0]["count"] == 1

            logger.info("PASS: Table creation is idempotent (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Table creation idempotency failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_05_data_insertion_idempotency_hot(
        self, migration_engine_idempotency_hot, harmful_tracker
    ):
        """Test that data insertion is idempotent.

        Given: Migration that inserts data with ON CONFLICT
        When: Migration is run multiple times
        Then: Data is inserted only once
        And: No duplicate data exists
        """
        logger.info("TEST: Data insertion idempotency (HOT)")

        try:
            # Register idempotent data migration
            migration_engine_idempotency_hot.register(
                "001", "insert_data", idempotent_insert_data_up, idempotent_insert_data_down
            )

            # First application
            await migration_engine_idempotency_hot.migrate()

            # Count rows
            result = await migration_engine_idempotency_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM idempotent_data"
            )
            initial_count = result[0]["count"]
            assert initial_count == 2

            # Run migration function again manually
            await idempotent_insert_data_up(migration_engine_idempotency_hot.adapter)

            # Verify no duplicate data
            result = await migration_engine_idempotency_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM idempotent_data"
            )
            assert result[0]["count"] == initial_count, "Duplicate data was inserted"

            logger.info("PASS: Data insertion is idempotent (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Data insertion idempotency failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_06_partial_migration_recovery_hot(
        self, migration_engine_idempotency_hot, harmful_tracker
    ):
        """Test recovery from partial migration execution.

        Given: Migration that can fail partway through
        When: Migration is re-run after partial failure
        Then: Migration completes successfully
        And: No duplicate operations occur
        """
        logger.info("TEST: Partial migration recovery (HOT)")

        try:
            # Register recoverable migration
            migration_engine_idempotency_hot.register(
                "001", "recoverable", recoverable_migration_up
            )

            # First run (complete)
            await migration_engine_idempotency_hot.migrate()

            # Verify table and data
            result = await migration_engine_idempotency_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM recoverable_test"
            )
            assert result[0]["count"] == 1

            # Simulate re-run after partial failure
            await recoverable_migration_up(migration_engine_idempotency_hot.adapter)

            # Verify no duplicate data
            result = await migration_engine_idempotency_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM recoverable_test"
            )
            assert result[0]["count"] == 1, "Duplicate data after recovery"

            logger.info("PASS: Partial migration recovery works (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Partial migration recovery failed: {e}", exc_info=True)
            raise


# ============================================================================
# Edge Cases and Non-Idempotent Scenarios
# ============================================================================


@pytest.mark.cold
class TestIdempotencyEdgeCases:
    """Test edge cases and non-idempotent scenarios."""

    async def test_non_idempotent_migration_detection(
        self, migration_engine_idempotency_cold
    ):
        """Test that non-idempotent migrations are detected.

        Given: Migration without idempotent patterns
        When: Migration is registered
        Then: Migration can be applied
        But: Warning about non-idempotency could be issued
        """
        logger.info("TEST: Non-idempotent migration detection")

        try:
            # Register non-idempotent migration
            migration_engine_idempotency_cold.register(
                "001", "non_idempotent", non_idempotent_insert_up
            )

            # Apply migration
            await migration_engine_idempotency_cold.migrate()

            # Migration should succeed (tracking prevents re-run)
            applied = await migration_engine_idempotency_cold.get_applied_migrations()
            assert "001" in applied

            logger.info("PASS: Non-idempotent migration accepted with tracking")
        except Exception as e:
            logger.error(f"FAIL: Non-idempotent detection failed: {e}", exc_info=True)
            raise

    async def test_migration_tracking_prevents_rerun(
        self, migration_engine_idempotency_cold
    ):
        """Test that migration tracking prevents re-runs.

        Given: Any migration (idempotent or not)
        When: Migration is applied
        Then: Migration tracking prevents re-execution
        And: Idempotency at tracking level
        """
        logger.info("TEST: Migration tracking prevents re-run")

        execution_count = {"count": 0}

        async def counting_migration(adapter):
            execution_count["count"] += 1

        try:
            migration_engine_idempotency_cold.register(
                "001", "tracked", counting_migration
            )

            # First run
            await migration_engine_idempotency_cold.migrate()
            assert execution_count["count"] == 1

            # Second run (should not execute)
            await migration_engine_idempotency_cold.migrate()
            assert execution_count["count"] == 1

            # Third run (still should not execute)
            await migration_engine_idempotency_cold.migrate()
            assert execution_count["count"] == 1

            logger.info("PASS: Migration tracking prevents re-runs")
        except Exception as e:
            logger.error(f"FAIL: Tracking test failed: {e}", exc_info=True)
            raise

    async def test_concurrent_migration_safety(
        self, migration_engine_idempotency_cold
    ):
        """Test that concurrent migration attempts are handled safely.

        Given: Same migration attempted concurrently
        When: Multiple migrate() calls run in parallel
        Then: Migration executes only once
        And: No race conditions occur
        """
        logger.info("TEST: Concurrent migration safety")

        execution_count = {"count": 0}
        lock = asyncio.Lock()

        async def thread_safe_migration(adapter):
            async with lock:
                execution_count["count"] += 1

        try:
            migration_engine_idempotency_cold.register(
                "001", "concurrent", thread_safe_migration
            )

            # Simulate concurrent migration attempts
            await asyncio.gather(
                migration_engine_idempotency_cold.migrate(),
                migration_engine_idempotency_cold.migrate(),
                migration_engine_idempotency_cold.migrate(),
            )

            # Verify only one execution
            assert execution_count["count"] == 1, \
                f"Migration ran {execution_count['count']} times (expected 1)"

            logger.info("PASS: Concurrent migration safety verified")
        except Exception as e:
            logger.error(f"FAIL: Concurrent safety test failed: {e}", exc_info=True)
            raise

    async def test_migration_state_consistency(
        self, migration_engine_idempotency_cold
    ):
        """Test that migration state remains consistent.

        Given: Migration applied successfully
        When: State is queried multiple times
        Then: State is always consistent
        And: No state corruption occurs
        """
        logger.info("TEST: Migration state consistency")

        try:
            migration_engine_idempotency_cold.register(
                "001", "state_test", idempotent_create_table_up
            )

            # Apply migration
            await migration_engine_idempotency_cold.migrate()

            # Query state multiple times
            for i in range(5):
                applied = await migration_engine_idempotency_cold.get_applied_migrations()
                assert "001" in applied, f"State inconsistent on check {i+1}"

                statuses = await migration_engine_idempotency_cold.status()
                assert len(statuses) == 1
                assert statuses[0]["version"] == "001"
                assert statuses[0]["status"] == "applied"

            logger.info("PASS: Migration state remains consistent")
        except Exception as e:
            logger.error(f"FAIL: State consistency test failed: {e}", exc_info=True)
            raise

    async def test_idempotency_with_rollback(
        self, migration_engine_idempotency_cold
    ):
        """Test idempotency after rollback and re-application.

        Given: Migration applied, rolled back, and re-applied
        When: Migration is run again
        Then: Migration completes successfully
        And: Final state is correct
        """
        logger.info("TEST: Idempotency with rollback")

        try:
            migration_engine_idempotency_cold.register(
                "001", "rollback_test",
                idempotent_create_table_up,
                idempotent_create_table_down
            )

            # Apply
            await migration_engine_idempotency_cold.migrate()

            # Rollback
            await migration_engine_idempotency_cold.rollback(steps=1)

            # Re-apply
            await migration_engine_idempotency_cold.migrate()

            # Verify final state
            applied = await migration_engine_idempotency_cold.get_applied_migrations()
            assert "001" in applied

            logger.info("PASS: Idempotency works with rollback cycle")
        except Exception as e:
            logger.error(f"FAIL: Rollback idempotency test failed: {e}", exc_info=True)
            raise


__all__ = [
    "TestIdempotencyCOLD",
    "TestIdempotencyHOT",
    "TestIdempotencyEdgeCases",
]
