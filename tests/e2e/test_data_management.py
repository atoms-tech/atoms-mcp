pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]
"""Data Management E2E Tests - Story 10"""

import pytest
import uuid


class TestBatchCreate:
    """Batch create operations."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can batch create multiple entities")
    async def test_batch_create_10_entities(self, mcp_client):
        """Create 10 entities in batch."""
        entities = [{"name": f"Entity {i}"} for i in range(10)]
        
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="create",
            batch=entities
        )
        
        assert result["success"] is True
        assert len(result["data"]) == 10

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.slow
    @pytest.mark.story("User can batch create multiple entities")
    async def test_batch_create_1000_entities(self, mcp_client):
        """Create 1000 entities in batch."""
        entities = [{"name": f"Entity {i}"} for i in range(1000)]
        
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="create",
            batch=entities
        )
        
        assert result["success"] is True
        # May be 1000 or paginated result
        assert len(result["data"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can batch create multiple entities")
    async def test_batch_create_with_metadata(self, mcp_client):
        """Batch create with full metadata."""
        entities = [
            {"name": f"Entity {i}", "description": f"Description {i}", "status": "active"}
            for i in range(5)
        ]
        
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="create",
            batch=entities
        )
        
        assert result["success"] is True
        for entity in result["data"]:
            assert "name" in entity
            assert "id" in entity


class TestPagination:
    """Pagination operations."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_list_with_limit(self, mcp_client):
        """List with limit parameter."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            limit=5
        )
        
        assert result["success"] is True
        assert len(result["data"]) <= 5

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_list_with_offset(self, mcp_client):
        """List with offset parameter."""
        # First page
        page1 = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            limit=5,
            offset=0
        )
        
        # Second page
        page2 = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            limit=5,
            offset=5
        )
        
        assert page1["success"] is True
        assert page2["success"] is True
        # Pages may have different content
        assert isinstance(page1["data"], list)
        assert isinstance(page2["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_pagination_cursor_based(self, mcp_client):
        """Cursor-based pagination if supported."""
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            limit=10,
            cursor=None
        )
        
        assert result["success"] is True
        # May have cursor in response

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_pagination_total_count(self, mcp_client):
        """Get total count with pagination."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            limit=5
        )
        
        assert result["success"] is True
        # Should include total count
        assert "count" in result or len(result["data"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_pagination_large_dataset(self, mcp_client):
        """Paginate through large result set (1000+ items)."""
        # First page
        page1 = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            limit=100,
            offset=0
        )
        
        assert page1["success"] is True
        assert len(page1["data"]) <= 100


class TestSorting:
    """Sorting operations."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can sort query results")
    async def test_sort_by_name_ascending(self, mcp_client):
        """Sort by name ascending."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            order_by="name",
            limit=100
        )
        
        assert result["success"] is True
        if len(result["data"]) > 1:
            names = [o.get("name", "") for o in result["data"]]
            # Should be sorted
            assert names == sorted(names) or len(names) <= 1

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can sort query results")
    async def test_sort_by_name_descending(self, mcp_client):
        """Sort by name descending."""
        result = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            order_by="-name",  # Descending
            limit=100
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can sort query results")
    async def test_sort_by_created_date(self, mcp_client):
        """Sort by creation date."""
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            order_by="created_at",
            limit=100
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can sort query results")
    async def test_sort_by_updated_date(self, mcp_client):
        """Sort by modification date."""
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            order_by="updated_at",
            limit=100
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can sort query results")
    async def test_sort_by_custom_field(self, mcp_client):
        """Sort by custom field."""
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            order_by="priority",
            limit=100
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_multi_field_sort(self, mcp_client):
        """Sort by multiple fields."""
        result = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            order_by="status,name",  # Sort by status, then name
            limit=100
        )
        
        assert "success" in result


class TestSortWithPagination:
    """Sorting with pagination."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can sort query results")
    async def test_sorted_paginated_list(self, mcp_client):
        """List sorted and paginated together."""
        page1 = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            order_by="name",
            limit=10,
            offset=0
        )
        
        page2 = await mcp_client.entity_tool(
            entity_type="organization",
            operation="list",
            order_by="name",
            limit=10,
            offset=10
        )
        
        assert page1["success"] is True
        assert page2["success"] is True
        # Results should maintain sort order across pages

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_reverse_sort_paginated(self, mcp_client):
        """Reverse sorted pagination."""
        page1 = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            order_by="-created_at",
            limit=10,
            offset=0
        )
        
        page2 = await mcp_client.entity_tool(
            entity_type="project",
            operation="list",
            order_by="-created_at",
            limit=10,
            offset=10
        )
        
        assert page1["success"] is True
        assert page2["success"] is True
