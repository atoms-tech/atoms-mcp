"""Additional tests to achieve 100% coverage for relationship_tool.

These tests cover edge cases and error paths not covered by the main unit tests.

Run with: pytest tests/test_relationship_tool_coverage.py -v
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.relationship import RelationshipManager, relationship_operation


class TestEdgeCases:
    """Test edge cases and error paths for 100% coverage."""

    @pytest.mark.asyncio
    async def test_unlink_member_source_type_error(self):
        """Test unlink with invalid member source type."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Invalid source type for member relationship"):
            await manager.unlink_entities(
                relationship_type="member",
                source={"type": "invalid", "id": "123"},
                target={"type": "user", "id": "456"},
                soft_delete=True
            )

    @pytest.mark.asyncio
    async def test_unlink_unknown_relationship_type(self):
        """Test unlink with unknown relationship type."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Unknown relationship type"):
            await manager.unlink_entities(
                relationship_type="unknown_type",
                source={"type": "test", "id": "123"},
                target={"type": "test", "id": "456"},
                soft_delete=True
            )

    @pytest.mark.asyncio
    async def test_list_member_no_source_type(self):
        """Test listing members without source type (defaults to organization)."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[])

        result = await manager.list_relationships(
            relationship_type="member",
            source={"id": "org_123"},  # No type specified
            limit=10
        )

        # Should default to organization_members table
        call_args = manager._db_query.call_args
        assert call_args[0][0] == "organization_members"

    @pytest.mark.asyncio
    async def test_list_member_no_source(self):
        """Test listing members with no source at all."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[])

        result = await manager.list_relationships(
            relationship_type="member",
            limit=10
        )

        # Should default to organization_members table
        call_args = manager._db_query.call_args
        assert call_args[0][0] == "organization_members"

    @pytest.mark.asyncio
    async def test_list_unknown_relationship_type(self):
        """Test list with unknown relationship type."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Unknown relationship type"):
            await manager.list_relationships(
                relationship_type="unknown_type",
                source={"type": "test", "id": "123"},
                limit=10
            )

    @pytest.mark.asyncio
    async def test_update_member_invalid_source_type(self):
        """Test update with invalid member source type."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Invalid source type for member relationship"):
            await manager.update_relationship(
                relationship_type="member",
                source={"type": "invalid", "id": "123"},
                target={"type": "user", "id": "456"},
                metadata={"role": "admin"}
            )

    @pytest.mark.asyncio
    async def test_update_unknown_relationship_type(self):
        """Test update with unknown relationship type."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Unknown relationship type"):
            await manager.update_relationship(
                relationship_type="unknown_type",
                source={"type": "test", "id": "123"},
                target={"type": "test", "id": "456"},
                metadata={}
            )

    @pytest.mark.asyncio
    async def test_relationship_operation_unknown_operation(self):
        """Test relationship_operation with unknown operation."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": "user_123"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="invalid_operation",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"}
            )

            assert result["success"] is False
            assert "Unknown operation" in result["error"]

    @pytest.mark.asyncio
    async def test_relationship_operation_missing_target_for_unlink(self):
        """Test unlink operation requires target."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": "user_123"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="unlink",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"}
                # Missing target
            )

            assert result["success"] is False
            assert "target is required" in result["error"]

    @pytest.mark.asyncio
    async def test_relationship_operation_missing_target_for_check(self):
        """Test check operation requires target."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": "user_123"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="check",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"}
                # Missing target
            )

            assert result["success"] is False
            assert "target is required" in result["error"]

    @pytest.mark.asyncio
    async def test_relationship_operation_missing_metadata_for_update(self):
        """Test update operation requires metadata."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": "user_123"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="update",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"}
                # Missing metadata
            )

            assert result["success"] is False
            assert "metadata are required" in result["error"]

    @pytest.mark.asyncio
    async def test_check_relationship_not_found(self):
        """Test check_relationship when relationship doesn't exist."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth, \
             patch.object(RelationshipManager, 'check_relationship', new_callable=AsyncMock) as mock_check:

            mock_auth.return_value = {"user_id": "user_123"}
            mock_check.return_value = None

            result = await relationship_operation(
                auth_token="test_token",
                operation="check",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"}
            )

            assert result["exists"] is False
            assert result["relationship"] is None

    @pytest.mark.asyncio
    async def test_link_entities_without_user_context(self):
        """Test link without user context (no created_by)."""
        manager = RelationshipManager()
        manager._user_context = {}  # No user context
        manager._db_insert = AsyncMock(return_value={
            "id": "assign_123",
            "entity_id": "req_456",
            "assignee_id": "user_789",
            "entity_type": "requirement"
        })

        result = await manager.link_entities(
            relationship_type="assignment",
            source={"type": "requirement", "id": "req_456"},
            target={"type": "user", "id": "user_789"}
        )

        # Should succeed without created_by
        assert result["entity_id"] == "req_456"

        # Verify created_by was not added
        call_args = manager._db_insert.call_args
        assert "created_by" not in call_args[0][1]

    @pytest.mark.asyncio
    async def test_unlink_soft_delete_without_user_context(self):
        """Test soft delete without user context (no deleted_by)."""
        manager = RelationshipManager()
        manager._user_context = {}  # No user context
        manager._db_update = AsyncMock(return_value={
            "id": "trace_123",
            "is_deleted": True
        })

        result = await manager.unlink_entities(
            relationship_type="trace_link",
            source={"type": "requirement", "id": "req_1"},
            target={"type": "requirement", "id": "req_2"},
            soft_delete=True
        )

        assert result is True

        # Verify deleted_by was not added
        call_args = manager._db_update.call_args
        assert "deleted_by" not in call_args[0][1]

    @pytest.mark.asyncio
    async def test_update_without_user_context(self):
        """Test update without user context (no updated_by)."""
        manager = RelationshipManager()
        manager._user_context = {}  # No user context
        manager._db_update = AsyncMock(return_value={
            "id": "mem_1",
            "role": "admin"
        })

        result = await manager.update_relationship(
            relationship_type="member",
            source={"type": "organization", "id": "org_1"},
            target={"type": "user", "id": "user_1"},
            metadata={"role": "admin"}
        )

        # Should succeed without updated_by
        assert result["role"] == "admin"

        # Verify updated_by was not added
        call_args = manager._db_update.call_args
        assert "updated_by" not in call_args[0][1]

    @pytest.mark.asyncio
    async def test_unlink_returns_false_when_nothing_deleted(self):
        """Test unlink returns False when no records are deleted."""
        manager = RelationshipManager()
        manager._db_delete = AsyncMock(return_value=0)

        result = await manager.unlink_entities(
            relationship_type="assignment",
            source={"type": "requirement", "id": "req_1"},
            target={"type": "user", "id": "user_1"},
            soft_delete=False
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_unlink_soft_delete_returns_false_when_nothing_updated(self):
        """Test soft delete returns False when no records are updated."""
        manager = RelationshipManager()
        manager._db_update = AsyncMock(return_value=None)

        result = await manager.unlink_entities(
            relationship_type="trace_link",
            source={"type": "requirement", "id": "req_1"},
            target={"type": "requirement", "id": "req_2"},
            soft_delete=True
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_list_members_empty_user_ids(self):
        """Test listing members when no user_ids are present."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[
            {"id": "mem_1", "organization_id": "org_123", "user_id": None},
        ])

        result = await manager.list_relationships(
            relationship_type="member",
            source={"type": "organization", "id": "org_123"},
            limit=10
        )

        # Should handle None user_ids gracefully
        assert len(result) == 1
        assert "profiles" not in result[0]

    @pytest.mark.asyncio
    async def test_link_member_metadata_filtering(self):
        """Test that only valid metadata fields are included."""
        manager = RelationshipManager()
        manager._db_insert = AsyncMock(return_value={
            "id": "mem_123",
            "organization_id": "org_123",
            "user_id": "user_456",
            "role": "admin"
        })

        result = await manager.link_entities(
            relationship_type="member",
            source={"type": "organization", "id": "org_123"},
            target={"type": "user", "id": "user_456"},
            metadata={
                "role": "admin",
                "invalid_field": "should_be_ignored"
            }
        )

        # Verify only valid metadata fields were passed
        call_args = manager._db_insert.call_args
        assert "role" in call_args[0][1]
        assert "invalid_field" not in call_args[0][1]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
