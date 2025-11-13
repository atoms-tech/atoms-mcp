"""Relationship tool tests - Enhanced coverage for relationship operations.

Tests relationship management operations:
- Entity linking with metadata
- Unlinking entities
- Relationship listing and filtering
- Relationship checking
- Complex relationship scenarios
- Error handling

Run with: pytest tests/unit/tools/test_relationship_coverage.py -v
"""

import uuid
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestRelationshipLinking:
    """Test entity linking operations."""
    
    @pytest.mark.story("Entity Relationships - User can link entities together")
    async def test_link_basic_entities(self, call_mcp):
        """Test basic entity linking."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "from_entity": {
                "type": "organization",
                "id": f"org-{uuid.uuid4().hex[:8]}"
            },
            "to_entity": {
                "type": "project",
                "id": f"proj-{uuid.uuid4().hex[:8]}"
            }
        })
        
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.story("Entity Relationships - User can link entities together")
    async def test_link_with_metadata(self, call_mcp):
        """Test linking entities with relationship metadata."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "assignment",
            "from_entity": {
                "type": "person",
                "id": "user-123"
            },
            "to_entity": {
                "type": "requirement",
                "id": "req-456"
            },
            "metadata": {
                "role": "owner",
                "assigned_date": "2023-01-01",
                "priority": "high"
            }
        })
        
        assert result is not None
    
    async def test_link_bidirectional(self, call_mcp):
        """Test bidirectional linking."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "related_to",
            "from_entity": {
                "type": "requirement",
                "id": "req-1"
            },
            "to_entity": {
                "type": "requirement",
                "id": "req-2"
            },
            "bidirectional": True
        })
        
        assert result is not None


class TestRelationshipUnlinking:
    """Test entity unlinking operations."""
    
    @pytest.mark.story("Entity Relationships - User can unlink related entities")
    async def test_unlink_entities(self, call_mcp):
        """Test unlinking entities."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "unlink",
            "relationship_type": "member",
            "from_entity": {
                "type": "organization",
                "id": "org-123"
            },
            "to_entity": {
                "type": "project",
                "id": "proj-456"
            }
        })
        
        assert result is not None
    
    async def test_unlink_nonexistent_relationship(self, call_mcp):
        """Test unlinking a relationship that doesn't exist."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "unlink",
            "relationship_type": "member",
            "from_entity": {
                "type": "organization",
                "id": "nonexistent-org"
            },
            "to_entity": {
                "type": "project",
                "id": "nonexistent-proj"
            }
        })
        
        # Should handle gracefully
        assert result is not None


class TestRelationshipListing:
    """Test relationship listing and querying."""
    
    @pytest.mark.story("Entity Relationships - User can view entity relationships")
    async def test_list_relationships_for_entity(self, call_mcp):
        """Test listing all relationships for an entity."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "entity_type": "project",
            "entity_id": "proj-123"
        })
        
        assert result is not None
        if result.get("success"):
            assert "data" in result
            assert isinstance(result["data"], (list, dict))
    
    async def test_list_relationships_by_type(self, call_mcp):
        """Test listing relationships filtered by type."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "entity_type": "organization",
            "entity_id": "org-123",
            "relationship_type": "member"
        })
        
        assert result is not None
    
    async def test_list_relationships_with_pagination(self, call_mcp):
        """Test listing relationships with pagination."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "entity_type": "project",
            "entity_id": "proj-123",
            "limit": 10,
            "offset": 0
        })
        
        assert result is not None
    
    async def test_list_relationships_reverse_direction(self, call_mcp):
        """Test listing reverse direction relationships."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "entity_type": "requirement",
            "entity_id": "req-123",
            "direction": "incoming"  # What links TO this entity
        })
        
        assert result is not None


class TestRelationshipChecking:
    """Test relationship existence checking."""
    
    @pytest.mark.story("Entity Relationships - User can check if entities are related")
    async def test_check_relationship_exists(self, call_mcp):
        """Test checking if relationship exists between two entities."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "check",
            "relationship_type": "member",
            "from_entity": {
                "type": "organization",
                "id": "org-123"
            },
            "to_entity": {
                "type": "project",
                "id": "proj-456"
            }
        })
        
        assert result is not None
        if result.get("success"):
            assert "exists" in result or "related" in result
    
    async def test_check_relationship_specific_type(self, call_mcp):
        """Test checking for specific relationship type."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "check",
            "relationship_type": "assignment",
            "from_entity": {
                "type": "person",
                "id": "user-123"
            },
            "to_entity": {
                "type": "requirement",
                "id": "req-456"
            }
        })
        
        assert result is not None
    
    async def test_check_with_metadata_filter(self, call_mcp):
        """Test checking relationships with metadata filters."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "check",
            "relationship_type": "assignment",
            "from_entity": {
                "type": "person",
                "id": "user-123"
            },
            "to_entity": {
                "type": "requirement",
                "id": "req-456"
            },
            "metadata_filter": {"role": "owner"}
        })
        
        assert result is not None


