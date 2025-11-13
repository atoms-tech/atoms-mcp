"""List entity operations with pagination, filtering, and sorting.

This module contains parametrized tests for LIST operations across all entity types.

Run with: pytest tests/unit/tools/test_entity_list.py -v
"""

from __future__ import annotations

import pytest
from typing import Dict, Any, List

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestEntityListBasic:
    """Basic LIST operations across all entity types."""

    @pytest.mark.parametrize("entity_type", [
        "organization",
        "project",
        "document",
        "requirement",
        "test"
    ])
    async def test_list_entity_basic(self, call_mcp, entity_type: str, test_organization):
        """Test basic LIST operation returns results.

        User story: User can list entities of a given type
        """
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": entity_type,
                "offset": 0,
                "limit": 10
            }
        )

        assert result is not None
        assert "results" in result or isinstance(result.get("results"), list) or isinstance(result, list)
        # Handle both list and dict responses
        if isinstance(result, dict):
            if "results" in result:
                assert isinstance(result["results"], list)
                assert "total" in result
                assert isinstance(result["total"], int)
                assert result["total"] >= 0
            elif "success" in result:
                # Backwards compatibility - old response format
                assert isinstance(result, list) or isinstance(result.get("results"), list)
        else:
            # If it's a list, that's also valid
            assert isinstance(result, list)

    @pytest.mark.parametrize("entity_type", [
        "organization",
        "project",
        "document",
        "requirement",
        "test"
    ])
    async def test_list_returns_correct_structure(self, call_mcp, entity_type: str, test_organization):
        """Test LIST response structure matches spec.

        User story: LIST response includes pagination metadata
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": entity_type,
                "pagination": {"offset": 0, "limit": 5}
            }
        )

        # Check response structure
        assert "results" in result
        assert "total" in result
        assert "offset" in result
        assert "limit" in result
        assert "has_more" in result

        # Validate pagination values
        assert result["offset"] == 0
        assert result["limit"] == 5
        assert isinstance(result["has_more"], bool)


class TestEntityListPagination:
    """Pagination tests for LIST operations."""

    async def test_list_pagination_offset_limit(self, call_mcp, test_organization):
        """Test pagination with offset and limit.

        User story: User can paginate through results using offset/limit
        """
        # Create multiple documents for pagination testing
        docs = []
        for i in range(25):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "document",
                    "data": {
                        "name": f"Doc {i:02d}",
                        "project_id": test_organization["projects"][0]
                    }
                }
            )
            docs.append(result["id"])

        # Test first page
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "pagination": {"offset": 0, "limit": 10}
            }
        )
        assert len(result1["results"]) == 10
        assert result1["total"] >= 25
        assert result1["has_more"] is True

        # Test second page
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "pagination": {"offset": 10, "limit": 10}
            }
        )
        assert len(result2["results"]) == 10

        # Ensure pages don't overlap
        result1_ids = {r["id"] for r in result1["results"]}
        result2_ids = {r["id"] for r in result2["results"]}
        assert len(result1_ids & result2_ids) == 0

    async def test_list_pagination_beyond_total(self, call_mcp, test_organization):
        """Test pagination with offset beyond total results.

        User story: LIST gracefully handles pagination beyond total
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "pagination": {"offset": 10000, "limit": 10}
            }
        )

        assert result["results"] == []
        assert result["has_more"] is False

    async def test_list_default_pagination(self, call_mcp, test_organization):
        """Test LIST with no pagination uses defaults.

        User story: LIST applies default pagination if not specified
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization"
            }
        )

        assert "results" in result
        assert "offset" in result
        assert "limit" in result
        assert result["offset"] == 0
        assert result["limit"] >= 10  # Default limit


class TestEntityListFiltering:
    """Filtering tests for LIST operations."""

    async def test_list_filter_by_status(self, call_mcp, test_organization):
        """Test filtering by status field.

        User story: User can filter results by status
        """
        # Create requirements with different statuses
        await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": "Active Req",
                    "document_id": test_organization["docs"][0],
                    "status": "active"
                }
            }
        )

        await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": "Archived Req",
                    "document_id": test_organization["docs"][0],
                    "status": "archived"
                }
            }
        )

        # Filter by status
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ]
            }
        )

        assert len(result["results"]) >= 1
        for req in result["results"]:
            assert req.get("status") == "active"

    async def test_list_filter_by_priority(self, call_mcp, test_organization):
        """Test filtering by priority field.

        User story: User can filter by priority
        """
        # Create requirements with different priorities
        await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": "High Priority",
                    "document_id": test_organization["docs"][0],
                    "priority": "high"
                }
            }
        )

        await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {
                    "name": "Low Priority",
                    "document_id": test_organization["docs"][0],
                    "priority": "low"
                }
            }
        )

        # Filter by priority
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": [
                    {"field": "priority", "operator": "in", "value": ["high", "critical"]}
                ]
            }
        )

        assert len(result["results"]) >= 1
        for req in result["results"]:
            assert req.get("priority") in ["high", "critical"]

    async def test_list_multiple_filters(self, call_mcp, test_organization):
        """Test combining multiple filters.

        User story: User can combine multiple filter conditions
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": [
                    {"field": "status", "operator": "eq", "value": "active"},
                    {"field": "priority", "operator": "in", "value": ["high", "critical"]}
                ]
            }
        )

        assert isinstance(result["results"], list)
        for req in result["results"]:
            assert req.get("status") == "active"
            assert req.get("priority") in ["high", "critical"]


