"""Unit tests for Phase 2 Week 3: Deprecation Manager.

Tests deprecation warnings, migration tracking, and timeline management.
"""

import pytest
import warnings
from services.deprecation_manager import (
    DeprecationManager,
    DeprecationLevel,
    get_deprecation_manager
)


class TestDeprecationManagerPhase2:
    """Test Phase 2 deprecation manager."""

    @pytest.fixture
    def deprecation_manager(self):
        """Get deprecation manager instance."""
        return DeprecationManager()

    # ========== Deprecation Setup Tests ==========

    def test_query_tool_deprecated(self, deprecation_manager):
        """Test query_tool is marked as deprecated."""
        assert deprecation_manager.is_deprecated("query_tool")

    def test_query_tool_replacement(self, deprecation_manager):
        """Test query_tool replacement is entity_tool."""
        replacement = deprecation_manager.get_replacement("query_tool")
        assert replacement == "entity_tool"

    def test_query_tool_has_migration_guide(self, deprecation_manager):
        """Test query_tool has migration guide."""
        guide = deprecation_manager.get_migration_guide("query_tool")
        assert guide is not None
        assert "migration" in guide.lower()

    def test_query_tool_has_removal_date(self, deprecation_manager):
        """Test query_tool has removal date."""
        removal_date = deprecation_manager.get_removal_date("query_tool")
        assert removal_date is not None

    # ========== Deprecation Warning Tests ==========

    def test_warn_deprecated(self, deprecation_manager):
        """Test deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            deprecation_manager.warn_deprecated("query_tool")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "query_tool" in str(w[0].message)

    def test_warn_deprecated_with_custom_message(self, deprecation_manager):
        """Test deprecation warning with custom message."""
        custom_msg = "Custom deprecation message"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            deprecation_manager.warn_deprecated("query_tool", message=custom_msg)

            assert len(w) == 1
            assert custom_msg in str(w[0].message)

    def test_warn_nonexistent_api(self, deprecation_manager):
        """Test warning for non-existent API does nothing."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            deprecation_manager.warn_deprecated("nonexistent_api")

            # Should not raise warning for non-existent API
            assert len(w) == 0

    # ========== Deprecation Info Tests ==========

    def test_get_deprecation_info(self, deprecation_manager):
        """Test getting deprecation info."""
        info = deprecation_manager.get_deprecation_info("query_tool")

        assert info is not None
        assert info["name"] == "query_tool"
        assert info["replacement"] == "entity_tool"
        assert "deprecated_date" in info
        assert "removal_date" in info

    def test_get_deprecation_info_nonexistent(self, deprecation_manager):
        """Test getting info for non-existent API."""
        info = deprecation_manager.get_deprecation_info("nonexistent")
        assert info is None

    def test_get_all_deprecations(self, deprecation_manager):
        """Test getting all deprecations."""
        all_deprecations = deprecation_manager.get_all_deprecations()

        assert isinstance(all_deprecations, dict)
        assert len(all_deprecations) > 0
        assert "query_tool" in all_deprecations

    # ========== Add Deprecation Tests ==========

    def test_add_deprecation(self, deprecation_manager):
        """Test adding new deprecation."""
        deprecation_manager.add_deprecation(
            api_name="old_api",
            replacement="new_api",
            level=DeprecationLevel.WARNING,
            removal_days=60,
            migration_guide="https://example.com/migration",
            reason="Replaced with new_api"
        )

        assert deprecation_manager.is_deprecated("old_api")
        assert deprecation_manager.get_replacement("old_api") == "new_api"

    def test_add_deprecation_critical(self, deprecation_manager):
        """Test adding critical deprecation."""
        deprecation_manager.add_deprecation(
            api_name="critical_api",
            replacement="new_critical_api",
            level=DeprecationLevel.CRITICAL,
            removal_days=30
        )

        info = deprecation_manager.get_deprecation_info("critical_api")
        assert info["level"] == DeprecationLevel.CRITICAL

    # ========== Migration Guide Tests ==========

    def test_get_migration_guide(self, deprecation_manager):
        """Test getting migration guide."""
        guide = deprecation_manager.get_migration_guide("query_tool")

        assert guide is not None
        assert isinstance(guide, str)

    def test_get_migration_guide_nonexistent(self, deprecation_manager):
        """Test getting migration guide for non-existent API."""
        guide = deprecation_manager.get_migration_guide("nonexistent")
        assert guide is None

    # ========== Removal Date Tests ==========

    def test_get_removal_date(self, deprecation_manager):
        """Test getting removal date."""
        removal_date = deprecation_manager.get_removal_date("query_tool")

        assert removal_date is not None
        assert isinstance(removal_date, str)

    def test_get_removal_date_nonexistent(self, deprecation_manager):
        """Test getting removal date for non-existent API."""
        removal_date = deprecation_manager.get_removal_date("nonexistent")
        assert removal_date is None

    # ========== Deprecation Level Tests ==========

    def test_deprecation_levels(self):
        """Test deprecation levels."""
        assert DeprecationLevel.WARNING.value == "warning"
        assert DeprecationLevel.CRITICAL.value == "critical"
        assert DeprecationLevel.REMOVED.value == "removed"

    # ========== Singleton Tests ==========

    def test_deprecation_manager_singleton(self):
        """Test deprecation manager singleton."""
        manager1 = get_deprecation_manager()
        manager2 = get_deprecation_manager()

        assert manager1 is manager2

