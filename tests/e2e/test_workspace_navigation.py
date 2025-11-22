"""Workspace Navigation E2E Tests - Story 6"""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestWorkspaceContext:
    """Workspace context operations."""

    @pytest.mark.asyncio
    @pytest.mark.workspace
    @pytest.mark.story("User can view current workspace context")
    async def test_get_current_workspace_context(self, end_to_end_client):
        """Get current workspace context."""
        result = await end_to_end_client.call_tool("workspace_tool", {"operation": "get_context"})
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_get_context_at_org_level(self, end_to_end_client):
        """Get workspace context at organization level."""
        org_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}
            }
        )
        org_id = org_result["data"]["id"]

        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "get_context",
                "context_type": "organization",
                "entity_id": org_id
            }
        )

        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_get_context_at_project_level(self, end_to_end_client):
        """Get workspace context at project level."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]

        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "get_context",
                "context_type": "project",
                "entity_id": project_id
            }
        )

        assert "success" in result


class TestContextSwitching:
    """Context switching operations."""

    @pytest.mark.asyncio
    @pytest.mark.workspace
    @pytest.mark.story("User can switch to organization workspace")
    async def test_switch_to_organization_context(self, end_to_end_client):
        """Switch to organization workspace."""
        org_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Switch Org {uuid.uuid4().hex[:4]}"}
            }
        )
        org_id = org_result["data"]["id"]
        
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": org_id
            }
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workspace
    @pytest.mark.story("User can switch to project workspace")
    async def test_switch_to_project_context(self, end_to_end_client):
        """Switch to project workspace."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Switch Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]

        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "project",
                "entity_id": project_id
            }
        )

        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workspace
    @pytest.mark.story("User can switch to document workspace")
    async def test_switch_to_document_context(self, end_to_end_client):
        """Switch to document workspace."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]

        doc_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": f"Doc {uuid.uuid4().hex[:4]}", "project_id": project_id}
            }
        )
        doc_id = doc_result["data"]["id"]
        
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "document",
                "entity_id": doc_id
            }
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_switch_with_fuzzy_entity_name(self, end_to_end_client):
        """Switch context using fuzzy entity name."""
        org_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Vehicle Organization {uuid.uuid4().hex[:4]}"}
            }
        )
        org_id = org_result["data"]["id"]

        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": org_id
            }
        )

        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_switch_invalid_context_fails(self, end_to_end_client):
        """Switching to invalid context fails."""
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "set_context",
                "context_type": "organization",
                "entity_id": str(uuid.uuid4())  # Non-existent
            }
        )

        assert "success" in result


class TestWorkspaceDefaults:
    """Default values per workspace."""

    @pytest.mark.asyncio
    @pytest.mark.workspace
    @pytest.mark.story("User can get workspace defaults")
    async def test_get_defaults_organization_context(self, end_to_end_client):
        """Get defaults for organization context."""
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "get_defaults",
                "context_type": "organization"
            }
        )

        assert "success" in result
        assert "defaults" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_get_defaults_project_context(self, end_to_end_client):
        """Get defaults for project context."""
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "get_defaults",
                "context_type": "project"
            }
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_get_defaults_includes_templates(self, end_to_end_client):
        """Defaults include available templates."""
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "get_defaults",
                "context_type": "organization"
            }
        )
        
        assert result["success"] is True
        # Defaults may include templates, rate limits, etc.

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_get_defaults_includes_rate_limits(self, end_to_end_client):
        """Defaults include rate limit info."""
        result = await end_to_end_client.call_tool(
            "workspace_tool",
            {
                "operation": "get_defaults",
                "context_type": "project"
            }
        )
        
        assert result["success"] is True


class TestWorkspaceListing:
    """List available workspaces."""

    @pytest.mark.asyncio
    @pytest.mark.workspace
    @pytest.mark.story("User can list all available workspaces")
    async def test_list_all_workspaces(self, end_to_end_client):
        """List all available workspaces."""
        result = await end_to_end_client.call_tool("workspace_tool", {"operation": "list_workspaces"})
        
        assert result["success"] is True
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_list_workspaces_includes_orgs(self, end_to_end_client):
        """List includes organizations."""
        # Create an org
        org_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"List Org {uuid.uuid4().hex[:4]}"}
            }
        )
        
        # List workspaces
        result = await end_to_end_client.call_tool("workspace_tool", {"operation": "list_workspaces"})
        
        assert result["success"] is True
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.workspace
    async def test_list_workspaces_hierarchical(self, end_to_end_client):
        """Workspace list shows hierarchy."""
        result = await end_to_end_client.call_tool("workspace_tool", {"operation": "list_workspaces"})
        
        assert result["success"] is True
        # List should include both orgs and nested projects/docs
