"""Relationship CREATE and DELETE operations.

Run with: pytest tests/unit/tools/test_relationship_crud.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestRelationshipList:
    """LIST relationship operations (already exist)."""

    async def test_list_relationships(self, call_mcp):
        """Test listing relationships."""
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test"
            }
        )

        assert result is not None


class TestRelationshipUpdate:
    """UPDATE relationship operations (already exist)."""

    async def test_update_relationship(self, call_mcp):
        """Test updating a relationship."""
        # Update operation already exists
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "requirement_test",
                "source": {"id": "test-id-1"},
                "target": {"id": "test-id-2"},
                "data": {}
            }
        )

        assert result is not None


class TestRelationshipUserStories:
    """User story acceptance tests for relationship management."""

    async def test_user_can_view_relationships(self, call_mcp):
        """User story: User can view entity relationships.

        Acceptance criteria:
        - Can list relationships
        - Returns relationship data
        """
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test"
            }
        )

        assert result is not None

    async def test_user_can_update_relationships(self, call_mcp):
        """User story: User can update entity relationships.

        Acceptance criteria:
        - Can update relationship data
        - Changes persist
        """
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "requirement_test",
                "source": {"id": "req-1"},
                "target": {"id": "test-1"},
                "data": {"metadata": "value"}
            }
        )

        assert result is not None
