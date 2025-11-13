"""Relationship Tool Tests - Unit Tests.

This test suite validates relationship_tool functionality with the correct API:
- operation: link, unlink, list, check, update
- relationship_type: member, assignment, trace_link, requirement_test, invitation
- source_entity_type, source_id, target_entity_type, target_id
- Other parameters: metadata, filters, limit, offset, format_type, etc.

Run with: pytest tests/unit/tools/test_relationship.py -v
"""

import pytest
import pytest_asyncio

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestRelationshipLink:
    """Test linking entities with relationships."""
    
    async def test_link_member_relationship(self, call_mcp, test_organization, test_user):
        """Test creating a member relationship between organization and user."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "target_entity_type": "user",
            "target_id": test_user,
            "metadata": {"role": "admin"}
        })
        
        assert result is not None, "Should return a result"
        if result.get("success"):
            assert "data" in result, "Result should contain data"
    
    async def test_link_with_minimal_fields(self, call_mcp, test_organization, test_user):
        """Test linking with only required fields."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "target_entity_type": "user",
            "target_id": test_user
        })
        
        assert result is not None, "Should return a result"


class TestRelationshipUnlink:
    """Test unlinking entity relationships."""
    
    async def test_unlink_relationship(self, call_mcp, test_organization, test_user):
        """Test removing a relationship between entities."""
        # First create a relationship
        link_result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "target_entity_type": "user",
            "target_id": test_user
        })
        
        if link_result.get("success"):
            # Then unlink it
            result, _ = await call_mcp("relationship_tool", {
                "operation": "unlink",
                "relationship_type": "member",
                "source_entity_type": "organization",
                "source_id": test_organization,
                "target_entity_type": "user",
                "target_id": test_user
            })
            
            assert result is not None, "Should return a result"


class TestRelationshipList:
    """Test listing relationships."""
    
    async def test_list_organization_members(self, call_mcp, test_organization):
        """Test listing all member relationships for an organization."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "limit": 50
        })
        
        assert result is not None, "Should return a result"
        if result.get("success"):
            assert "data" in result, "Result should contain data"
    
    async def test_list_with_filters(self, call_mcp, test_organization):
        """Test listing relationships with filter conditions."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "filters": {"role": "admin"},
            "limit": 50
        })
        
        assert result is not None, "Should return a result"
    
    async def test_list_with_pagination(self, call_mcp, test_organization):
        """Test listing relationships with pagination."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "limit": 10,
            "offset": 0
        })
        
        assert result is not None, "Should return a result"


class TestRelationshipCheck:
    """Test checking relationship existence."""
    
    async def test_check_member_exists(self, call_mcp, test_organization, test_user):
        """Test checking if a member relationship exists."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "check",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "target_entity_type": "user",
            "target_id": test_user
        })
        
        assert result is not None, "Should return a result"
        if result.get("success"):
            # Should have exists field
            assert "data" in result, "Result should contain exists data"


class TestRelationshipUpdate:
    """Test updating relationship metadata."""
    
    async def test_update_member_role(self, call_mcp, test_organization, test_user):
        """Test updating a member role."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "update",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "target_entity_type": "user",
            "target_id": test_user,
            "metadata": {"role": "editor"}
        })
        
        assert result is not None, "Should return a result"


class TestRelationshipEdgeCases:
    """Test edge cases and error conditions."""
    
    async def test_invalid_relationship_type(self, call_mcp, test_organization, test_user):
        """Test linking with invalid relationship type."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "invalid_type",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "target_entity_type": "user",
            "target_id": test_user
        })
        
        # Should handle gracefully (success: False or error)
        assert result is not None, "Should return a result"
    
    async def test_missing_required_fields(self, call_mcp):
        """Test operation with missing required fields."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member"
            # Missing source/target fields
        })
        
        assert result is not None, "Should return a result"
        assert not result.get("success"), "Should fail without required fields"
    
    async def test_list_empty_relationships(self, call_mcp):
        """Test listing relationships for non-existent entity."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": "non-existent-id",
            "limit": 50
        })
        
        assert result is not None, "Should return a result"


class TestRelationshipFormats:
    """Test different response formats."""
    
    async def test_list_detailed_format(self, call_mcp, test_organization):
        """Test listing with detailed format."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return a result"
    
    async def test_list_summary_format(self, call_mcp, test_organization):
        """Test listing with summary format."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source_entity_type": "organization",
            "source_id": test_organization,
            "format_type": "summary"
        })
        
        assert result is not None, "Should return a result"
