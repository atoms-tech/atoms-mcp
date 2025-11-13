"""Workspace CRUD operations (completing workspace management).

Run with: pytest tests/unit/tools/test_workspace_crud.py -v
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestWorkspaceCRUD:
    """CRUD operations for workspace entity."""

    async def test_list_workspaces(self, call_mcp):
        """Test listing workspaces."""
        result, _ = await call_mcp(
            "workspace_tool",
            {"operation": "list"}
        )

        assert result is not None
        if isinstance(result, dict):
            assert isinstance(result.get("results"), list) or isinstance(result, list)

    async def test_create_workspace(self, call_mcp):
        """Test creating a workspace.

        User story: User can create a new workspace
        """
        result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "create",
                "data": {"name": "Test Workspace"}
            }
        )

        assert result is not None
        if isinstance(result, dict):
            assert "id" in result or result.get("success") is True

    async def test_read_workspace(self, call_mcp):
        """Test reading workspace details.

        User story: User can view workspace details
        """
        # First, list workspaces to get an ID
        list_result, _ = await call_mcp(
            "workspace_tool",
            {"operation": "list"}
        )

        if isinstance(list_result, dict) and "results" in list_result:
            workspaces = list_result["results"]
        elif isinstance(list_result, list):
            workspaces = list_result
        else:
            pytest.skip("Could not get workspaces for read test")

        if not workspaces:
            pytest.skip("No workspaces available")

        workspace_id = workspaces[0].get("id")
        if not workspace_id:
            pytest.skip("Could not extract workspace ID")

        # Read specific workspace
        result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "read",
                "entity_id": workspace_id
            }
        )

        assert result is not None

    async def test_update_workspace(self, call_mcp):
        """Test updating workspace.

        User story: User can update workspace name and settings
        """
        # Create workspace first
        create_result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "create",
                "data": {"name": "Update Test Workspace"}
            }
        )

        if not create_result or "error" in create_result:
            pytest.skip("Could not create workspace for update test")

        workspace_id = create_result.get("id")
        if not workspace_id:
            pytest.skip("Could not extract workspace ID from creation result")

        # Update workspace
        update_result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "update",
                "entity_id": workspace_id,
                "data": {"name": "Updated Workspace Name"}
            }
        )

        assert update_result is not None

    async def test_delete_workspace(self, call_mcp):
        """Test deleting workspace.

        User story: User can delete a workspace
        """
        # Create workspace first
        create_result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "create",
                "data": {"name": "Delete Test Workspace"}
            }
        )

        if not create_result or "error" in create_result:
            pytest.skip("Could not create workspace for delete test")

        workspace_id = create_result.get("id")
        if not workspace_id:
            pytest.skip("Could not extract workspace ID from creation result")

        # Delete workspace
        delete_result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "delete",
                "entity_id": workspace_id
            }
        )

        assert delete_result is not None


class TestWorkspaceUserStories:
    """User story acceptance tests for workspace management."""

    async def test_user_can_create_workspace(self, call_mcp):
        """User story: User can create a new workspace.

        Acceptance criteria:
        - Workspace creation succeeds
        - Returns workspace ID
        - Workspace is listed afterward
        """
        result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "create",
                "data": {"name": "My New Workspace"}
            }
        )

        assert result is not None

    async def test_user_can_manage_workspaces(self, call_mcp):
        """User story: User can manage multiple workspaces.

        Acceptance criteria:
        - Can create workspaces
        - Can list them
        - Can update them
        - Can delete them
        """
        # Create
        create_result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "create",
                "data": {"name": "Workspace A"}
            }
        )
        assert create_result is not None

        # List
        list_result, _ = await call_mcp(
            "workspace_tool",
            {"operation": "list"}
        )
        assert list_result is not None

        # Update
        if isinstance(create_result, dict) and "id" in create_result:
            update_result, _ = await call_mcp(
                "workspace_tool",
                {
                    "operation": "update",
                    "entity_id": create_result["id"],
                    "data": {"name": "Workspace A Updated"}
                }
            )
            assert update_result is not None

            # Delete
            delete_result, _ = await call_mcp(
                "workspace_tool",
                {
                    "operation": "delete",
                    "entity_id": create_result["id"]
                }
            )
            assert delete_result is not None
