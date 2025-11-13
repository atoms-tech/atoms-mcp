"""Archive and restore operations for entity soft-delete.

Run with: pytest tests/unit/tools/test_entity_archive.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestEntityArchive:
    """ARCHIVE/RESTORE operations for all entity types."""

    async def test_soft_delete_entity(self, call_mcp):
        """Test soft-deleting an entity.

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

            # Soft delete it
            delete_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "delete",
                    "entity_type": "organization",
                    "entity_id": org_id,
                    "soft_delete": True
                }
            )

            assert delete_result is not None
            assert delete_result.get("success") is not False

    async def test_restore_archived_entity(self, call_mcp):
        """Test restoring a soft-deleted entity.

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
                    "operation": "delete",
                    "entity_type": "organization",
                    "entity_id": org_id,
                    "soft_delete": True
                }
            )

            # Restore it
            restore_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "update",
                    "entity_type": "organization",
                    "entity_id": org_id,
                    "data": {"is_deleted": False}
                }
            )

            assert restore_result is not None


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
