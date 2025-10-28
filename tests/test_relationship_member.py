"""
Member Relationship Tests

This module contains comprehensive tests for member relationship operations:
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


class TestMemberRelationship:
    """Test suite for member relationship operations."""

    @pytest.fixture
    def relationship_service(self):
        """Create a RelationshipService instance with mocked client."""
        service = RelationshipService()
        service.client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_member_link_basic(self, relationship_service):
        """Test basic member relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "member",
            "source_id": "user_123",
            "target_id": "org_456",
            "metadata": {}
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["id"] == "rel_789"
        relationship_service.client.create_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_member_link_with_metadata(self, relationship_service):
        """Test member relationship creation with metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
            metadata={"role": "admin", "joined_at": "2024-01-01"}
        )

        relationship_service.client.create_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "member",
            "source_id": "user_123",
            "target_id": "org_456",
            "metadata": {"role": "admin", "joined_at": "2024-01-01"}
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["metadata"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_member_unlink_basic(self, relationship_service):
        """Test basic member relationship removal."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        relationship_service.client.delete_relationship = AsyncMock(return_value={
            "success": True,
            "message": "Relationship removed"
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        relationship_service.client.delete_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_member_list_basic(self, relationship_service):
        """Test listing member relationships."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123"
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {
                    "id": "rel_789",
                    "relationship_type": "member",
                    "source_id": "user_123",
                    "target_id": "org_456",
                    "metadata": {"role": "admin"}
                }
            ],
            "total": 1
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 1
        assert result["relationships"][0]["target_id"] == "org_456"

    @pytest.mark.asyncio
    async def test_member_list_with_pagination(self, relationship_service):
        """Test listing member relationships with pagination."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            limit=10,
            offset=0
        )

        relationship_service.client.list_relationships = AsyncMock(return_value={
            "relationships": [
                {
                    "id": f"rel_{i}",
                    "relationship_type": "member",
                    "source_id": "user_123",
                    "target_id": f"org_{i}",
                    "metadata": {}
                } for i in range(10)
            ],
            "total": 25
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 10
        assert result["total"] == 25

    @pytest.mark.asyncio
    async def test_member_check_exists(self, relationship_service):
        """Test checking if member relationship exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        relationship_service.client.get_relationship = AsyncMock(return_value={
            "id": "rel_789",
            "relationship_type": "member",
            "source_id": "user_123",
            "target_id": "org_456",
            "metadata": {}
        })

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_member_check_not_exists(self, relationship_service):
        """Test checking if member relationship does not exist."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_999"
        )

        relationship_service.client.get_relationship = AsyncMock(return_value=None)

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_member_link_duplicate(self, relationship_service):
        """Test linking duplicate member relationship."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        relationship_service.client.create_relationship = AsyncMock(side_effect=Exception("Relationship already exists"))

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_member_unlink_not_exists(self, relationship_service):
        """Test unlinking non-existent member relationship."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_999"
        )

        relationship_service.client.delete_relationship = AsyncMock(side_effect=Exception("Relationship not found"))

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_member_list_empty(self, relationship_service):
        """Test listing member relationships when none exist."""
        request = RelationshipRequest(
            action="list",
            relationship_type=RelationshipType.MEMBER,
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
    async def test_member_invalid_action(self, relationship_service):
        """Test invalid action for member relationship."""
        request = RelationshipRequest(
            action="invalid",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456"
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "Invalid action" in result["error"]
