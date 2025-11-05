"""
Other Relationship Tests

This module contains comprehensive tests for other relationship types:
- DEPENDENCY relationships
- HIERARCHY relationships
- CUSTOM relationships
- Error conditions
- Special cases
"""

from unittest.mock import AsyncMock

import pytest
from atoms_mcp.lib.models import RelationshipRequest, RelationshipType
from atoms_mcp.lib.relationship import RelationshipService


class TestOtherRelationships:
    """Test suite for other relationship types."""

    @pytest.fixture
    def relationship_service(self):
        """Create a RelationshipService instance with mocked client."""
        service = RelationshipService()
        service.client = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_dependency_link_basic(self, relationship_service):
        """Test basic dependency relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.DEPENDENCY,
            source_type="requirement",
            source_id="req_123",
            target_type="requirement",
            target_id="req_456",
        )

        relationship_service.client.create_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "dependency",
                "source_id": "req_123",
                "target_id": "req_456",
                "metadata": {},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["id"] == "rel_789"
        relationship_service.client.create_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_dependency_link_with_metadata(self, relationship_service):
        """Test dependency relationship creation with metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.DEPENDENCY,
            source_type="requirement",
            source_id="req_123",
            target_type="requirement",
            target_id="req_456",
            metadata={"dependency_type": "blocking", "priority": "high"},
        )

        relationship_service.client.create_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "dependency",
                "source_id": "req_123",
                "target_id": "req_456",
                "metadata": {"dependency_type": "blocking", "priority": "high"},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["metadata"]["dependency_type"] == "blocking"

    @pytest.mark.asyncio
    async def test_hierarchy_link_basic(self, relationship_service):
        """Test basic hierarchy relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.HIERARCHY,
            source_type="project",
            source_id="project_123",
            target_type="project",
            target_id="project_456",
        )

        relationship_service.client.create_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "hierarchy",
                "source_id": "project_123",
                "target_id": "project_456",
                "metadata": {},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["id"] == "rel_789"
        relationship_service.client.create_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_hierarchy_link_with_metadata(self, relationship_service):
        """Test hierarchy relationship creation with metadata."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.HIERARCHY,
            source_type="project",
            source_id="project_123",
            target_type="project",
            target_id="project_456",
            metadata={"level": 1, "parent_child": "parent"},
        )

        relationship_service.client.create_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "hierarchy",
                "source_id": "project_123",
                "target_id": "project_456",
                "metadata": {"level": 1, "parent_child": "parent"},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["metadata"]["level"] == 1

    @pytest.mark.asyncio
    async def test_custom_relationship_link(self, relationship_service):
        """Test custom relationship creation."""
        request = RelationshipRequest(
            action="link",
            relationship_type="custom_relationship",
            source_type="document",
            source_id="doc_123",
            target_type="test",
            target_id="test_456",
        )

        relationship_service.client.create_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "custom_relationship",
                "source_id": "doc_123",
                "target_id": "test_456",
                "metadata": {},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["relationship"]["id"] == "rel_789"
        relationship_service.client.create_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_dependency_list_basic(self, relationship_service):
        """Test listing dependency relationships."""
        request = RelationshipRequest(
            action="list", relationship_type=RelationshipType.DEPENDENCY, source_type="requirement", source_id="req_123"
        )

        relationship_service.client.list_relationships = AsyncMock(
            return_value={
                "relationships": [
                    {
                        "id": "rel_789",
                        "relationship_type": "dependency",
                        "source_id": "req_123",
                        "target_id": "req_456",
                        "metadata": {"dependency_type": "blocking"},
                    }
                ],
                "total": 1,
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 1
        assert result["relationships"][0]["target_id"] == "req_456"

    @pytest.mark.asyncio
    async def test_hierarchy_list_basic(self, relationship_service):
        """Test listing hierarchy relationships."""
        request = RelationshipRequest(
            action="list", relationship_type=RelationshipType.HIERARCHY, source_type="project", source_id="project_123"
        )

        relationship_service.client.list_relationships = AsyncMock(
            return_value={
                "relationships": [
                    {
                        "id": "rel_789",
                        "relationship_type": "hierarchy",
                        "source_id": "project_123",
                        "target_id": "project_456",
                        "metadata": {"level": 1},
                    }
                ],
                "total": 1,
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert len(result["relationships"]) == 1
        assert result["relationships"][0]["target_id"] == "project_456"

    @pytest.mark.asyncio
    async def test_dependency_check_exists(self, relationship_service):
        """Test checking if dependency relationship exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.DEPENDENCY,
            source_type="requirement",
            source_id="req_123",
            target_type="requirement",
            target_id="req_456",
        )

        relationship_service.client.get_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "dependency",
                "source_id": "req_123",
                "target_id": "req_456",
                "metadata": {},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_hierarchy_check_exists(self, relationship_service):
        """Test checking if hierarchy relationship exists."""
        request = RelationshipRequest(
            action="check",
            relationship_type=RelationshipType.HIERARCHY,
            source_type="project",
            source_id="project_123",
            target_type="project",
            target_id="project_456",
        )

        relationship_service.client.get_relationship = AsyncMock(
            return_value={
                "id": "rel_789",
                "relationship_type": "hierarchy",
                "source_id": "project_123",
                "target_id": "project_456",
                "metadata": {},
            }
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_dependency_unlink_basic(self, relationship_service):
        """Test basic dependency relationship removal."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.DEPENDENCY,
            source_type="requirement",
            source_id="req_123",
            target_type="requirement",
            target_id="req_456",
        )

        relationship_service.client.delete_relationship = AsyncMock(
            return_value={"success": True, "message": "Relationship removed"}
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        relationship_service.client.delete_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_hierarchy_unlink_basic(self, relationship_service):
        """Test basic hierarchy relationship removal."""
        request = RelationshipRequest(
            action="unlink",
            relationship_type=RelationshipType.HIERARCHY,
            source_type="project",
            source_id="project_123",
            target_type="project",
            target_id="project_456",
        )

        relationship_service.client.delete_relationship = AsyncMock(
            return_value={"success": True, "message": "Relationship removed"}
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is True
        relationship_service.client.delete_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_relationship_type(self, relationship_service):
        """Test invalid relationship type."""
        request = RelationshipRequest(
            action="link",
            relationship_type="invalid_type",
            source_type="user",
            source_id="user_123",
            target_type="organization",
            target_id="org_456",
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "Invalid relationship type" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, relationship_service):
        """Test missing required fields."""
        request = RelationshipRequest(
            action="link",
            relationship_type=RelationshipType.MEMBER,
            source_type="user",
            source_id="user_123",
            # Missing target_type and target_id
        )

        result = await relationship_service.process_relationship(request)

        assert result["success"] is False
        assert "Missing required fields" in result["error"]
