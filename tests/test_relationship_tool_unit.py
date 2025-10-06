"""Unit tests for relationship_tool.

These tests mock the database layer to test the relationship logic without
requiring a running server or database connection.

Run with: pytest tests/test_relationship_tool_unit.py -v -s
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.relationship import RelationshipManager, relationship_operation


class TestRelationshipConfiguration:
    """Test relationship configuration retrieval."""

    def test_get_member_config(self):
        """Test getting member relationship configuration."""
        manager = RelationshipManager()

        config = manager._get_relationship_config("member")

        assert "organization" in config
        assert "project" in config
        assert config["organization"]["table"] == "organization_members"
        assert config["organization"]["source_field"] == "organization_id"
        assert config["organization"]["target_field"] == "user_id"
        assert "role" in config["organization"]["metadata_fields"]
        assert "status" in config["organization"]["metadata_fields"]

    def test_get_assignment_config(self):
        """Test getting assignment relationship configuration."""
        manager = RelationshipManager()

        config = manager._get_relationship_config("assignment")

        assert config["table"] == "assignments"
        assert config["source_field"] == "entity_id"
        assert config["target_field"] == "assignee_id"
        assert "entity_type" in config["metadata_fields"]
        assert "role" in config["metadata_fields"]

    def test_get_trace_link_config(self):
        """Test getting trace_link relationship configuration."""
        manager = RelationshipManager()

        config = manager._get_relationship_config("trace_link")

        assert config["table"] == "trace_links"
        assert config["source_field"] == "source_id"
        assert config["target_field"] == "target_id"
        assert "source_type" in config["metadata_fields"]
        assert "target_type" in config["metadata_fields"]
        assert "link_type" in config["metadata_fields"]
        assert config["defaults"]["version"] == 1

    def test_get_requirement_test_config(self):
        """Test getting requirement_test relationship configuration."""
        manager = RelationshipManager()

        config = manager._get_relationship_config("requirement_test")

        assert config["table"] == "requirement_tests"
        assert config["source_field"] == "requirement_id"
        assert config["target_field"] == "test_id"
        assert "relationship_type" in config["metadata_fields"]
        assert config["defaults"]["relationship_type"] == "tests"

    def test_get_invitation_config(self):
        """Test getting invitation relationship configuration."""
        manager = RelationshipManager()

        config = manager._get_relationship_config("invitation")

        assert config["table"] == "organization_invitations"
        assert config["source_field"] == "organization_id"
        assert config["target_field"] == "email"
        assert "role" in config["metadata_fields"]
        assert config["defaults"]["status"] == "pending"

    def test_unknown_relationship_type(self):
        """Test handling of unknown relationship type."""
        manager = RelationshipManager()

        config = manager._get_relationship_config("unknown_type")

        assert config == {}


class TestLinkEntities:
    """Test link_entities method."""

    @pytest.mark.asyncio
    async def test_link_organization_member(self):
        """Test linking a user to an organization."""
        manager = RelationshipManager()
        manager._db_insert = AsyncMock(return_value={
            "id": "mem_123",
            "organization_id": "org_123",
            "user_id": "user_456",
            "role": "admin",
            "status": "active"
        })

        result = await manager.link_entities(
            relationship_type="member",
            source={"type": "organization", "id": "org_123"},
            target={"type": "user", "id": "user_456"},
            metadata={"role": "admin"}
        )

        assert result["organization_id"] == "org_123"
        assert result["user_id"] == "user_456"
        assert result["role"] == "admin"
        assert result["status"] == "active"  # default

        # Verify db_insert was called with correct table and data
        manager._db_insert.assert_called_once()
        call_args = manager._db_insert.call_args
        assert call_args[0][0] == "organization_members"
        assert call_args[0][1]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_link_project_member_with_context(self):
        """Test linking a user to a project with organization context."""
        manager = RelationshipManager()
        manager._db_insert = AsyncMock(return_value={
            "id": "mem_456",
            "project_id": "proj_123",
            "user_id": "user_456",
            "role": "developer",
            "org_id": "org_789",
            "status": "active"
        })

        result = await manager.link_entities(
            relationship_type="member",
            source={"type": "project", "id": "proj_123"},
            target={"type": "user", "id": "user_456"},
            metadata={"role": "developer"},
            source_context="org_789"
        )

        assert result["project_id"] == "proj_123"
        assert result["user_id"] == "user_456"
        assert result["role"] == "developer"
        assert result["org_id"] == "org_789"

        # Verify org_id was set from source_context
        call_args = manager._db_insert.call_args
        assert call_args[0][1]["org_id"] == "org_789"

    @pytest.mark.asyncio
    async def test_link_assignment(self):
        """Test creating an assignment relationship."""
        manager = RelationshipManager()
        manager._user_context = {"user_id": "creator_123"}
        manager._db_insert = AsyncMock(return_value={
            "id": "assign_123",
            "entity_id": "req_456",
            "assignee_id": "user_789",
            "entity_type": "requirement",
            "role": "owner",
            "status": "active",
            "created_by": "creator_123"
        })

        result = await manager.link_entities(
            relationship_type="assignment",
            source={"type": "requirement", "id": "req_456"},
            target={"type": "user", "id": "user_789"},
            metadata={"role": "owner"}
        )

        assert result["entity_id"] == "req_456"
        assert result["assignee_id"] == "user_789"
        assert result["entity_type"] == "requirement"
        assert result["role"] == "owner"
        assert result["created_by"] == "creator_123"

    @pytest.mark.asyncio
    async def test_link_trace_link(self):
        """Test creating a trace link."""
        manager = RelationshipManager()
        manager._user_context = {"user_id": "creator_123"}
        manager._db_insert = AsyncMock(return_value={
            "id": "trace_123",
            "source_id": "req_1",
            "target_id": "req_2",
            "source_type": "requirement",
            "target_type": "requirement",
            "link_type": "depends_on",
            "version": 1,
            "is_deleted": False,
            "created_by": "creator_123"
        })

        result = await manager.link_entities(
            relationship_type="trace_link",
            source={"type": "requirement", "id": "req_1"},
            target={"type": "requirement", "id": "req_2"},
            metadata={"link_type": "depends_on"}
        )

        assert result["source_id"] == "req_1"
        assert result["target_id"] == "req_2"
        assert result["source_type"] == "requirement"
        assert result["target_type"] == "requirement"
        assert result["link_type"] == "depends_on"
        assert result["version"] == 1
        assert result["is_deleted"] is False

    @pytest.mark.asyncio
    async def test_link_requirement_test(self):
        """Test linking a requirement to a test."""
        manager = RelationshipManager()
        manager._user_context = {"user_id": "creator_123"}
        manager._db_insert = AsyncMock(return_value={
            "id": "reqtest_123",
            "requirement_id": "req_456",
            "test_id": "test_789",
            "relationship_type": "tests",
            "coverage_level": "full",
            "created_by": "creator_123"
        })

        result = await manager.link_entities(
            relationship_type="requirement_test",
            source={"type": "requirement", "id": "req_456"},
            target={"type": "test", "id": "test_789"},
            metadata={"coverage_level": "full"}
        )

        assert result["requirement_id"] == "req_456"
        assert result["test_id"] == "test_789"
        assert result["relationship_type"] == "tests"
        assert result["coverage_level"] == "full"

    @pytest.mark.asyncio
    async def test_link_invitation(self):
        """Test creating an invitation."""
        manager = RelationshipManager()
        manager._user_context = {"user_id": "creator_123"}
        manager._db_insert = AsyncMock(return_value={
            "id": "inv_123",
            "organization_id": "org_456",
            "email": "new@example.com",
            "role": "member",
            "status": "pending",
            "created_by": "creator_123"
        })

        result = await manager.link_entities(
            relationship_type="invitation",
            source={"type": "organization", "id": "org_456"},
            target={"type": "email", "id": "new@example.com"},
            metadata={"role": "member"}
        )

        assert result["organization_id"] == "org_456"
        assert result["email"] == "new@example.com"
        assert result["role"] == "member"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_link_unknown_type_raises_error(self):
        """Test that unknown relationship type raises ValueError."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Unknown relationship type"):
            await manager.link_entities(
                relationship_type="unknown_type",
                source={"type": "test", "id": "123"},
                target={"type": "test", "id": "456"}
            )

    @pytest.mark.asyncio
    async def test_link_member_invalid_source_type(self):
        """Test that member relationship with invalid source type raises error."""
        manager = RelationshipManager()

        with pytest.raises(ValueError, match="Invalid source type for member relationship"):
            await manager.link_entities(
                relationship_type="member",
                source={"type": "invalid", "id": "123"},
                target={"type": "user", "id": "456"}
            )


