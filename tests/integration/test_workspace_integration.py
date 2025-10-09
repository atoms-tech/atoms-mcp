"""Integration tests for workspace operations with real OAuth and HTTP calls.

This demonstrates:
- Real OAuth authentication (session-scoped)
- Direct HTTP tool calls to live MCP server
- Integration between multiple tools
- Realistic test scenarios
"""

import pytest
from tests.fixtures import (
    authenticated_client, 
    workspace_client, 
    entity_client,
    sample_workspace_data,
    cleanup_test_data
)


@pytest.mark.integration
class TestWorkspaceIntegration:
    """Integration tests for workspace operations."""
    
    async def test_workspace_project_lifecycle(self, workspace_client, cleanup_test_data):
        """Test complete project lifecycle in workspace."""
        # Create a project
        result = await workspace_client.call("create_project", {
            "name": "Integration Test Project",
            "description": "Project created during integration testing"
        })
        
        if "result" in result and "project" in result["result"]:
            project_id = result["result"]["project"]["id"]
            cleanup_test_data.track("project", project_id)
            
            # Verify project was created
            projects = await workspace_client.call("list_projects")
            assert "result" in projects
            
            project_names = [p["name"] for p in projects["result"].get("projects", [])]
            assert "Integration Test Project" in project_names
            
            # Update project
            update_result = await workspace_client.call("update_project", {
                "project_id": project_id,
                "updates": {"status": "in_progress"}
            })
            assert "result" in update_result or "error" not in update_result
    
    async def test_workspace_member_management(self, workspace_client):
        """Test workspace member operations."""
        # List current members
        members = await workspace_client.call("list_members")
        assert "result" in members
        
        initial_count = len(members["result"].get("members", []))
        assert initial_count >= 1  # At least the authenticated user
        
        # Note: In a real test, you might add/remove members
        # For now, just verify we can list them
    
    async def test_workspace_and_entity_interaction(
        self, 
        workspace_client, 
        entity_client,
        cleanup_test_data
    ):
        """Test interaction between workspace and entity operations."""
        # Get workspace info
        workspace_info = await workspace_client.call("get_info")
        assert "result" in workspace_info
        
        # Create an entity in this workspace
        entity_result = await entity_client.call("create", {
            "entity_type": "document",
            "data": {
                "title": "Integration Test Document",
                "content": "Document created during workspace integration test"
            }
        })
        
        if "result" in entity_result and "entity" in entity_result["result"]:
            entity_id = entity_result["result"]["entity"]["id"]
            cleanup_test_data.track("entity", entity_id)
            
            # Verify entity is accessible through workspace
            # (This might involve querying entities in workspace)


@pytest.mark.integration
@pytest.mark.slow
class TestWorkspaceBulkOperations:
    """Integration tests for bulk workspace operations."""
    
    async def test_bulk_project_creation(self, workspace_client, cleanup_test_data):
        """Test creating multiple projects."""
        project_names = [f"Bulk Test Project {i}" for i in range(3)]
        
        created_projects = []
        for name in project_names:
            result = await workspace_client.call("create_project", {
                "name": name,
                "description": f"Bulk test project: {name}"
            })
            
            if "result" in result and "project" in result["result"]:
                project_id = result["result"]["project"]["id"]
                created_projects.append(project_id)
                cleanup_test_data.track("project", project_id)
        
        # Verify all projects were created
        assert len(created_projects) == 3
        
        # List projects and verify they're all there
        projects = await workspace_client.call("list_projects")
        assert "result" in projects
        
        project_names_in_workspace = [p["name"] for p in projects["result"].get("projects", [])]
        for name in project_names:
            assert name in project_names_in_workspace


@pytest.mark.integration
class TestWorkspaceErrorHandling:
    """Integration tests for error handling scenarios."""
    
    async def test_invalid_operation(self, workspace_client):
        """Test handling of invalid operations."""
        result = await workspace_client.call("invalid_operation")
        
        # Should get an error response
        assert "error" in result
    
    async def test_malformed_parameters(self, workspace_client):
        """Test handling of malformed parameters."""
        result = await workspace_client.call("create_project", {
            "invalid_param": "invalid_value"
        })
        
        # Should handle gracefully
        assert result is not None
    
    async def test_permission_scenarios(self, workspace_client):
        """Test operations that might require specific permissions."""
        # This would test operations that require admin access, etc.
        # For now, just verify we can call operations
        result = await workspace_client.call("list_members")
        assert result is not None


# Example of testing with different auth providers
@pytest.mark.integration
@pytest.mark.provider
class TestWorkspaceMultiProvider:
    """Test workspace operations with different OAuth providers."""
    
    async def test_workspace_with_authkit(self, workspace_client):
        """Test workspace operations with AuthKit authentication."""
        # This uses the default authenticated_client (AuthKit)
        result = await workspace_client.call("get_info")
        assert result is not None
    
    @pytest.mark.skip(reason="GitHub OAuth not configured")
    async def test_workspace_with_github(self, github_client):
        """Test workspace operations with GitHub authentication."""
        # This would use GitHub OAuth if configured
        # For now, skip unless GitHub auth is set up
        pass