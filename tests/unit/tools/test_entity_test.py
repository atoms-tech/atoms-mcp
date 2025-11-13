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
        """User can create test cases.
        
        User Story: User can create test cases
        Acceptance Criteria:
        - Test case can be created with title and project_id
        - Test case gets unique ID
        - Test case is stored successfully
        """
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

        # Parse project result
        if hasattr(project_result, "data"):
            project_data = project_result.data.get("data", {})
        else:
            project_data = project_result.get("data", {})
        
        project_id = project_data.get("id")
        if not project_id:
            pytest.skip("Could not create test project")

        # Create test case entity (entity type is "test", requires "title" not "name")
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {
                    "title": f"Test Case {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "status": "pending",
                    "priority": "medium",
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

        # Verify test case was created
        assert success, f"Test case creation failed: {result}"
        assert "id" in data, "Test case should have an ID"
        assert data.get("project_id") == project_id, "Test case should reference correct project"

    @pytest.mark.story("Test Case Management - User can view test results")
    @pytest.mark.unit
    async def test_read_test_results(self, call_mcp, test_organization):
        """User can view test results.
        
        User Story: User can view test results
        Acceptance Criteria:
        - Test case can be retrieved by ID
        - Retrieved test case has correct fields
        - Test case data is accurate
        """
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

        # Parse project result
        if hasattr(project_result, "data"):
            project_data = project_result.data.get("data", {})
        else:
            project_data = project_result.get("data", {})
        
        project_id = project_data.get("id")
        if not project_id:
            pytest.skip("Could not create test project")

        # Create test case (requires "title" not "name")
        test_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {
                    "title": f"Test to Read {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )

        # Parse test result
        if hasattr(test_result, "data"):
            test_data = test_result.data.get("data", {})
        else:
            test_data = test_result.get("data", {})
        
        test_id = test_data.get("id")
        if not test_id:
            pytest.skip("Could not create test case")

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

        # Verify test case was read successfully
        assert success, f"Test case read failed: {result}"
        assert data.get("id") == test_id, "Retrieved test case should have correct ID"
        assert data.get("project_id") == project_id, "Retrieved test case should reference correct project"