class TestUnlinkEntities:
    """Test unlink_entities method."""

    @pytest.mark.asyncio
    async def test_unlink_soft_delete(self):
        """Test soft deleting a relationship."""
        manager = RelationshipManager()
        manager._user_context = {"user_id": "user_123"}
        manager._db_update = AsyncMock(return_value={
            "id": "trace_123",
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc).isoformat()
        })

        result = await manager.unlink_entities(
            relationship_type="trace_link",
            source={"type": "requirement", "id": "req_1"},
            target={"type": "requirement", "id": "req_2"},
            soft_delete=True
        )

        assert result is True

        # Verify update was called with is_deleted
        call_args = manager._db_update.call_args
        assert call_args[0][1]["is_deleted"] is True
        assert "deleted_at" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_unlink_hard_delete(self):
        """Test hard deleting a relationship."""
        manager = RelationshipManager()
        manager._db_delete = AsyncMock(return_value=1)

        result = await manager.unlink_entities(
            relationship_type="assignment",
            source={"type": "requirement", "id": "req_1"},
            target={"type": "user", "id": "user_1"},
            soft_delete=False
        )

        assert result is True
        manager._db_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlink_member_hard_delete(self):
        """Test that member relationships use hard delete (no is_deleted field)."""
        manager = RelationshipManager()
        manager._db_delete = AsyncMock(return_value=1)

        result = await manager.unlink_entities(
            relationship_type="member",
            source={"type": "organization", "id": "org_1"},
            target={"type": "user", "id": "user_1"},
            soft_delete=True  # Will use hard delete anyway
        )

        assert result is True
        # Should use hard delete since member doesn't have is_deleted
        manager._db_delete.assert_called_once()


