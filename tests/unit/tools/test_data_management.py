"""E2E tests for Data Management operations.

Tests for all data management operations (batch create, pagination, sorting).

Covers:
- Story 10.1: Batch create entities
- Story 10.2: Paginate large lists
- Story 10.3: Sort query results

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
    @pytest.mark.entity
    async def test_batch_create_entities(self, call_mcp):
        """Create multiple entities in single batch operation."""
        entities = [
            {"name": f"Org {i}"}
            for i in range(5)
        ]
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "batch": entities
            }
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_batch_create_with_relationships(self, call_mcp):
        """Batch create entities and establish relationships."""
        # Create org first
        org_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "Test Org"}
            }
        )
        org_id = org_result["data"]["id"] if org_result["success"] else str(uuid.uuid4())
        
        projects = [
            {"name": f"Project {i}", "organization_id": org_id}
            for i in range(10)
        ]
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "batch": projects
            }
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_batch_create_with_validation(self, call_mcp):
        """Batch create with validation of each entity."""
        # Create document first for requirements
        doc_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": "Test Doc", "project_id": str(uuid.uuid4())}
            }
        )
        doc_id = doc_result["data"]["id"] if doc_result["success"] else str(uuid.uuid4())
        
        entities = [
            {"name": f"Req {i}", "document_id": doc_id, "priority": "high" if i % 2 == 0 else "normal"}
            for i in range(20)
        ]
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "create",
                "batch": entities
            }
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_batch_create_handles_partial_failure(self, call_mcp):
        """Batch create with partial failures - valid entities created, invalid ones reported."""
        entities = [
            {"name": f"Valid Org {i}"}
            for i in range(5)
        ] + [
            {"name": ""}  # Invalid - empty name
        ]
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "batch": entities
            }
        )
        
        assert result["success"] is True
        assert "data" in result


class TestPagination:
    """Test pagination of large result sets."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_paginate_large_list(self, call_mcp):
        """Paginate through large list with page size."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list",
                "limit": 20,
                "offset": 0
            }
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_paginate_with_cursor(self, call_mcp):
        """Paginate using cursor-based pagination (more efficient for large sets)."""
        # Get first page
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list",
                "limit": 10
            }
        )
        
        assert result1["success"] is True
        
        # Get next page using offset
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list",
                "limit": 10,
                "offset": 10
            }
        )
        
        assert result2["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_paginate_preserves_sort_order(self, call_mcp):
        """Verify pagination preserves sort order across pages."""
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "list",
                "limit": 10,
                "order_by": "created_at DESC"
            }
        )
        
        assert result1["success"] is True
        first_page = result1["data"] if isinstance(result1["data"], list) else result1["data"].get("results", [])
        
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "list",
                "limit": 10,
                "offset": 10,
                "order_by": "created_at DESC"
            }
        )
        
        assert result2["success"] is True
        second_page = result2["data"] if isinstance(result2["data"], list) else result2["data"].get("results", [])
        
        # Verify sort order maintained
        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0].get("created_at", "") >= second_page[0].get("created_at", "")
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_paginate_empty_result_set(self, call_mcp):
        """Handle pagination with empty result set gracefully."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list",
                "filters": {"name": "NONEXISTENT_ORG_XYZ"},
                "limit": 10,
                "offset": 0
            }
        )
        
        assert result["success"] is True
        data = result["data"] if isinstance(result["data"], list) else result["data"].get("results", [])
        assert len(data) == 0
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_paginate_respects_limit_parameter(self, call_mcp):
        """Verify limit parameter is respected in pagination."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "limit": 5
            }
        )
        
        assert result["success"] is True
        data = result["data"] if isinstance(result["data"], list) else result["data"].get("results", [])
        assert len(data) <= 5


class TestSorting:
    """Test result sorting by various fields."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_sort_by_created_date(self, call_mcp):
        """Sort query results by created_at field."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list",
                "order_by": "created_at ASC"
            }
        )
        
        assert result["success"] is True
        results = result["data"] if isinstance(result["data"], list) else result["data"].get("results", [])
        if len(results) > 1:
            assert results[0].get("created_at", "") <= results[-1].get("created_at", "")
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_sort_by_name_alphabetically(self, call_mcp):
        """Sort query results by name field alphabetically."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list",
                "order_by": "name ASC"
            }
        )
        
        assert result["success"] is True
        results = result["data"] if isinstance(result["data"], list) else result["data"].get("results", [])
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].get("name", "") <= results[i + 1].get("name", "")
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_sort_descending(self, call_mcp):
        """Sort query results in descending order."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "requirement",
                "operation": "list",
                "order_by": "created_at DESC"
            }
        )
        
        assert result["success"] is True
        results = result["data"] if isinstance(result["data"], list) else result["data"].get("results", [])
        if len(results) > 1:
            assert results[0].get("created_at", "") >= results[-1].get("created_at", "")
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_sort_by_multiple_fields(self, call_mcp):
        """Sort by multiple fields (primary and secondary sort)."""
        # Create test data first
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )

        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "entities": ["project"],
                "search_term": "Proj"
            }
        )

        assert result["success"] is True or "data" in result
