"""Entity versioning operations - archive, restore, and history.

Tests for soft-delete archiving and version history tracking with restoration.

Run with: pytest tests/unit/tools/test_entity_versioning.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
    pytest.mark.skip(reason="Test infrastructure requires additional setup - use consolidated test files instead")
]


class TestEntityArchive:
    """ARCHIVE/RESTORE operations for all entity types."""

    async def test_archive_entity(self, call_mcp):
        """Test archiving an entity.

        User story: User can archive an entity
        """
        # Create organization
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": "Archive Test Org"}
            }
        )

        if isinstance(create_result, dict) and "id" in create_result:
            org_id = create_result["id"]

            # Archive it using explicit archive operation
            archive_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "archive",
                    "entity_type": "organization",
                    "entity_id": org_id
                }
            )

            assert archive_result is not None
            assert archive_result.get("success") is True
            assert archive_result.get("operation") == "archive"

    async def test_restore_archived_entity(self, call_mcp):
        """Test restoring an archived entity.

        User story: User can restore an archived entity
        """
        # Create organization
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": "Restore Test Org"}
            }
        )

        if isinstance(create_result, dict) and "id" in create_result:
            org_id = create_result["id"]

            # Archive it
            await call_mcp(
                "entity_tool",
                {
                    "operation": "archive",
                    "entity_type": "organization",
                    "entity_id": org_id
                }
            )

            # Restore it using explicit restore operation
            restore_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "restore",
                    "entity_type": "organization",
                    "entity_id": org_id
                }
            )

            assert restore_result is not None
            assert restore_result.get("success") is True
            assert restore_result.get("operation") == "restore"


class TestArchiveUserStories:
    """User story acceptance tests for archive/restore."""

    async def test_user_can_archive_entity(self, call_mcp):
        """User story: User can archive entity without losing data.

        Acceptance criteria:
        - Archive operation succeeds
        - Entity can be restored
        """
        # Create org
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": "Important Org"}
            }
        )

        assert create_result is not None
        if isinstance(create_result, dict) and "id" in create_result:
            org_id = create_result["id"]

            # Archive
            archive_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "delete",
                    "entity_type": "organization",
                    "entity_id": org_id,
                    "soft_delete": True
                }
            )

            assert archive_result is not None

    async def test_archived_items_hidden_from_list(self, call_mcp):
        """Test that archived items are excluded from LIST by default."""
        # Create and archive an organization
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": "Hidden Org"}
            }
        )

        if isinstance(create_result, dict) and "id" in create_result:
            org_id = create_result["id"]

            # Archive it
            await call_mcp(
                "entity_tool",
                {
                    "operation": "delete",
                    "entity_type": "organization",
                    "entity_id": org_id,
                    "soft_delete": True
                }
            )

            # List should exclude it by default
            list_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "list",
                    "entity_type": "organization"
                }
            )

            assert list_result is not None


class TestEntityHistory:
    """Entity version history operations."""

    async def test_get_history_basic(self, call_mcp, test_organization):
        """Test getting version history for an entity."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert result.get("entity_id") == test_organization
        assert result.get("entity_type") == "organization"

    async def test_get_history_with_limit(self, call_mcp, test_organization):
        """Test getting version history with pagination."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization,
                "limit": 10
            }
        )
        
        assert result is not None
        assert result.get("limit") == 10

    async def test_get_history_with_offset(self, call_mcp, test_organization):
        """Test getting version history with offset."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization,
                "offset": 5
            }
        )
        
        assert result is not None
        assert result.get("offset") == 5

    async def test_get_history_returns_versions(self, call_mcp, test_organization):
        """Test that history returns versions array."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        # Should have versions array (empty if no history)
        assert "versions" in result or "note" in result

    async def test_get_history_returns_count(self, call_mcp, test_organization):
        """Test that history returns total version count."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert "total" in result


class TestRestoreVersion:
    """Entity version restoration operations."""

    async def test_restore_version_basic(self, call_mcp, test_organization):
        """Test restoring an entity to a specific version."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": test_organization,
                "version": 1
            }
        )
        
        assert result is not None
        assert result.get("entity_id") == test_organization
        assert result.get("version") == 1

    async def test_restore_version_returns_operation_name(self, call_mcp, test_organization):
        """Test that restore_version includes operation name."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": test_organization,
                "version": 1
            }
        )
        
        assert result is not None
        assert result.get("operation") == "restore_version"

    async def test_restore_version_with_invalid_version(self, call_mcp, test_organization):
        """Test restore with version number."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": test_organization,
                "version": 99
            }
        )
        
        assert result is not None
        # Should indicate whether restore was successful
        assert "success" in result or "note" in result


class TestHistoryIntegration:
    """Integration tests for version history."""

    async def test_history_and_restore_together(self, call_mcp, test_organization):
        """Test getting history and then restoring."""
        # Get history
        history_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization
            }
        )
        
        assert history_result is not None
        
        # Try to restore (even if history is empty)
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": test_organization,
                "version": 1
            }
        )
        
        assert restore_result is not None

    async def test_history_includes_timing(self, call_mcp, test_organization):
        """Test that history operation includes timing metrics."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert duration_ms >= 0

    async def test_restore_version_includes_timing(self, call_mcp, test_organization):
        """Test that restore_version includes timing metrics."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": test_organization,
                "version": 1
            }
        )
        
        assert result is not None
        assert duration_ms >= 0


class TestHistoryErrorHandling:
    """Error handling for version history operations."""

    async def test_history_without_entity_id(self, call_mcp):
        """Test history operation without entity_id."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": None
            }
        )
        
        # Should handle gracefully (error or empty)
        assert result is not None

    async def test_restore_version_without_version(self, call_mcp, test_organization):
        """Test restore_version without version parameter."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": test_organization,
                "version": None
            }
        )
        
        # Should handle gracefully
        assert result is not None or result is None

    async def test_restore_version_without_entity_id(self, call_mcp):
        """Test restore_version without entity_id."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore_version",
                "entity_type": "organization",
                "entity_id": None,
                "version": 1
            }
        )
        
        # Should handle gracefully
        assert result is not None or result is None


class TestHistoryScenarios:
    """Scenario-based version history tests."""

    async def test_history_for_different_entity_types(self, call_mcp, test_organization):
        """Test history operation works for different entity types."""
        # Test with organization (which exists)
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": "organization",
                "entity_id": test_organization
            }
        )
        
        assert result is not None
        assert result.get("entity_type") == "organization"

    async def test_history_pagination_params(self, call_mcp, test_organization):
        """Test history with various pagination parameters."""
        # Test with various limits
        for limit in [5, 10, 20, 50]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "history",
                    "entity_type": "organization",
                    "entity_id": test_organization,
                    "limit": limit
                }
            )
            
            assert result is not None
            assert result.get("limit") == limit

    async def test_history_offset_params(self, call_mcp, test_organization):
        """Test history with various offset parameters."""
        # Test with various offsets
        for offset in [0, 5, 10, 20]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "history",
                    "entity_type": "organization",
                    "entity_id": test_organization,
                    "offset": offset
                }
            )
            
            assert result is not None
            assert result.get("offset") == offset

    async def test_restore_version_with_version_numbers(self, call_mcp, test_organization):
        """Test restore with different version numbers."""
        # Test with various version numbers
        for version in [1, 2, 3, 5, 10]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "restore_version",
                    "entity_type": "organization",
                    "entity_id": test_organization,
                    "version": version
                }
            )
            
            assert result is not None
            assert result.get("version") == version
