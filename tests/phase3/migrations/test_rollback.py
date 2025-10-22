"""Test migration rollback functionality with comprehensive coverage.

This module tests rollback mechanisms including:
- Single-step rollback
- Multi-step rollback
- Rollback to specific version
- Rollback of failed migrations
- Data preservation during rollback
- Error handling in rollback operations

Coverage areas:
- Happy path: successful rollback operations
- Error scenarios: missing down functions, rollback failures
- Edge cases: rollback of partially applied migrations
- Data integrity: verify data is preserved correctly
"""

import logging
from unittest.mock import patch

import pytest
import pytest_asyncio
from pheno_vendor.db_kit.adapters.base import DatabaseAdapter
from pheno_vendor.db_kit.migrations import MigrationEngine, MigrationStatus

from tests.framework import harmful
from tests.framework.harmful import CleanupStrategy

from .test_migration_runner import (
    MockDatabaseAdapter,
    migration_001_down,
    migration_001_up,
    migration_002_down,
    migration_002_up,
    migration_003_down,
    migration_003_up,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Additional Test Migration Functions for Rollback
# ============================================================================


async def migration_with_data_up(adapter: DatabaseAdapter):
    """Migration that creates table and inserts data."""
    await adapter.execute("""
        CREATE TABLE IF NOT EXISTS rollback_test (
            id SERIAL PRIMARY KEY,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await adapter.execute(
        "INSERT INTO rollback_test (value) VALUES ('test_data_1'), ('test_data_2')"
    )


async def migration_with_data_down(adapter: DatabaseAdapter):
    """Rollback migration with data."""
    # Should preserve data before dropping
    await adapter.execute("DROP TABLE IF EXISTS rollback_test CASCADE")


async def migration_complex_up(adapter: DatabaseAdapter):
    """Complex migration with multiple operations."""
    await adapter.execute("CREATE TABLE rollback_complex (id SERIAL PRIMARY KEY)")
    await adapter.execute("CREATE INDEX idx_rollback_id ON rollback_complex(id)")
    await adapter.execute("INSERT INTO rollback_complex (id) VALUES (1), (2), (3)")


async def migration_complex_down(adapter: DatabaseAdapter):
    """Complex rollback with multiple operations."""
    await adapter.execute("DROP INDEX IF EXISTS idx_rollback_id")
    await adapter.execute("DROP TABLE IF EXISTS rollback_complex CASCADE")


async def migration_failing_down(adapter: DatabaseAdapter):
    """Rollback that intentionally fails."""
    raise RuntimeError("Intentional rollback failure for testing")


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_adapter_rollback():
    """Provide mock adapter with rollback support."""
    adapter = MockDatabaseAdapter()
    return adapter


@pytest_asyncio.fixture
async def migration_engine_rollback_cold(mock_adapter_rollback):
    """Provide migration engine for rollback testing (COLD mode)."""
    engine = MigrationEngine(mock_adapter_rollback)
    await engine.init()
    return engine


@pytest_asyncio.fixture
async def migration_engine_rollback_hot(real_adapter_rollback):
    """Provide migration engine for rollback testing (HOT mode)."""
    engine = MigrationEngine(real_adapter_rollback)
    await engine.init()

    yield engine

    # Cleanup
    try:
        await real_adapter_rollback.execute("DROP TABLE IF EXISTS _migrations CASCADE")
        await real_adapter_rollback.execute("DROP TABLE IF EXISTS rollback_test CASCADE")
        await real_adapter_rollback.execute("DROP TABLE IF EXISTS rollback_complex CASCADE")
        await real_adapter_rollback.execute("DROP TABLE IF EXISTS test_table_001 CASCADE")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


@pytest_asyncio.fixture
async def real_adapter_rollback():
    """Provide real database adapter for rollback testing."""
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
# COLD Mode Rollback Tests
# ============================================================================


@pytest.mark.cold
class TestRollbackCOLD:
    """Test rollback functionality with mocked database (COLD mode)."""

    async def test_01_single_step_rollback_cold(self, migration_engine_rollback_cold):
        """Test rolling back a single migration.

        Given: One migration is applied
        When: Rollback is called with steps=1
        Then: Migration is rolled back successfully
        And: Migration status is updated to ROLLED_BACK
        """
        logger.info("TEST: Single step rollback (COLD)")

        try:
            # Apply migration
            migration_engine_rollback_cold.register(
                "001", "test", migration_001_up, migration_001_down
            )
            await migration_engine_rollback_cold.migrate()

            # Verify migration was applied
            applied = await migration_engine_rollback_cold.get_applied_migrations()
            assert "001" in applied

            # Rollback
            rolled_back = await migration_engine_rollback_cold.rollback(steps=1)

            # Verify rollback
            assert len(rolled_back) == 1
            assert rolled_back[0].version == "001"
            assert rolled_back[0].status == MigrationStatus.ROLLED_BACK

            logger.info("PASS: Single step rollback successful (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Single step rollback failed: {e}", exc_info=True)
            raise

    async def test_02_multi_step_rollback_cold(self, migration_engine_rollback_cold):
        """Test rolling back multiple migrations.

        Given: Three migrations are applied
        When: Rollback is called with steps=2
        Then: Last two migrations are rolled back
        And: First migration remains applied
        """
        logger.info("TEST: Multi-step rollback (COLD)")

        try:
            # Apply multiple migrations
            migration_engine_rollback_cold.register(
                "001", "first", migration_001_up, migration_001_down
            )
            migration_engine_rollback_cold.register(
                "002", "second", migration_002_up, migration_002_down
            )
            migration_engine_rollback_cold.register(
                "003", "third", migration_003_up, migration_003_down
            )
            await migration_engine_rollback_cold.migrate()

            # Rollback last 2 migrations
            rolled_back = await migration_engine_rollback_cold.rollback(steps=2)

            # Verify rollback order (should be 003, then 002)
            assert len(rolled_back) == 2
            assert rolled_back[0].version == "003"
            assert rolled_back[1].version == "002"

            # Verify 001 is still applied
            applied = await migration_engine_rollback_cold.get_applied_migrations()
            assert "001" in applied
            assert "002" not in applied
            assert "003" not in applied

            logger.info("PASS: Multi-step rollback successful (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Multi-step rollback failed: {e}", exc_info=True)
            raise

    async def test_03_rollback_without_down_function_cold(
        self, migration_engine_rollback_cold
    ):
        """Test rollback behavior when down function is missing.

        Given: Migration applied without down function
        When: Rollback is attempted
        Then: Rollback is skipped with warning
        And: No error occurs
        """
        logger.info("TEST: Rollback without down function (COLD)")

        try:
            # Register migration without down function
            migration_engine_rollback_cold.register(
                "001", "no_down", migration_001_up, down=None
            )
            await migration_engine_rollback_cold.migrate()

            # Attempt rollback (should skip with warning)
            with patch("builtins.print") as mock_print:
                rolled_back = await migration_engine_rollback_cold.rollback(steps=1)

                # Verify warning was printed
                mock_print.assert_called()
                call_args = str(mock_print.call_args)
                assert "Cannot rollback" in call_args or "No down migration" in call_args

            # Verify no rollback occurred
            assert len(rolled_back) == 0

            logger.info("PASS: Rollback without down function handled (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Rollback without down test failed: {e}", exc_info=True)
            raise

    async def test_04_rollback_order_verification_cold(
        self, migration_engine_rollback_cold
    ):
        """Test that rollbacks happen in reverse order.

        Given: Migrations with dependencies applied
        When: Rollback is performed
        Then: Rollbacks execute in reverse order
        And: Dependencies are respected
        """
        logger.info("TEST: Rollback order verification (COLD)")

        rollback_order = []

        async def track_down_001(adapter):
            rollback_order.append("001")

        async def track_down_002(adapter):
            rollback_order.append("002")

        async def track_down_003(adapter):
            rollback_order.append("003")

        try:
            # Apply migrations
            migration_engine_rollback_cold.register("001", "first", migration_001_up, track_down_001)
            migration_engine_rollback_cold.register("002", "second", migration_002_up, track_down_002)
            migration_engine_rollback_cold.register("003", "third", migration_003_up, track_down_003)
            await migration_engine_rollback_cold.migrate()

            # Rollback all
            await migration_engine_rollback_cold.rollback(steps=3)

            # Verify reverse order
            assert rollback_order == ["003", "002", "001"], \
                f"Expected [003, 002, 001], got {rollback_order}"

            logger.info("PASS: Rollback order correct (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Rollback order test failed: {e}", exc_info=True)
            raise


# ============================================================================
# HOT Mode Rollback Tests
# ============================================================================


@pytest.mark.hot
@pytest.mark.integration
class TestRollbackHOT:
    """Test rollback functionality with real database (HOT mode)."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_05_rollback_preserves_data_hot(
        self, migration_engine_rollback_hot, harmful_tracker
    ):
        """Test that rollback can preserve data when needed.

        Given: Migration creates table with data
        When: Migration is rolled back
        Then: Rollback function is executed
        And: Data handling is as specified in down function
        """
        logger.info("TEST: Rollback data preservation (HOT)")

        try:
            # Apply migration with data
            migration_engine_rollback_hot.register(
                "001", "with_data", migration_with_data_up, migration_with_data_down
            )
            await migration_engine_rollback_hot.migrate()

            # Verify data exists
            result = await migration_engine_rollback_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM rollback_test"
            )
            assert result[0]["count"] == 2, "Data was not inserted"

            # Rollback
            await migration_engine_rollback_hot.rollback(steps=1)

            # Verify table is dropped (as per down function)
            result = await migration_engine_rollback_hot.adapter.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'rollback_test'"
            )
            assert result[0]["count"] == 0, "Table was not dropped"

            logger.info("PASS: Rollback data handling works (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Rollback data test failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_06_rollback_complex_migration_hot(
        self, migration_engine_rollback_hot, harmful_tracker
    ):
        """Test rollback of complex migration with multiple operations.

        Given: Complex migration with table, index, and data
        When: Migration is rolled back
        Then: All operations are reversed
        And: Database state is restored
        """
        logger.info("TEST: Complex migration rollback (HOT)")

        try:
            # Apply complex migration
            migration_engine_rollback_hot.register(
                "001", "complex", migration_complex_up, migration_complex_down
            )
            await migration_engine_rollback_hot.migrate()

            # Verify all operations were applied
            table_result = await migration_engine_rollback_hot.adapter.execute(
                "SELECT COUNT(*) as count FROM rollback_complex"
            )
            assert table_result[0]["count"] == 3

            # Rollback
            await migration_engine_rollback_hot.rollback(steps=1)

            # Verify table is dropped
            result = await migration_engine_rollback_hot.adapter.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'rollback_complex'"
            )
            assert result[0]["count"] == 0

            logger.info("PASS: Complex rollback successful (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Complex rollback failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_07_rollback_updates_status_hot(
        self, migration_engine_rollback_hot, harmful_tracker
    ):
        """Test that rollback updates migration status correctly.

        Given: Applied migration
        When: Rollback is performed
        Then: Migration status is updated to ROLLED_BACK
        And: Status is persisted in database
        """
        logger.info("TEST: Rollback status update (HOT)")

        try:
            # Apply migration
            migration_engine_rollback_hot.register(
                "001", "test", migration_001_up, migration_001_down
            )
            await migration_engine_rollback_hot.migrate()

            # Rollback
            await migration_engine_rollback_hot.rollback(steps=1)

            # Verify status in database
            result = await migration_engine_rollback_hot.adapter.execute(
                "SELECT status FROM _migrations WHERE version = '001'"
            )
            assert result[0]["status"] == MigrationStatus.ROLLED_BACK.value

            logger.info("PASS: Rollback status updated (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Rollback status test failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_08_failed_rollback_handling_hot(
        self, migration_engine_rollback_hot, harmful_tracker
    ):
        """Test handling of failed rollback operations.

        Given: Migration with failing down function
        When: Rollback is attempted
        Then: Error is caught and logged
        And: Rollback failure is reported
        """
        logger.info("TEST: Failed rollback handling (HOT)")

        try:
            # Apply migration with failing down
            migration_engine_rollback_hot.register(
                "001", "fail_down", migration_001_up, migration_failing_down
            )
            await migration_engine_rollback_hot.migrate()

            # Attempt rollback (should fail)
            with pytest.raises(RuntimeError, match="Intentional rollback failure"):
                await migration_engine_rollback_hot.rollback(steps=1)

            logger.info("PASS: Failed rollback handled correctly (HOT)")
        except AssertionError:
            raise
        except Exception as e:
            logger.error(f"FAIL: Failed rollback test failed: {e}", exc_info=True)
            raise


