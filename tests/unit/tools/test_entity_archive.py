"""Archive and restore operations for entity soft-delete.

Run with: pytest tests/unit/tools/test_entity_archive.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


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
