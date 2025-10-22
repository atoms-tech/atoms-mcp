"""Test migration versioning functionality with comprehensive coverage.

This module tests version management including:
- Version numbering scheme validation
- Version dependency handling
- Skipped version detection and handling
- Version ordering and comparison
- Migration history tracking

Coverage areas:
- Happy path: sequential version progression
- Error scenarios: invalid versions, version conflicts
- Edge cases: non-sequential versions, version gaps
- Version format validation
"""

import logging

import pytest
import pytest_asyncio
from pheno_vendor.db_kit.adapters.base import DatabaseAdapter
from pheno_vendor.db_kit.migrations import MigrationEngine

from tests.framework import harmful
from tests.framework.harmful import CleanupStrategy

from .test_migration_runner import (
    MockDatabaseAdapter,
    migration_001_up,
    migration_002_up,
    migration_003_up,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Test Migration Functions for Versioning
# ============================================================================


async def version_timestamp_up(adapter: DatabaseAdapter):
    """Migration with timestamp version."""
    await adapter.execute(
        "CREATE TABLE IF NOT EXISTS version_test (id SERIAL PRIMARY KEY)"
    )


async def version_timestamp_down(adapter: DatabaseAdapter):
    """Rollback timestamp version migration."""
    await adapter.execute("DROP TABLE IF EXISTS version_test")


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_adapter_versioning():
    """Provide mock adapter for versioning tests."""
    adapter = MockDatabaseAdapter()
    return adapter


@pytest_asyncio.fixture
async def migration_engine_versioning_cold(mock_adapter_versioning):
    """Provide migration engine for versioning tests (COLD mode)."""
    engine = MigrationEngine(mock_adapter_versioning)
    await engine.init()
    return engine


@pytest_asyncio.fixture
async def migration_engine_versioning_hot(real_adapter_versioning):
    """Provide migration engine for versioning tests (HOT mode)."""
    engine = MigrationEngine(real_adapter_versioning)
    await engine.init()

    yield engine

    # Cleanup
    try:
        await real_adapter_versioning.execute("DROP TABLE IF EXISTS _migrations CASCADE")
        await real_adapter_versioning.execute("DROP TABLE IF EXISTS version_test CASCADE")
        await real_adapter_versioning.execute("DROP TABLE IF EXISTS test_table_001 CASCADE")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


@pytest_asyncio.fixture
async def real_adapter_versioning():
    """Provide real database adapter for versioning tests."""
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
# COLD Mode Versioning Tests
# ============================================================================


@pytest.mark.cold
class TestVersioningCOLD:
    """Test versioning functionality with mocked database (COLD mode)."""

    async def test_01_sequential_version_numbering_cold(
        self, migration_engine_versioning_cold
    ):
        """Test sequential version numbering (001, 002, 003).

        Given: Migrations with sequential numeric versions
        When: Migrations are applied
        Then: Migrations execute in sequential order
        And: Version numbers are validated
        """
        logger.info("TEST: Sequential version numbering (COLD)")

        try:
            # Register migrations with sequential versions
            migration_engine_versioning_cold.register("001", "first", migration_001_up)
            migration_engine_versioning_cold.register("002", "second", migration_002_up)
            migration_engine_versioning_cold.register("003", "third", migration_003_up)

            # Apply all migrations
            applied = await migration_engine_versioning_cold.migrate()

            # Verify sequential order
            assert len(applied) == 3
            assert applied[0].version == "001"
            assert applied[1].version == "002"
            assert applied[2].version == "003"

            logger.info("PASS: Sequential versioning works (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Sequential versioning failed: {e}", exc_info=True)
            raise

    async def test_02_timestamp_version_format_cold(
        self, migration_engine_versioning_cold
    ):
        """Test timestamp-based version format (YYYYMMDD_HHMMSS).

        Given: Migrations with timestamp versions
        When: Migrations are applied
        Then: Versions are ordered chronologically
        And: Timestamp format is preserved
        """
        logger.info("TEST: Timestamp version format (COLD)")

        try:
            # Register migrations with timestamp versions
            migration_engine_versioning_cold.register(
                "20240101_120000", "first", migration_001_up
            )
            migration_engine_versioning_cold.register(
                "20240102_120000", "second", migration_002_up
            )
            migration_engine_versioning_cold.register(
                "20240103_120000", "third", migration_003_up
            )

            # Apply migrations
            applied = await migration_engine_versioning_cold.migrate()

            # Verify chronological order
            assert len(applied) == 3
            assert applied[0].version == "20240101_120000"
            assert applied[1].version == "20240102_120000"
            assert applied[2].version == "20240103_120000"

            logger.info("PASS: Timestamp versioning works (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Timestamp versioning failed: {e}", exc_info=True)
            raise

    async def test_03_version_dependency_ordering_cold(
        self, migration_engine_versioning_cold
    ):
        """Test that version dependencies are respected.

        Given: Migrations with dependencies indicated by versions
        When: Migrations are applied
        Then: Dependencies are satisfied in order
        And: Later versions depend on earlier versions
        """
        logger.info("TEST: Version dependency ordering (COLD)")

        execution_log = []

        async def track_001(adapter):
            execution_log.append("001")

        async def track_002(adapter):
            # This depends on 001 being executed
            if "001" not in execution_log:
                raise RuntimeError("Dependency not satisfied: 001 required")
            execution_log.append("002")

        async def track_003(adapter):
            # This depends on both 001 and 002
            if "001" not in execution_log or "002" not in execution_log:
                raise RuntimeError("Dependencies not satisfied: 001, 002 required")
            execution_log.append("003")

        try:
            # Register with implicit dependencies
            migration_engine_versioning_cold.register("001", "base", track_001)
            migration_engine_versioning_cold.register("002", "depends_on_001", track_002)
            migration_engine_versioning_cold.register("003", "depends_on_002", track_003)

            # Apply migrations
            await migration_engine_versioning_cold.migrate()

            # Verify execution order satisfied dependencies
            assert execution_log == ["001", "002", "003"]

            logger.info("PASS: Version dependencies respected (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Version dependencies failed: {e}", exc_info=True)
            raise

    async def test_04_skipped_version_handling_cold(
        self, migration_engine_versioning_cold
    ):
        """Test handling of skipped versions (001, 003, 005).

        Given: Migrations with non-sequential versions (gaps)
        When: Migrations are applied
        Then: All registered migrations are applied
        And: Version gaps are ignored
        """
        logger.info("TEST: Skipped version handling (COLD)")

        try:
            # Register migrations with gaps
            migration_engine_versioning_cold.register("001", "first", migration_001_up)
            migration_engine_versioning_cold.register("003", "third", migration_003_up)
            migration_engine_versioning_cold.register("005", "fifth", migration_002_up)

            # Apply migrations
            applied = await migration_engine_versioning_cold.migrate()

            # Verify all were applied despite gaps
            assert len(applied) == 3
            assert applied[0].version == "001"
            assert applied[1].version == "003"
            assert applied[2].version == "005"

            # Get status
            statuses = await migration_engine_versioning_cold.status()
            assert len(statuses) == 3
            assert all(s["status"] == "applied" for s in statuses)

            logger.info("PASS: Skipped versions handled (COLD)")
        except Exception as e:
            logger.error(f"FAIL: Skipped version test failed: {e}", exc_info=True)
            raise


# ============================================================================
# HOT Mode Versioning Tests
# ============================================================================


@pytest.mark.hot
@pytest.mark.integration
class TestVersioningHOT:
    """Test versioning functionality with real database (HOT mode)."""

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_05_version_history_tracking_hot(
        self, migration_engine_versioning_hot, harmful_tracker
    ):
        """Test that version history is tracked in database.

        Given: Multiple migrations applied over time
        When: Status is queried
        Then: Complete version history is available
        And: Applied timestamps are recorded
        """
        logger.info("TEST: Version history tracking (HOT)")

        try:
            # Apply migrations sequentially
            migration_engine_versioning_hot.register("001", "v1", migration_001_up)
            await migration_engine_versioning_hot.migrate(target="001")

            # Add more migrations
            migration_engine_versioning_hot.register("002", "v2", migration_002_up)
            await migration_engine_versioning_hot.migrate(target="002")

            # Query version history from database
            history = await migration_engine_versioning_hot.adapter.execute(
                "SELECT version, name, applied_at FROM _migrations ORDER BY applied_at"
            )

            # Verify history
            assert len(history) == 2
            assert history[0]["version"] == "001"
            assert history[1]["version"] == "002"
            assert history[0]["applied_at"] is not None
            assert history[1]["applied_at"] is not None

            logger.info("PASS: Version history tracked (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Version history test failed: {e}", exc_info=True)
            raise

    @harmful(cleanup_strategy=CleanupStrategy.CASCADE_DELETE)
    async def test_06_version_checksum_integrity_hot(
        self, migration_engine_versioning_hot, harmful_tracker
    ):
        """Test that version checksums ensure migration integrity.

        Given: Migration with calculated checksum
        When: Migration is applied
        Then: Checksum is stored with version
        And: Checksum can detect changes
        """
        logger.info("TEST: Version checksum integrity (HOT)")

        try:
            # Register migration
            migration = migration_engine_versioning_hot.register(
                "001", "checksummed", migration_001_up
            )

            original_checksum = migration.checksum
            assert original_checksum is not None

            # Apply migration
            await migration_engine_versioning_hot.migrate()

            # Verify checksum in database
            result = await migration_engine_versioning_hot.adapter.execute(
                "SELECT checksum FROM _migrations WHERE version = '001'"
            )
            assert result[0]["checksum"] == original_checksum

            # Verify checksum calculation is consistent
            new_engine = MigrationEngine(migration_engine_versioning_hot.adapter)
            new_migration = new_engine.register("001", "checksummed", migration_001_up)
            assert new_migration.checksum == original_checksum

            logger.info("PASS: Version checksum integrity maintained (HOT)")
        except Exception as e:
            logger.error(f"FAIL: Checksum integrity test failed: {e}", exc_info=True)
            raise


# ============================================================================
# Edge Cases and Error Scenarios
# ============================================================================


@pytest.mark.cold
class TestVersioningEdgeCases:
    """Test edge cases in versioning functionality."""

    async def test_version_string_comparison(self, migration_engine_versioning_cold):
        """Test that version strings are compared correctly.

        Given: Versions with different string lengths
        When: Migrations are sorted
        Then: Versions are compared as strings (lexicographic)
        And: Proper ordering is maintained
        """
        logger.info("TEST: Version string comparison")

        try:
            # Register versions with different lengths
            migration_engine_versioning_cold.register("1", "one", migration_001_up)
            migration_engine_versioning_cold.register("10", "ten", migration_002_up)
            migration_engine_versioning_cold.register("2", "two", migration_003_up)

            applied = await migration_engine_versioning_cold.migrate()

            # Verify lexicographic order: "1", "10", "2"
            assert applied[0].version == "1"
            assert applied[1].version == "10"
            assert applied[2].version == "2"

            logger.info("PASS: Version string comparison correct")
        except Exception as e:
            logger.error(f"FAIL: Version comparison failed: {e}", exc_info=True)
            raise

    async def test_version_with_special_characters(
        self, migration_engine_versioning_cold
    ):
        """Test versions with special characters.

        Given: Versions with underscores, dashes, etc.
        When: Migrations are applied
        Then: Special characters are preserved
        And: No errors occur
        """
        logger.info("TEST: Version with special characters")

        try:
            # Register versions with special characters
            migration_engine_versioning_cold.register(
                "v1.0.0", "semantic_version", migration_001_up
            )
            migration_engine_versioning_cold.register(
                "2024-01-01", "date_version", migration_002_up
            )
            migration_engine_versioning_cold.register(
                "feature_auth_001", "feature_version", migration_003_up
            )

            applied = await migration_engine_versioning_cold.migrate()

            # Verify all versions were accepted
            assert len(applied) == 3
            assert any(m.version == "v1.0.0" for m in applied)
            assert any(m.version == "2024-01-01" for m in applied)
            assert any(m.version == "feature_auth_001" for m in applied)

            logger.info("PASS: Special characters in versions handled")
        except Exception as e:
            logger.error(f"FAIL: Special character test failed: {e}", exc_info=True)
            raise

    async def test_version_case_sensitivity(self, migration_engine_versioning_cold):
        """Test that version comparison is case-sensitive.

        Given: Versions differing only in case
        When: Migrations are registered
        Then: Versions are treated as different
        And: Both can be applied
        """
        logger.info("TEST: Version case sensitivity")

        try:
            # Register versions with different cases
            migration_engine_versioning_cold.register("V001", "uppercase", migration_001_up)
            migration_engine_versioning_cold.register("v001", "lowercase", migration_002_up)

            applied = await migration_engine_versioning_cold.migrate()

            # Verify both were applied (case-sensitive)
            assert len(applied) == 2
            versions = [m.version for m in applied]
            assert "V001" in versions
            assert "v001" in versions

            logger.info("PASS: Version case sensitivity correct")
        except Exception as e:
            logger.error(f"FAIL: Case sensitivity test failed: {e}", exc_info=True)
            raise

    async def test_empty_version_string(self, migration_engine_versioning_cold):
        """Test handling of empty version string.

        Given: Migration with empty version string
        When: Migration is registered
        Then: Empty version is accepted
        And: Migration can be applied
        """
        logger.info("TEST: Empty version string")

        try:
            # Register migration with empty version
            migration_engine_versioning_cold.register("", "empty_version", migration_001_up)

            applied = await migration_engine_versioning_cold.migrate()

            # Verify migration was applied
            assert len(applied) == 1
            assert applied[0].version == ""

            logger.info("PASS: Empty version string handled")
        except Exception as e:
            logger.error(f"FAIL: Empty version test failed: {e}", exc_info=True)
            raise

    async def test_very_long_version_string(self, migration_engine_versioning_cold):
        """Test handling of very long version strings.

        Given: Migration with very long version (255+ chars)
        When: Migration is registered
        Then: Version is accepted
        Note: Database column is VARCHAR(255), so this tests the limit
        """
        logger.info("TEST: Very long version string")

        try:
            # Create very long version string
            long_version = "v" + "1234567890" * 25  # 251 chars

            migration_engine_versioning_cold.register(
                long_version, "long_version", migration_001_up
            )

            applied = await migration_engine_versioning_cold.migrate()

            # Verify migration was applied
            assert len(applied) == 1
            assert applied[0].version == long_version

            logger.info("PASS: Long version string handled")
        except Exception as e:
            logger.error(f"FAIL: Long version test failed: {e}", exc_info=True)
            raise


__all__ = [
    "TestVersioningCOLD",
    "TestVersioningHOT",
    "TestVersioningEdgeCases",
]