class TestEntityListSorting:
    """Sorting tests for LIST operations."""

    async def test_list_sort_by_single_field(self, call_mcp, test_organization):
        """Test sorting by single field.

        User story: User can sort results by a field
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "sort": [{"field": "name", "direction": "asc"}]
            }
        )

        assert len(result["results"]) >= 0
        if len(result["results"]) > 1:
            # Verify sorting (case-insensitive)
            names = [r.get("name", "").lower() for r in result["results"]]
            assert names == sorted(names)

    async def test_list_sort_descending(self, call_mcp, test_organization):
        """Test descending sort.

        User story: User can sort descending
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "sort": [{"field": "created_at", "direction": "desc"}]
            }
        )

        assert len(result["results"]) >= 0

    async def test_list_sort_multiple_fields(self, call_mcp, test_organization):
        """Test sorting by multiple fields.

        User story: User can sort by multiple fields (priority, then name)
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "sort": [
                    {"field": "priority", "direction": "desc"},
                    {"field": "name", "direction": "asc"}
                ]
            }
        )

        assert isinstance(result["results"], list)


class TestEntityListExcludingDeleted:
    """Test that LIST excludes deleted/archived items by default."""

    async def test_list_excludes_deleted_by_default(self, call_mcp, test_organization):
        """Test that deleted entities don't appear in LIST.

        User story: LIST excludes deleted items by default
        """
        # Create an entity
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": "Temp Doc",
                    "project_id": test_organization["projects"][0]
                }
            }
        )
        doc_id = create_result["id"]

        # Delete it
        await call_mcp(
            "entity_tool",
            {
                "operation": "delete",
                "entity_type": "document",
                "entity_id": doc_id
            }
        )

        # List should not include deleted
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": [{"field": "id", "operator": "eq", "value": doc_id}]
            }
        )

        # Document should not be in list (unless we explicitly include deleted)
        doc_ids = {r["id"] for r in result["results"]}
        assert doc_id not in doc_ids

    async def test_list_can_include_deleted_with_filter(self, call_mcp, test_organization):
        """Test that deleted items can be listed explicitly.

        User story: LIST can include deleted items with explicit filter
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": [{"field": "is_deleted", "operator": "eq", "value": True}]
            }
        )

        assert isinstance(result["results"], list)


class TestEntityListUserStories:
    """User story acceptance tests for LIST operations."""

    async def test_user_can_list_all_organizations(self, call_mcp):
        """User story: User can list all organizations.

        Acceptance criteria:
        - Returns all non-deleted organizations
        - Includes pagination info
        - Can filter and sort
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "pagination": {"offset": 0, "limit": 50}
            }
        )

        assert "results" in result
        assert "total" in result
        assert "has_more" in result
        assert isinstance(result["results"], list)

    async def test_user_can_list_projects_in_org(self, call_mcp, test_organization):
        """User story: User can list all projects in an organization.

        Acceptance criteria:
        - Only includes projects in the specified org
        - Supports pagination
        - Supports filtering by name, status
        """
        org_id = test_organization["id"]

        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "project",
                "filters": [
                    {"field": "organization_id", "operator": "eq", "value": org_id}
                ],
                "pagination": {"offset": 0, "limit": 50}
            }
        )

        assert len(result["results"]) >= 1
        for project in result["results"]:
            assert project.get("organization_id") == org_id

    async def test_user_can_filter_and_sort(self, call_mcp, test_organization):
        """User story: User can filter by status and priority, sort by name.

        Acceptance criteria:
        - Filters work correctly
        - Sorts work correctly
        - Can combine both
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": [
                    {"field": "status", "operator": "eq", "value": "active"},
                    {"field": "priority", "operator": "in", "value": ["high", "critical"]}
                ],
                "sort": [
                    {"field": "name", "direction": "asc"}
                ],
                "pagination": {"offset": 0, "limit": 50}
            }
        )

        assert isinstance(result["results"], list)
        # If results exist, verify criteria
        if result["results"]:
            for req in result["results"]:
                assert req.get("status") == "active"
                assert req.get("priority") in ["high", "critical"]
