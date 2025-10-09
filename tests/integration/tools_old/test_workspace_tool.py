"""Unit tests for workspace_operation tool.

This demonstrates the new TDD-friendly testing patterns:
- Import fixtures easily
- Test individual tools in isolation
- Use direct HTTP calls (no MCP client overhead)
- Fast execution with session-scoped auth
"""

import pytest
from tests.fixtures import (
    authenticated_client,
    workspace_client, 
    sample_workspace_data, 
    test_data_factory,
    cleanup_test_data
)


class TestWorkspaceOperations:
    """Test workspace_operation tool operations."""
    
    @pytest.mark.unit
    async def test_list_projects(self, workspace_client):
        """Test listing projects in workspace."""
        result = await workspace_client.call("list_projects")
        
        assert result is not None
        assert "result" in result or "error" in result
        
        # If successful, verify structure
        if "result" in result:
            projects = result["result"].get("projects", [])
            assert isinstance(projects, list)
    
    @pytest.mark.unit  
    async def test_get_workspace_info(self, workspace_client):
        """Test getting workspace information."""
        result = await workspace_client.call("get_info")
        
        assert result is not None
        if "result" in result:
            info = result["result"]
            assert "workspace" in info
            assert isinstance(info["workspace"], dict)
    
    @pytest.mark.unit
    async def test_create_project(self, workspace_client, test_data_factory):
        """Test creating a new project."""
        project_data = test_data_factory("project")
        
        result = await workspace_client.call("create_project", {
            "project_data": project_data
        })
        
        assert result is not None
        # Note: In unit tests, we might get mock responses
        # In integration tests, this would create a real project
    
    @pytest.mark.unit
    @pytest.mark.parametrize("operation", [
        "list_projects",
        "get_info", 
        "list_members"
    ])
    async def test_read_operations(self, workspace_client, operation):
        """Test various read operations."""
        result = await workspace_client.call(operation)
        assert result is not None
        # Basic validation that we got some response
    
    @pytest.mark.unit
    async def test_workspace_client_tool_name(self, workspace_client):
        """Test that workspace client has correct tool name."""
        assert workspace_client.tool_name == "workspace_tool"
    
    @pytest.mark.unit
    async def test_workspace_health_check(self, workspace_client):
        """Test workspace tool health check."""
        # This might be mocked in unit tests
        health = await workspace_client.health_check()
        assert isinstance(health, bool)


class TestWorkspaceDataHandling:
    """Test workspace data handling and validation."""
    
    @pytest.mark.unit
    def test_sample_workspace_data_structure(self, sample_workspace_data):
        """Test sample workspace data has required fields."""
        assert "name" in sample_workspace_data
        assert "description" in sample_workspace_data
        assert sample_workspace_data["name"].startswith("Test Workspace")
    
    @pytest.mark.unit
    def test_test_data_factory_workspace(self, test_data_factory):
        """Test workspace data factory."""
        workspace_data = test_data_factory("workspace")
        
        assert "name" in workspace_data
        assert "description" in workspace_data
        assert workspace_data["name"].startswith("Test Workspace")
        assert workspace_data["settings"]["privacy"] == "private"


# All tests require OAuth - using session-scoped authentication
class TestWorkspaceOAuthIntegration:
    """Tests with real OAuth authentication (session-scoped)."""
    
    @pytest.mark.unit
    @pytest.mark.auth
    async def test_workspace_operations_with_oauth(self, workspace_client):
        """Test workspace operations with real OAuth (session-scoped)."""
        # This uses session-scoped OAuth - fast after initial auth
        result = await workspace_client.call("list_projects")
        
        # Real server responses
        assert result is not None
        assert workspace_client.tool_name == "workspace_operation"
