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

    @pytest.mark.story("Test Case Management - User can update test case")
    @pytest.mark.unit
    async def test_update_test_case(self, call_mcp, test_organization):
        """User can update test case title, steps, expected results, and priority."""
        # Create project
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
        project_id = project_result["data"]["id"]

        # Create test case
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {
                    "title": "Old Test Title",
                    "description": "Original description",
                    "steps": ["Step 1"],
                    "expected_results": ["Result 1"],
                    "priority": "medium",
                    "project_id": project_id,
                },
            },
        )
        assert result["success"]
        test_id = result["data"]["id"]
        assert result["data"]["title"] == "Old Test Title"

        # Update fields
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update",
                "entity_type": "test",
                "entity_id": test_id,
                "data": {
                    "title": "Updated Test Title",
                    "description": "Updated description",
                    "steps": ["Step 1", "Step 2"],
                    "expected_results": ["Result 1", "Result 2"],
                    "priority": "high",
                },
            },
        )
        assert update_result["success"]
        assert update_result["data"]["title"] == "Updated Test Title"
        assert update_result["data"]["description"] == "Updated description"
        assert update_result["data"]["steps"] == ["Step 1", "Step 2"]
        assert update_result["data"]["expected_results"] == ["Result 1", "Result 2"]
        assert update_result["data"]["priority"] == "high"

    @pytest.mark.story("Test Case Management - User can soft delete test case")
    @pytest.mark.unit
    async def test_soft_delete_test_case(self, call_mcp, test_organization):
        """User can soft delete a test case; it won't appear in default lists."""
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Test Del Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        project_id = project_result["data"]["id"]

        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {
                    "title": "To Delete Test",
                    "description": "Desc",
                    "project_id": project_id,
                },
            },
        )
        assert result["success"]
        test_id = result["data"]["id"]

        # Soft delete
        delete_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "delete", "entity_type": "test", "entity_id": test_id, "soft_delete": True},
        )
        assert delete_result["success"]

        # Verify excluded from default list
        list_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "list", "entity_type": "test", "filters": {"project_id": project_id}},
        )
        items = list_result.get("results", list_result.get("data", []))
        assert all(d["id"] != test_id for d in items)

        # Verify can include with filter
        list_inc_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "list", "entity_type": "test", "filters": {"project_id": project_id, "is_deleted": True}},
        )
        items = list_inc_result.get("results", []); print(f"LIST INC RESULT: {list_inc_result}"); assert any(d["id"] == test_id for d in items)

    @pytest.mark.story("Test Case Management - User can hard delete test case")
    @pytest.mark.unit
    async def test_hard_delete_test_case(self, call_mcp, test_organization):
        """User can permanently delete a test case."""
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Test Hard Del Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )
        project_id = project_result["data"]["id"]

        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {
                    "title": "To Delete Hard Test",
                    "description": "Desc",
                    "project_id": project_id,
                },
            },
        )
        assert result["success"]
        test_id = result["data"]["id"]

        # Hard delete
        delete_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "delete", "entity_type": "test", "entity_id": test_id, "soft_delete": False},
        )
        assert delete_result["success"]

        # Verify gone even with is_deleted filter
        list_result, _ = await call_mcp(
            "entity_tool",
            {"operation": "list", "entity_type": "test", "filters": {"project_id": project_id, "is_deleted": True}},
        )
        assert all(d["id"] != test_id for d in list_result.get("data", {}).get("items", []))
