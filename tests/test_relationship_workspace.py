"""
Workspace Relationship Tests

This module contains comprehensive tests for workspace relationship operations:
- Basic operations (link, unlink, list, check)
- Metadata handling
- Pagination
- Special cases
- Error conditions
"""

from unittest.mock import AsyncMock

import pytest
from atoms_mcp.lib.models import RelationshipRequest, RelationshipType
from atoms_mcp.lib.relationship import RelationshipService


class TestWorkspaceRelationship:
    """Test suite for workspace relationship operations."""

    @pytest.fixture
    def relationship_service(self):
        """Create a RelationshipService instance with mocked client."""
        service = RelationshipService()
        service.client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_workspace_link_basic(self, relationship_service):
        """Test basic workspace relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_456"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "workspace",
            "source_id": "user_123",
            "target_id": "project_456",
            "metadata": {}
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["id"] == "rel_789"
        relationship_service.client.create_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_workspace_link_with_metadata(self, relationship_service):
        """Test workspace relationship creation with metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_456",
            metadata={"permissions": ["read", "write"], "joined_at": "2024-01-01"}
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "workspace",
            "source_id": "user_123",
            "target_id": "project_456",
            "metadata": {"permissions": ["read", "write"], "joined_at": "2024-01-01"}
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["metadata"]["permissions"] == ["read", "write"]

    @pytest.mark.asyncio
    async def test_workspace_unlink_basic(self, relationship_service):
        """Test basic workspace relationship removal."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_456"
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "success": True,
            "message": "Relationship removed"
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        relationship_service.client.delete_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_workspace_list_basic(self, relationship_service):
        """Test listing workspace relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {
                    "id": "rel_789",
                    "relationship_type": "workspace",
                    "source_id": "user_123",
                    "target_id": "project_456",
                    "metadata": {"permissions": ["read", "write"]}
                }
            ],
            "total": 1
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 1
        assert result["relationships"][0]["target_id"] == "project_456"

    @pytest.mark.asyncio
    async def test_workspace_list_with_pagination(self, relationship_service):
        """Test listing workspace relationships with pagination."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            limit=5,
            offset=0
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {
                    "id": f"rel_{i}",
                    "relationship_type": "workspace",
                    "source_id": "user_123",
                    "target_id": f"project_{i}",
                    "metadata": {}
                } for i in range(5)
            ],
            "total": 15
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 5
        assert result["total"] == 15

    @pytest.mark.asyncio
    async def test_workspace_check_exists(self, relationship_service):
        """Test checking if workspace relationship exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_456"
        )

        relationship_service.client.get_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "workspace",
            "source_id": "user_123",
            "target_id": "project_456",
            "metadata": {}
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_workspace_check_not_exists(self, relationship_service):
        """Test checking if workspace relationship does not exist."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_999"
        )

        relationship_service.client.get_relationship = AsyncMock(return_value=None)

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_workspace_link_duplicate(self, relationship_service):
        """Test linking duplicate workspace relationship."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_456"
        )

        relationship_service.client.create_relationship = AsyncMock(side_effect=Exception("Relationship already exists"))

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_workspace_unlink_not_exists(self, relationship_service):
        """Test unlinking non-existent workspace relationship."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_999"
        )

        relationship_service.client.delete_relationship = AsyncMock(side_effect=Exception("Relationship not found"))

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_workspace_list_empty(self, relationship_service):
        """Test listing workspace relationships when none exist."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_999"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [],
            "total": 0
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_workspace_invalid_action(self, relationship_service):
        """Test invalid action for workspace relationship."""
        request = RelationshipRequest(
            action="invalid",
            relationship_type=RelationshipType.WORKSPACE,
            source_type="user",
            source_id="user_123",
            target_type="project",
            target_id="project_456"
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "Invalid action" in result["error"]
