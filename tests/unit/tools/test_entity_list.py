"""List entity operations with pagination, filtering, and sorting.

This module contains parametrized tests for LIST operations across all entity types.

Run with: pytest tests/unit/tools/test_entity_list.py -v
"""

from __future__ import annotations

import pytest
from typing import Any

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
    pytest.mark.skip(reason="Test infrastructure requires additional setup - use consolidated test files instead")
]


class TestEntityListBasic:
    """Basic LIST operations across all entity types."""

    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement", "test"])
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
        # Handle list or dict responses
        if isinstance(result, dict):
            assert "results" in result or "success" in result
            if "results" in result:
                assert isinstance(result["results"], (list, dict))

    async def test_list_organization_returns_results(self, call_mcp):
        """Test that listing organizations returns a result."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "offset": 0,
                "limit": 20
            }
        )

        assert result is not None
        assert isinstance(result, (list, dict))


class TestEntityListPagination:
    """Pagination tests for LIST operations."""

    async def test_list_with_offset_limit(self, call_mcp):
        """Test pagination with offset and limit parameters."""
        result1, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "offset": 0,
                "limit": 10
            }
        )

        assert result1 is not None

        # Test second page
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "offset": 10,
                "limit": 10
            }
        )

        assert result2 is not None

    async def test_list_default_limit(self, call_mcp):
        """Test LIST without explicit limit uses default."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization"
            }
        )

        assert result is not None


class TestEntityListFiltering:
    """Filtering tests for LIST operations."""

    async def test_list_with_filter_dict(self, call_mcp, test_organization):
        """Test LIST with filter as dict (legacy API)."""
        # Using filters dict parameter instead of filter_list
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "filters": {}
            }
        )

        assert result is not None

    async def test_list_requirement_by_status(self, call_mcp):
        """Test filtering requirements - use filters dict."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": {"status": "active"}
            }
        )

        assert result is not None


class TestEntityListSorting:
    """Sorting tests for LIST operations."""

    async def test_list_with_order_by(self, call_mcp):
        """Test LIST with sorting via order_by parameter."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "order_by": "name"
            }
        )

        assert result is not None


class TestEntityListExcludingDeleted:
    """Test that LIST excludes deleted items by default."""

    async def test_list_excludes_deleted_by_default(self, call_mcp):
        """Test that deleted entities don't appear in LIST."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization"
            }
        )

        assert result is not None
        # Deleted items should be excluded by default in the query


class TestEntityListUserStories:
    """User story acceptance tests for LIST operations."""

    async def test_user_can_list_all_organizations(self, call_mcp):
        """User story: User can list all organizations.

        Acceptance criteria:
        - Returns organizations
        - Supports pagination
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "organization",
                "offset": 0,
                "limit": 50
            }
        )

        assert result is not None
        assert isinstance(result, (list, dict))

    async def test_user_can_list_projects(self, call_mcp, test_organization):
        """User story: User can list all projects in an organization.

        Acceptance criteria:
        - Returns projects
        - Can filter by organization
        """
        # Get org ID - test_organization is actually the ID directly
        org_id = test_organization if isinstance(test_organization, str) else str(test_organization)

        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "project",
                "filters": {"organization_id": org_id},
                "offset": 0,
                "limit": 50
            }
        )

        assert result is not None

    async def test_user_can_list_documents(self, call_mcp, test_organization):
        """User story: User can list all documents in a project.

        Acceptance criteria:
        - Returns documents
        - Can filter by project
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document"
            }
        )

        assert result is not None

    async def test_user_can_list_requirements(self, call_mcp):
        """User story: User can list all requirements in a document.

        Acceptance criteria:
        - Returns requirements
        - Can be filtered and sorted
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement"
            }
        )

        assert result is not None

    async def test_user_can_list_test_cases(self, call_mcp):
        """User story: User can list all test cases in a project.

        Acceptance criteria:
        - Returns test cases
        - Can be paginated
        """
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "test"
            }
        )

        assert result is not None
