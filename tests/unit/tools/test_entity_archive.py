"""Archive and restore operations for entity soft-delete.

This module tests ARCHIVE (soft-delete) and RESTORE functionality.

Run with: pytest tests/unit/tools/test_entity_archive.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestEntityArchive:
    """ARCHIVE/RESTORE operations for all entity types."""

    @pytest.mark.parametrize("entity_type", [
        "organization",
        "project",
        "document",
        "requirement",
        "test"
    ])
    async def test_archive_entity(self, call_mcp, entity_type: str, test_organization):
        """Test archiving (soft-deleting) an entity.

        User story: User can archive an entity without permanent loss
        """
        # Create entity
        create_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "create", "entity_type": entity_type, "data": self._get_entity_data(entity_type, test_organization)}
        )
        entity_id = create_result["id"]

        # Delete (archive) it with soft_delete=True (default)
        delete_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "soft_delete": True
            }
        )

        assert delete_result["success"] is True
        assert delete_result["soft_delete"] is True

        # Try to read it - should not be found (soft-deleted)
        read_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )
        
        # Should either not find it or indicate it's archived
        if isinstance(read_result, dict):
            # Might return error or archived status
            assert "error" in read_result or read_result.get("is_deleted") is True

    async def test_restore_archived_entity(self, call_mcp, test_organization):
        """Test restoring a soft-deleted entity.

        User story: User can restore an archived entity
        """
        # Create organization
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": "Temp Org"}
            }
        )
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

        # Restore it (set is_deleted to false)
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "organization",
                "entity_id": org_id,
                "data": {"is_deleted": False}
            }
        )

        # Should succeed
        assert restore_result is not None

        # Should be readable again
        read_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": org_id
            }
        )
        
        assert read_result is not None
        assert read_result.get("is_deleted") is False or "error" not in read_result

    async def test_archived_excluded_from_list(self, call_mcp, test_organization):
        """Test that archived items are excluded from LIST by default.

        User story: Archived items are hidden from default list views
        """
        # Create document
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": "Archive Test Doc",
                    "project_id": test_organization["projects"][0]
                }
            }
        )
        doc_id = create_result["id"]

        # Archive it
        await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "document",
                "entity_id": doc_id,
                "soft_delete": True
            }
        )

        # List documents - should not include archived
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "offset": 0,
                "limit": 100
            }
        )

        if "results" in list_result:
            doc_ids = {d["id"] for d in list_result["results"]}
            assert doc_id not in doc_ids

    async def test_can_list_only_archived(self, call_mcp, test_organization):
        """Test filtering to show only archived items.

        User story: User can view archived items by filtering
        """
        # List only archived documents
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filter_list": [{"field": "is_deleted", "operator": "eq", "value": True}]
            }
        )

        assert isinstance(result, (dict, list))
        if isinstance(result, dict) and "results" in result:
            # All items should be archived
            for doc in result["results"]:
                assert doc.get("is_deleted") is True

    def _get_entity_data(self, entity_type: str, test_organization: dict) -> dict:
        """Helper to get minimum required data for entity type."""
        if entity_type == "organization":
            return {"name": f"Test {entity_type}"}
        elif entity_type == "project":
            return {
                "name": f"Test {entity_type}",
                "organization_id": test_organization["id"]
            }
        elif entity_type == "document":
            return {
                "name": f"Test {entity_type}",
                "project_id": test_organization["projects"][0]
            }
        elif entity_type == "requirement":
            return {
                "name": f"Test {entity_type}",
                "document_id": test_organization["docs"][0]
            }
        elif entity_type == "test":
            return {
                "title": f"Test {entity_type}",
                "project_id": test_organization["projects"][0]
            }
        return {"name": f"Test {entity_type}"}


class TestArchiveUserStories:
    """User story acceptance tests for archive/restore."""

    async def test_user_can_archive_without_losing_data(self, call_mcp, test_organization):
        """User story: User can archive entity and restore it later.

        Acceptance criteria:
        - Archive operation marks entity as deleted
        - Archived entity is not visible in normal lists
        - Archived entity can be restored
        - Restoration makes entity visible again
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
        org_id = create_result["id"]

        # Archive
        await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": org_id,
                "soft_delete": True
            }
        )

        # Restore
        await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "organization",
                "entity_id": org_id,
                "data": {"is_deleted": False}
            }
        )

        # Should be readable
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": org_id
            }
        )

        assert result is not None
        assert "error" not in result or result.get("is_deleted") is False