class TestListRelationships:
    """Test list_relationships method."""

    @pytest.mark.asyncio
    async def test_list_organization_members(self):
        """Test listing organization members."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[
            {
                "id": "mem_1",
                "organization_id": "org_123",
                "user_id": "user_1",
                "role": "admin"
            },
            {
                "id": "mem_2",
                "organization_id": "org_123",
                "user_id": "user_2",
                "role": "member"
            }
        ])

        # Mock profile fetch
        with patch.object(manager, '_db_query', side_effect=[
            # First call for relationships
            [
                {"id": "mem_1", "organization_id": "org_123", "user_id": "user_1", "role": "admin"},
                {"id": "mem_2", "organization_id": "org_123", "user_id": "user_2", "role": "member"}
            ],
            # Second call for profiles
            [
                {"id": "user_1", "email": "user1@example.com"},
                {"id": "user_2", "email": "user2@example.com"}
            ]
        ]) as mock_query:
            result = await manager.list_relationships(
                relationship_type="member",
                source={"type": "organization", "id": "org_123"},
                limit=10
            )

        assert len(result) == 2
        assert result[0]["role"] == "admin"
        # Profiles should be joined
        assert "profiles" in result[0]

    @pytest.mark.asyncio
    async def test_list_with_filters(self):
        """Test listing with additional filters."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[
            {
                "id": "assign_1",
                "entity_id": "req_123",
                "assignee_id": "user_1",
                "status": "active"
            }
        ])

        result = await manager.list_relationships(
            relationship_type="assignment",
            source={"type": "requirement", "id": "req_123"},
            filters={"status": "active"},
            limit=10
        )

        assert len(result) == 1
        assert result[0]["status"] == "active"

        # Verify filters were passed
        call_args = manager._db_query.call_args
        assert call_args[1]["filters"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_excludes_deleted(self):
        """Test that deleted items are excluded by default."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[])

        await manager.list_relationships(
            relationship_type="trace_link",
            source={"type": "requirement", "id": "req_1"},
            limit=10
        )

        # Verify is_deleted filter was added
        call_args = manager._db_query.call_args
        assert call_args[1]["filters"]["is_deleted"] is False

    @pytest.mark.asyncio
    async def test_list_with_pagination(self):
        """Test listing with pagination."""
        manager = RelationshipManager()
        manager._db_query = AsyncMock(return_value=[])

        await manager.list_relationships(
            relationship_type="assignment",
            source={"type": "requirement", "id": "req_1"},
            limit=20,
            offset=10
        )

        call_args = manager._db_query.call_args
        assert call_args[1]["limit"] == 20
        assert call_args[1]["offset"] == 10


class TestCheckRelationship:
    """Test check_relationship method."""

    @pytest.mark.asyncio
    async def test_check_exists(self):
        """Test checking for existing relationship."""
        manager = RelationshipManager()
        manager.list_relationships = AsyncMock(return_value=[
            {"id": "mem_1", "organization_id": "org_1", "user_id": "user_1"}
        ])

        result = await manager.check_relationship(
            relationship_type="member",
            source={"type": "organization", "id": "org_1"},
            target={"type": "user", "id": "user_1"}
        )

        assert result is not None
        assert result["id"] == "mem_1"

    @pytest.mark.asyncio
    async def test_check_not_exists(self):
        """Test checking for non-existent relationship."""
        manager = RelationshipManager()
        manager.list_relationships = AsyncMock(return_value=[])

        result = await manager.check_relationship(
            relationship_type="member",
            source={"type": "organization", "id": "org_1"},
            target={"type": "user", "id": "user_1"}
        )

        assert result is None


class TestUpdateRelationship:
    """Test update_relationship method."""

    @pytest.mark.asyncio
    async def test_update_metadata(self):
        """Test updating relationship metadata."""
        manager = RelationshipManager()
        manager._user_context = {"user_id": "user_123"}
        manager._db_update = AsyncMock(return_value={
            "id": "mem_1",
            "organization_id": "org_1",
            "user_id": "user_1",
            "role": "admin",
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        result = await manager.update_relationship(
            relationship_type="member",
            source={"type": "organization", "id": "org_1"},
            target={"type": "user", "id": "user_1"},
            metadata={"role": "admin"}
        )

        assert result["role"] == "admin"

        # Verify update was called with correct data
        call_args = manager._db_update.call_args
        assert call_args[0][1]["role"] == "admin"
        assert "updated_at" in call_args[0][1]
        assert "updated_by" in call_args[0][1]


class TestRelationshipOperation:
    """Test the main relationship_operation function."""

    @pytest.mark.asyncio
    async def test_link_operation(self):
        """Test link operation."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth, \
             patch.object(RelationshipManager, 'link_entities', new_callable=AsyncMock) as mock_link:

            mock_auth.return_value = {"user_id": "user_123"}
            mock_link.return_value = {"id": "rel_123", "status": "active"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="link",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"},
                metadata={"role": "admin"}
            )

            assert result["success"] is True
            assert result["data"]["id"] == "rel_123"

    @pytest.mark.asyncio
    async def test_unlink_operation(self):
        """Test unlink operation."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth, \
             patch.object(RelationshipManager, 'unlink_entities', new_callable=AsyncMock) as mock_unlink:

            mock_auth.return_value = {"user_id": "user_123"}
            mock_unlink.return_value = True

            result = await relationship_operation(
                auth_token="test_token",
                operation="unlink",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"},
                soft_delete=True
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_operation(self):
        """Test list operation."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth, \
             patch.object(RelationshipManager, 'list_relationships', new_callable=AsyncMock) as mock_list:

            mock_auth.return_value = {"user_id": "user_123"}
            mock_list.return_value = [{"id": "rel_1"}, {"id": "rel_2"}]

            result = await relationship_operation(
                auth_token="test_token",
                operation="list",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                limit=10
            )

            assert result["success"] is True
            assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_check_operation(self):
        """Test check operation."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth, \
             patch.object(RelationshipManager, 'check_relationship', new_callable=AsyncMock) as mock_check:

            mock_auth.return_value = {"user_id": "user_123"}
            mock_check.return_value = {"id": "rel_1"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="check",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"}
            )

            assert result["exists"] is True
            assert result["relationship"]["id"] == "rel_1"

    @pytest.mark.asyncio
    async def test_update_operation(self):
        """Test update operation."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth, \
             patch.object(RelationshipManager, 'update_relationship', new_callable=AsyncMock) as mock_update:

            mock_auth.return_value = {"user_id": "user_123"}
            mock_update.return_value = {"id": "rel_1", "role": "admin"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="update",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"},
                metadata={"role": "admin"}
            )

            assert result["success"] is True
            assert result["data"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_missing_target_for_link(self):
        """Test that link operation requires target."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"user_id": "user_123"}

            result = await relationship_operation(
                auth_token="test_token",
                operation="link",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"}
                # Missing target
            )

            assert result["success"] is False
            assert "target is required" in result["error"]

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that errors are caught and returned."""
        with patch.object(RelationshipManager, '_validate_auth', new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Auth failed")

            result = await relationship_operation(
                auth_token="test_token",
                operation="link",
                relationship_type="member",
                source={"type": "organization", "id": "org_1"},
                target={"type": "user", "id": "user_1"}
            )

            assert result["success"] is False
            assert "Auth failed" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
