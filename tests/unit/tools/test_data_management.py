"""E2E tests for Data Management operations.

This file validates end-to-end data management functionality:
- Batch creating entities for bulk operations
- Paginating large result lists efficiently
- Sorting query results by various fields
- Managing data consistency and relationships

Test Coverage: 12 test scenarios covering 3 user stories.
File follows canonical naming - describes WHAT is tested (data management).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestBatchCreation:
    """Test batch entity creation."""
    
    @pytest.mark.asyncio
    async def test_batch_create_entities(self, call_mcp):
        """Create multiple entities in single batch operation."""
        entities = [
            {"name": f"Org {i}", "type": "organization"}
            for i in range(5)
        ]
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "batch_create",
                "parameters": {
                    "entity_type": "organization",
                    "entities": entities
                }
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "created_count" in result["data"]
        assert result["data"]["created_count"] == 5
    
    @pytest.mark.asyncio
    async def test_batch_create_with_relationships(self, call_mcp):
        """Batch create entities and establish relationships."""
        org_id = str(uuid.uuid4())
        projects = [
            {"name": f"Project {i}", "organization_id": org_id}
            for i in range(10)
        ]
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "batch_create_with_relationships",
                "parameters": {
                    "entity_type": "project",
                    "entities": projects,
                    "relationships": {
                        "parent_id": org_id,
                        "relationship_type": "belongs_to"
                    }
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["created_count"] == 10
        assert result["data"]["relationships_created"] == 10
    
    @pytest.mark.asyncio
    async def test_batch_create_with_validation(self, call_mcp):
        """Batch create with validation of each entity."""
        entities = [
            {"title": f"Req {i}", "priority": "high" if i % 2 == 0 else "normal"}
            for i in range(20)
        ]
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "batch_create_with_validation",
                "parameters": {
                    "entity_type": "requirement",
                    "entities": entities,
                    "validate": True
                }
            }
        )
        
        assert result["success"] is True
        assert "validation_results" in result["data"]
    
    @pytest.mark.asyncio
    async def test_batch_create_handles_partial_failure(self, call_mcp):
        """Batch create with partial failures - valid entities created, invalid ones reported."""
        entities = [
            {"name": f"Valid Org {i}"}
            for i in range(5)
        ] + [
            {"name": ""}  # Invalid - empty name
        ]
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "batch_create",
                "parameters": {
                    "entity_type": "organization",
                    "entities": entities,
                    "continue_on_error": True
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["created_count"] == 5
        assert "failed_items" in result["data"]


class TestPagination:
    """Test pagination of large result sets."""
    
    @pytest.mark.asyncio
    async def test_paginate_large_list(self, call_mcp):
        """Paginate through large list with page size."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "organization",
                "limit": 20,
                "offset": 0
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "results" in result["data"]
        assert "total_count" in result["data"]
    
    @pytest.mark.asyncio
    async def test_paginate_with_cursor(self, call_mcp):
        """Paginate using cursor-based pagination (more efficient for large sets)."""
        # Get first page
        result1, _ = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "project",
                "limit": 10
            }
        )
        
        assert result1["success"] is True
        assert "next_cursor" in result1["data"]
        
        # Get next page using cursor
        result2, _ = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "project",
                "limit": 10,
                "cursor": result1["data"]["next_cursor"]
            }
        )
        
        assert result2["success"] is True
    
    @pytest.mark.asyncio
    async def test_paginate_preserves_sort_order(self, call_mcp):
        """Verify pagination preserves sort order across pages."""
        result1, _ = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "limit": 10,
                "sort": {"field": "created_at", "order": "desc"}
            }
        )
        
        assert result1["success"] is True
        first_page = result1["data"]["results"]
        
        result2, _ = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "limit": 10,
                "offset": 10,
                "sort": {"field": "created_at", "order": "desc"}
            }
        )
        
        assert result2["success"] is True
        second_page = result2["data"]["results"]
        
        # Verify sort order maintained
        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0]["created_at"] >= second_page[0]["created_at"]
    
    @pytest.mark.asyncio
    async def test_paginate_empty_result_set(self, call_mcp):
        """Handle pagination with empty result set gracefully."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "organization",
                "filters": {"name": "NONEXISTENT_ORG_XYZ"},
                "limit": 10,
                "offset": 0
            }
        )
        
        assert result["success"] is True
        assert result["data"]["total_count"] == 0
        assert result["data"]["results"] == []
    
    @pytest.mark.asyncio
    async def test_paginate_respects_limit_parameter(self, call_mcp):
        """Verify limit parameter is respected in pagination."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "document",
                "limit": 5
            }
        )
        
        assert result["success"] is True
        assert len(result["data"]["results"]) <= 5


class TestSorting:
    """Test result sorting by various fields."""
    
    @pytest.mark.asyncio
    async def test_sort_by_created_date(self, call_mcp):
        """Sort query results by created_at field."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "project",
                "sort": {"field": "created_at", "order": "asc"}
            }
        )
        
        assert result["success"] is True
        results = result["data"]["results"]
        if len(results) > 1:
            assert results[0]["created_at"] <= results[-1]["created_at"]
    
    @pytest.mark.asyncio
    async def test_sort_by_name_alphabetically(self, call_mcp):
        """Sort query results by name field alphabetically."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "organization",
                "sort": {"field": "name", "order": "asc"}
            }
        )
        
        assert result["success"] is True
        results = result["data"]["results"]
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["name"] <= results[i + 1]["name"]
    
    @pytest.mark.asyncio
    async def test_sort_descending(self, call_mcp):
        """Sort query results in descending order."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "sort": {"field": "created_at", "order": "desc"}
            }
        )
        
        assert result["success"] is True
        results = result["data"]["results"]
        if len(results) > 1:
            assert results[0]["created_at"] >= results[-1]["created_at"]
    
    @pytest.mark.asyncio
    async def test_sort_by_multiple_fields(self, call_mcp):
        """Sort by multiple fields (primary and secondary sort)."""
        result, duration_ms = await call_mcp(
            "data_query",
            {
                "query_type": "search",
                "entity_type": "requirement",
                "sort": [
                    {"field": "priority", "order": "desc"},
                    {"field": "created_at", "order": "asc"}
                ]
            }
        )
        
        assert result["success"] is True
        assert "results" in result["data"]
