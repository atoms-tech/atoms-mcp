"""Entity tool tests - Test case management.

Tests test entity operations (test cases, not pytest tests):
- Create test case
- Read test results

User stories covered:
- User can create test cases
- User can view test results

Run with: pytest tests/unit/tools/test_entity_test.py -v
"""

import uuid
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestTestEntityCRUD:
    """Test case entity CRUD operations."""

    @pytest.mark.story("Test Case Management - User can create test case")
    @pytest.mark.unit
    async def test_create_test_case(self, call_mcp, test_organization):
        """User can create test cases."""
        # Create project first
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        # Create test case entity
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",  # Entity type is "test", not "test_case"
                "data": {
                    "name": f"Test Case {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "description": "Test case description",
                    "test_type": "unit",
                    "status": "pending",
                },
            },
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Test case creation failed"
        assert "id" in data
        assert data.get("project_id") == project_id

    @pytest.mark.story("Test Case Management - User can view test results")
    @pytest.mark.unit
    async def test_read_test_results(self, call_mcp, test_organization):
        """User can view test results."""
        # Create test case first
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        test_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {
                    "name": f"Test to Read {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )

        if hasattr(test_result, "data"):
            test_id = test_result.data.get("data", {}).get("id")
        else:
            test_id = test_result.get("data", {}).get("id")

        # Read test case
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "test",
                "entity_id": test_id,
            }
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Test case read failed"
        assert data.get("id") == test_id
