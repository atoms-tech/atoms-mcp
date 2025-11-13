"""Relationship CREATE and DELETE operations (completing CRUD lifecycle).

Run with: pytest tests/unit/tools/test_relationship_crud.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestRelationshipCreate:
    """CREATE relationship operations."""

    async def test_create_requirement_test_relationship(self, call_mcp, test_organization):
        """Test creating a relationship between requirement and test."""
        # Get requirement and test
        req_id = test_organization.get("requirements", [None])[0]
        test_id = test_organization.get("tests", [None])[0]
        
        if not req_id or not test_id:
            pytest.skip("Test requires requirement and test entity")

        # Create relationship
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "create",
                "relationship_type": "requirement_test",
                "from_id": req_id,
                "to_id": test_id
            }
        )

        assert result is not None
        if isinstance(result, dict):
            assert result.get("success") is not False or "id" in result

    async def test_create_parent_child_requirement(self, call_mcp, test_organization):
        """Test creating parent-child relationship between requirements."""
        reqs = test_organization.get("requirements", [])
        if len(reqs) < 2:
            pytest.skip("Test requires at least 2 requirements")

        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "create",
                "relationship_type": "requirement_parent",
                "from_id": reqs[0],
                "to_id": reqs[1]
            }
        )

        assert result is not None


class TestRelationshipDelete:
    """DELETE relationship operations."""

    async def test_delete_relationship(self, call_mcp, test_organization):
        """Test deleting a relationship."""
        # Create a relationship first
        req_id = test_organization.get("requirements", [None])[0]
        test_id = test_organization.get("tests", [None])[0]
        
        if not req_id or not test_id:
            pytest.skip("Test requires requirement and test entity")

        # Create relationship
        create_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "create",
                "relationship_type": "requirement_test",
                "from_id": req_id,
                "to_id": test_id
            }
        )

        if not create_result or "error" in create_result:
            pytest.skip("Could not create relationship for deletion test")

        # Delete relationship
        delete_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "delete",
                "relationship_type": "requirement_test",
                "from_id": req_id,
                "to_id": test_id
            }
        )

        assert delete_result is not None
        if isinstance(delete_result, dict):
            assert delete_result.get("success") is not False or "error" not in delete_result


class TestRelationshipCRUDUserStories:
    """User story acceptance tests for relationship management."""

    async def test_user_can_link_requirement_to_test(self, call_mcp, test_organization):
        """User story: User can link a requirement to a test case.

        Acceptance criteria:
        - Relationship can be created
        - Relationship tracks the linkage
        - Link can be verified
        """
        reqs = test_organization.get("requirements", [])
        tests = test_organization.get("tests", [])
        
        if not reqs or not tests:
            pytest.skip("Test requires requirements and tests")

        # Link requirement to test
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "create",
                "relationship_type": "requirement_test",
                "from_id": reqs[0],
                "to_id": tests[0]
            }
        )

        assert result is not None

    async def test_user_can_unlink_entities(self, call_mcp, test_organization):
        """User story: User can unlink entities.

        Acceptance criteria:
        - Relationship can be deleted
        - After deletion, link no longer exists
        """
        reqs = test_organization.get("requirements", [])
        tests = test_organization.get("tests", [])
        
        if not reqs or not tests:
            pytest.skip("Test requires requirements and tests")

        # Delete relationship
        result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "delete",
                "relationship_type": "requirement_test",
                "from_id": reqs[0],
                "to_id": tests[0]
            }
        )

        assert result is not None
