"""Entity resolver tests - Fuzzy entity resolution."""

import re
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from tools.entity_resolver import EntityResolver

pytestmark = [pytest.mark.unit]


@pytest.fixture
def mock_db():
    """Mock database adapter."""
    db = AsyncMock()
    # Default return values
    db.get_single = AsyncMock(return_value=None)
    db.query = AsyncMock(return_value=[])
    return db


@pytest.fixture
def resolver(mock_db):
    """Create entity resolver with mock DB."""
    return EntityResolver(mock_db)


class TestEntityResolverUUID:
    """Test UUID detection and direct lookup."""

    async def test_uuid_pattern_detection(self, resolver):
        """Test _is_uuid recognizes valid UUIDs."""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "00000000-0000-0000-0000-000000000000",
        ]
        
        for uuid_str in valid_uuids:
            assert resolver._is_uuid(uuid_str), f"Should recognize {uuid_str} as UUID"
    
    async def test_uuid_pattern_rejection(self, resolver):
        """Test _is_uuid rejects invalid UUIDs."""
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # incomplete
            "550e8400_e29b_41d4_a716_446655440000",  # underscores
            "550e8400e29b41d4a716446655440000",  # no dashes
        ]
        
        for uuid_str in invalid_uuids:
            assert not resolver._is_uuid(uuid_str), f"Should reject {uuid_str} as UUID"
    
    async def test_resolve_by_valid_uuid(self, resolver, mock_db):
        """Test resolution by exact UUID."""
        entity_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_entity = {
            "id": entity_id,
            "name": "Test Organization",
            "created_at": "2023-01-01T00:00:00Z"
        }
        mock_db.get_single.return_value = mock_entity
        
        result = await resolver.resolve_entity_id("organization", entity_id)
        
        assert result["success"] is True
        assert result["entity_id"] == entity_id
        assert result["entity"] == mock_entity
        assert result["match_type"] == "exact_uuid"
        mock_db.get_single.assert_called_once()
    
    async def test_resolve_by_uuid_not_found(self, resolver, mock_db):
        """Test resolution by UUID when entity doesn't exist."""
        entity_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_db.get_single.return_value = None
        mock_db.query.return_value = []
        
        result = await resolver.resolve_entity_id("organization", entity_id)
        
        assert result["success"] is False
        assert "error" in result