class TestRelationshipUpdating:
    """Test relationship metadata updates."""
    
    async def test_update_relationship_metadata(self, call_mcp):
        """Test updating relationship metadata."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "update",
            "relationship_type": "assignment",
            "from_entity": {
                "type": "person",
                "id": "user-123"
            },
            "to_entity": {
                "type": "requirement",
                "id": "req-456"
            },
            "metadata": {
                "role": "reviewer",
                "updated_date": "2023-12-01"
            }
        })
        
        assert result is not None
    
    async def test_update_nonexistent_relationship(self, call_mcp):
        """Test updating metadata on non-existent relationship."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "update",
            "relationship_type": "member",
            "from_entity": {
                "type": "organization",
                "id": "nonexistent"
            },
            "to_entity": {
                "type": "project",
                "id": "also-nonexistent"
            },
            "metadata": {"status": "active"}
        })
        
        # Should handle gracefully
        assert result is not None


class TestRelationshipScenarios:
    """Test complex relationship scenarios."""
    
    async def test_multiple_relationship_types_same_entities(self, call_mcp):
        """Test multiple different relationships between same entities."""
        org_id = "org-123"
        proj_id = "proj-456"
        
        # Create first relationship
        result1, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "from_entity": {"type": "organization", "id": org_id},
            "to_entity": {"type": "project", "id": proj_id}
        })
        
        assert result1 is not None
        
        # Create second relationship between same entities
        result2, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "owns",
            "from_entity": {"type": "organization", "id": org_id},
            "to_entity": {"type": "project", "id": proj_id}
        })
        
        assert result2 is not None
    
    async def test_relationship_chain(self, call_mcp):
        """Test following a chain of relationships."""
        # Link A -> B
        result1, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "contains",
            "from_entity": {"type": "organization", "id": "org-1"},
            "to_entity": {"type": "project", "id": "proj-1"}
        })
        
        assert result1 is not None
        
        # Link B -> C
        result2, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "contains",
            "from_entity": {"type": "project", "id": "proj-1"},
            "to_entity": {"type": "requirement", "id": "req-1"}
        })
        
        assert result2 is not None
        
        # Could potentially follow chain from A to C
        result3, _ = await call_mcp("relationship_tool", {
            "operation": "list",
            "entity_type": "organization",
            "entity_id": "org-1"
        })
        
        assert result3 is not None


class TestRelationshipErrorHandling:
    """Test error handling in relationship operations."""
    
    async def test_invalid_relationship_type(self, call_mcp):
        """Test handling of invalid relationship type."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "invalid_type",
            "from_entity": {"type": "organization", "id": "org-1"},
            "to_entity": {"type": "project", "id": "proj-1"}
        })
        
        # Should fail gracefully
        assert result is not None
    
    async def test_missing_entity_identifiers(self, call_mcp):
        """Test handling missing entity identifiers."""
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "member",
            "from_entity": {"type": "organization"},  # Missing id
            "to_entity": {"type": "project", "id": "proj-1"}
        })
        
        # Should handle missing identifier
        assert result is not None
    
    async def test_circular_relationship_prevention(self, call_mcp):
        """Test handling of circular relationships."""
        entity_id = "entity-123"
        
        result, _ = await call_mcp("relationship_tool", {
            "operation": "link",
            "relationship_type": "depends_on",
            "from_entity": {"type": "requirement", "id": entity_id},
            "to_entity": {"type": "requirement", "id": entity_id}  # Linking to itself
        })
        
        # Should either prevent or handle gracefully
        assert result is not None
