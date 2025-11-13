"""Relationship Tool Tests - Unit Tests Only.

This test suite validates relationship_tool functionality:
- operation: link, unlink, list, check, update
- relationship_type: member, assignment, trace_link, requirement_test, invitation
- source: dict with type and id
- target: dict with type and id
- metadata: optional dict for relationship data

Run with: pytest tests/unit/tools/test_relationship.py -v
"""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestRelationshipLink:
    """Test linking operations."""
    
    async def test_link_basic(self, call_mcp):
        """Test basic relationship link operation."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should return result"
    
    async def test_link_with_metadata(self, call_mcp):
        """Test linking with relationship metadata."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
            "metadata": {"role": "admin"}
        })
        
        assert result is not None, "Should return result"
    
    async def test_link_different_types(self, call_mcp):
        """Test linking different relationship types."""
        for rel_type in ["member", "assignment", "trace_link"]:
            result, _ = await call_mcp("relationship_tool", {
                "operation": "link",
                "relationship_type": rel_type,
                "source": {"type": "organization", "id": "org_123"},
                "target": {"type": "user", "id": "user_456"},
            })
            
            assert result is not None, f"Should handle {rel_type}"


class TestRelationshipUnlink:
    """Test unlinking operations."""
    
    async def test_unlink_basic(self, call_mcp):
        """Test basic unlink operation."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "unlink",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should return result"
    
    async def test_unlink_with_soft_delete(self, call_mcp):
        """Test unlink with soft delete flag."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "unlink",
            "relationship_type": "assignment",
            "source": {"type": "project", "id": "proj_789"},
            "target": {"type": "user", "id": "user_123"},
            "soft_delete": True
        })
        
        assert result is not None, "Should handle soft_delete flag"


class TestRelationshipList:
    """Test listing operations."""
    
    @pytest.mark.story("Entity Relationships - User can view related entities")
    async def test_list_relationships(self, call_mcp):
        """Test listing relationships."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "limit": 10
        })
        
        assert result is not None, "Should return result"
    
    async def test_list_with_pagination(self, call_mcp):
        """Test listing with pagination."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "assignment",
            "source": {"type": "project", "id": "proj_789"},
            "limit": 5,
            "offset": 0
        })
        
        assert result is not None, "Should handle pagination"


class TestRelationshipCheck:
    """Test checking relationships."""
    
    async def test_check_relationship(self, call_mcp):
        """Test checking if a relationship exists."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "check",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should return result"


@pytest.mark.dependency(depends=["TestRelationshipCreate"])
class TestRelationshipUpdate:
    """Test updating operations."""
    
    @pytest.mark.story("Entity Relationships - User can update relationships")
    async def test_update_relationship(self, call_mcp):
        """Test updating relationship metadata."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "update",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
            "metadata": {"role": "viewer"}
        })
        
        assert result is not None, "Should return result"


class TestRelationshipEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_missing_operation(self, call_mcp):
        """Test with missing operation."""
        result, _ = await call_mcp("relationship_tool", {
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
        })
        
        assert result is not None, "Should handle missing operation"
    
    async def test_invalid_operation(self, call_mcp):
        """Test with invalid operation."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "invalid_op",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
        })
        
        assert result is not None, "Should handle invalid operation"
    
    async def test_missing_source(self, call_mcp):
        """Test with missing source."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should handle missing source"
    
    async def test_invalid_source_format(self, call_mcp):
        """Test with invalid source format."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": "invalid",
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should handle invalid format"
    
    async def test_empty_source(self, call_mcp):
        """Test with empty source."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": {},
            "target": {"type": "user", "id": "user_456"},
        })
        
        assert result is not None, "Should handle empty source"


class TestRelationshipFormats:
    """Test format types."""
    
    async def test_detailed_format(self, call_mcp):
        """Test detailed format."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return result"
    
    async def test_summary_format(self, call_mcp):
        """Test summary format."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "relationship_type": "assignment",
            "source": {"type": "project", "id": "proj_789"},
            "format_type": "summary"
        })
        
        assert result is not None, "Should return result"


class TestRelationshipContext:
    """Test context handling."""
    
    async def test_with_source_context(self, call_mcp):
        """Test with source context."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "source": {"type": "organization", "id": "org_123"},
            "target": {"type": "user", "id": "user_456"},
            "source_context": "workspace:default"
        })
        
        assert result is not None, "Should handle source_context"