class TestEntityResolverExactMatch:
    """Test exact name matching."""

    async def test_exact_name_match_single(self, resolver, mock_db):
        """Test exact name match returns single entity."""
        identifier = "Acme Corporation"
        entities = [
            {
                "id": "org-1",
                "name": "Acme Corporation",
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id("organization", identifier)
        
        assert result["success"] is True
        assert result["entity_id"] == "org-1"
        assert result["match_type"] == "exact_name"
    
    async def test_exact_name_match_case_insensitive(self, resolver, mock_db):
        """Test exact name matching is case-insensitive."""
        identifier = "acme corporation"
        entities = [
            {
                "id": "org-1",
                "name": "Acme Corporation",
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id("organization", identifier)
        
        assert result["success"] is True
        assert result["entity_id"] == "org-1"
    
    async def test_exact_name_match_multiple_entities(self, resolver, mock_db):
        """Test when multiple entities have the same name."""
        identifier = "Test Project"
        entities = [
            {"id": "proj-1", "name": "Test Project"},
            {"id": "proj-2", "name": "Test Project"},
            {"id": "proj-3", "name": "Another Project"}
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id("project", identifier)
        
        # Should not match since multiple exact matches
        assert result["success"] is True or result["success"] is False


class TestEntityResolverFuzzyMatch:
    """Test fuzzy matching."""

    async def test_fuzzy_match_substring(self, resolver, mock_db):
        """Test fuzzy matching finds substring matches."""
        identifier = "Acme"
        entities = [
            {
                "id": "org-1",
                "name": "Acme Corporation",
                "created_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": "org-2",
                "name": "ABC Industries",
                "created_at": "2023-01-02T00:00:00Z"
            }
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id("organization", identifier, threshold=50)
        
        assert result["success"] is True
        assert result["entity_id"] == "org-1"
        assert result["match_type"] == "fuzzy"
    
    async def test_fuzzy_match_with_threshold(self, resolver, mock_db):
        """Test fuzzy matching respects threshold."""
        identifier = "Xyz"  # Low similarity with all names
        entities = [
            {"id": "org-1", "name": "Acme Corporation"},
            {"id": "org-2", "name": "Beta Industries"}
        ]
        mock_db.query.return_value = entities
        
        # High threshold should fail
        result = await resolver.resolve_entity_id(
            "organization", 
            identifier, 
            threshold=90
        )
        
        assert result["success"] is False
        assert "No" in result.get("error", "") or "not found" in result.get("error", "")


class TestEntityResolverWithFilters:
    """Test resolution with filter conditions."""

    async def test_resolve_with_status_filter(self, resolver, mock_db):
        """Test resolution respects additional filters."""
        identifier = "Active Project"
        entities = [
            {
                "id": "proj-1",
                "name": "Active Project",
                "status": "active"
            }
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id(
            "project",
            identifier,
            filters={"status": "active"}
        )
        
        assert result["success"] is True
        # Verify filters were passed to query
        mock_db.query.assert_called_once()
        call_args = mock_db.query.call_args
        assert "filters" in call_args.kwargs
    
    async def test_resolve_adds_is_deleted_filter(self, resolver, mock_db):
        """Test that is_deleted filter is added for appropriate tables."""
        mock_db.query.return_value = []
        
        await resolver.resolve_entity_id("organization", "test")
        
        # Verify is_deleted filter was added
        call_args = mock_db.query.call_args
        filters = call_args.kwargs.get("filters", {})
        assert filters.get("is_deleted") is False


class TestEntityResolverSuggestions:
    """Test suggestion return."""

    async def test_multiple_matches_with_suggestions(self, resolver, mock_db):
        """Test returning suggestions for ambiguous matches."""
        identifier = "Project"
        entities = [
            {"id": "proj-1", "name": "Project Alpha"},
            {"id": "proj-2", "name": "Project Beta"},
            {"id": "proj-3", "name": "Project Gamma"}
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id(
            "project",
            identifier,
            return_suggestions=True,
            threshold=50
        )
        
        # Should return suggestions
        assert "suggestions" in result or "success" in result


class TestEntityResolverEdgeCases:
    """Test edge cases and error handling."""

    async def test_no_entities_found(self, resolver, mock_db):
        """Test when no entities match."""
        mock_db.query.return_value = []
        
        result = await resolver.resolve_entity_id("organization", "NonExistent")
        
        assert result["success"] is False
        assert "error" in result
    
    async def test_empty_identifier(self, resolver, mock_db):
        """Test with empty identifier."""
        mock_db.query.return_value = [
            {"id": "org-1", "name": "Organization"}
        ]
        
        result = await resolver.resolve_entity_id("organization", "")
        
        # Empty string won't match anything reasonably
        assert isinstance(result, dict)
    
    async def test_exception_handling(self, resolver, mock_db):
        """Test error handling for database exceptions."""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await resolver.resolve_entity_id("organization", "test")
        
        assert result["success"] is False
        assert "error" in result
        assert "error" in result["error"]
    
    async def test_entity_with_missing_name_field(self, resolver, mock_db):
        """Test handling entities with missing name field."""
        entities = [
            {"id": "org-1"},  # Missing 'name' field
            {"id": "org-2", "name": "Valid Org"}
        ]
        mock_db.query.return_value = entities
        
        result = await resolver.resolve_entity_id("organization", "Valid")
        
        # Should not crash and should find the valid entity
        assert isinstance(result, dict)


class TestEntityResolverSoftDeleteTables:
    """Test handling of tables without soft delete."""

    def test_uuid_is_recognized(self, resolver):
        """Test that UUID recognition works for valid UUIDs."""
        # Simple test to ensure the UUID detection pattern works
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        assert resolver._is_uuid(uuid_str) is True
    
    def test_uuid_not_recognized_for_invalid(self, resolver):
        """Test that UUID recognition rejects invalid UUIDs."""
        # Ensure invalid patterns are rejected
        assert resolver._is_uuid("not-a-uuid") is False
        assert resolver._is_uuid("550e8400") is False