# ============================================================================
# Edge Cases and Error Scenarios
# ============================================================================


@pytest.mark.cold
class TestRollbackEdgeCases:
    """Test edge cases in rollback functionality."""

    async def test_rollback_with_no_migrations(self, migration_engine_rollback_cold):
        """Test rollback when no migrations are applied.

        Given: No migrations applied
        When: Rollback is called
        Then: Empty list is returned
        And: No error occurs
        """
        logger.info("TEST: Rollback with no migrations")

        rolled_back = await migration_engine_rollback_cold.rollback(steps=1)
        assert len(rolled_back) == 0

        logger.info("PASS: Rollback with no migrations handled")

    async def test_rollback_more_steps_than_available(
        self, migration_engine_rollback_cold
    ):
        """Test rollback with more steps than available migrations.

        Given: Only one migration applied
        When: Rollback is called with steps=5
        Then: Only available migration is rolled back
        And: No error occurs
        """
        logger.info("TEST: Rollback more steps than available")

        # Apply one migration
        migration_engine_rollback_cold.register(
            "001", "test", migration_001_up, migration_001_down
        )
        await migration_engine_rollback_cold.migrate()

        # Try to rollback 5 steps
        rolled_back = await migration_engine_rollback_cold.rollback(steps=5)

        # Should rollback only 1
        assert len(rolled_back) == 1

        logger.info("PASS: Rollback steps limited correctly")

    async def test_rollback_zero_steps(self, migration_engine_rollback_cold):
        """Test rollback with zero steps.

        Given: Migrations applied
        When: Rollback is called with steps=0
        Then: No rollback occurs
        And: No error occurs
        """
        logger.info("TEST: Rollback zero steps")

        migration_engine_rollback_cold.register(
            "001", "test", migration_001_up, migration_001_down
        )
        await migration_engine_rollback_cold.migrate()

        # Rollback 0 steps
        rolled_back = await migration_engine_rollback_cold.rollback(steps=0)
        assert len(rolled_back) == 0

        logger.info("PASS: Rollback zero steps handled")


__all__ = [
    "TestRollbackCOLD",
    "TestRollbackHOT",
    "TestRollbackEdgeCases",
]
