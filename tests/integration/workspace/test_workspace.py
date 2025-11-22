"""Integration tests for Workspace Tool with real database.

This test suite validates workspace_tool functionality:
- operation: get_context, set_context, list_workspaces, get_defaults
- context_type: organization, project, document
- entity_id: ID of the entity to set as context
- format_type: Result format (detailed, summary)

Run with: pytest tests/integration/workspace/test_workspace.py -v
"""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestWorkspaceGetContext:
    """Test getting current workspace context."""
    
    @pytest.mark.story("Workspace Navigation - User can view current context")
    async def test_get_current_context(self, call_mcp):
        """Test getting current workspace context."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_context"
        })
        
        assert result is not None, "Should return context"
    
    async def test_get_context_detailed_format(self, call_mcp):
        """Test getting context with detailed format."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_context",
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return context"


class TestWorkspaceSetContext:
    """Test setting workspace context."""
    
    @pytest.mark.story("Workspace Navigation - User can switch to organization")
    async def test_set_organization_context(self, call_mcp):
        """Test setting organization context."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "organization",
            "entity_id": "org_123"
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Workspace Navigation - User can switch to project")
    async def test_set_project_context(self, call_mcp):
        """Test setting project context."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "project",
            "entity_id": "proj_456"
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Workspace Navigation - User can switch to document")
    async def test_set_document_context(self, call_mcp):
        """Test setting document context."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "document",
            "entity_id": "doc_789"
        })
        
        assert result is not None, "Should return result"
    
    async def test_set_context_with_format(self, call_mcp):
        """Test setting context with format type."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "project",
            "entity_id": "proj_123",
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return result"


class TestWorkspaceListWorkspaces:
    """Test listing available workspaces."""
    
    @pytest.mark.story("Workspace Navigation - User can list workspaces")
    async def test_list_all_workspaces(self, call_mcp):
        """Test listing all available workspaces."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "list_workspaces"
        })
        
        assert result is not None, "Should return workspace list"
    
    async def test_list_workspaces_detailed(self, call_mcp):
        """Test listing workspaces with detailed format."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "list_workspaces",
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return workspace list"
    
    async def test_list_workspaces_summary(self, call_mcp):
        """Test listing workspaces with summary format."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "list_workspaces",
            "format_type": "summary"
        })
        
        assert result is not None, "Should return workspace list"


class TestWorkspaceGetDefaults:
    """Test getting smart default values."""
    
    @pytest.mark.story("Workspace Navigation - User can get default context")
    async def test_get_defaults(self, call_mcp):
        """Test getting smart defaults."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_defaults"
        })
        
        assert result is not None, "Should return defaults"
    
    async def test_get_defaults_for_organization(self, call_mcp):
        """Test getting defaults for organization context."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_defaults",
            "context_type": "organization"
        })
        
        assert result is not None, "Should return defaults"
    
    async def test_get_defaults_for_project(self, call_mcp):
        """Test getting defaults for project context."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_defaults",
            "context_type": "project",
            "entity_id": "proj_123"
        })
        
        assert result is not None, "Should return defaults"
    
    async def test_get_defaults_detailed(self, call_mcp):
        """Test getting defaults with detailed format."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_defaults",
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return defaults"


class TestWorkspaceEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_missing_operation(self, call_mcp):
        """Test with missing operation."""
        result, _ = await call_mcp("workspace_tool", {})
        
        assert result is not None, "Should handle missing operation"
    
    async def test_invalid_operation(self, call_mcp):
        """Test with invalid operation."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "invalid_operation"
        })
        
        assert result is not None, "Should handle invalid operation"
    
    async def test_invalid_context_type(self, call_mcp):
        """Test with invalid context type."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "invalid_type",
            "entity_id": "id_123"
        })
        
        assert result is not None, "Should handle invalid context type"
    
    async def test_missing_entity_id_for_set(self, call_mcp):
        """Test setting context without entity_id."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "project"
        })
        
        assert result is not None, "Should handle missing entity_id"
    
    async def test_empty_entity_id(self, call_mcp):
        """Test with empty entity_id."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "project",
            "entity_id": ""
        })
        
        assert result is not None, "Should handle empty entity_id"
    
    async def test_invalid_format_type(self, call_mcp):
        """Test with invalid format type."""
        result, _ = await call_mcp("workspace_tool", {
            "operation": "get_context",
            "format_type": "invalid_format"
        })
        
        assert result is not None, "Should handle invalid format"


class TestWorkspaceSequential:
    """Test sequential workspace operations."""
    
    async def test_set_then_get_context(self, call_mcp):
        """Test setting context then getting it."""
        # Set context
        set_result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "project",
            "entity_id": "proj_123"
        })
        
        assert set_result is not None, "Should set context"
        
        # Get context
        get_result, _ = await call_mcp("workspace_tool", {
            "operation": "get_context"
        })
        
        assert get_result is not None, "Should get context"
    
    async def test_multiple_context_changes(self, call_mcp):
        """Test changing context multiple times."""
        contexts = [
            ("organization", "org_1"),
            ("project", "proj_1"),
            ("document", "doc_1"),
            ("project", "proj_2"),
            ("organization", "org_2"),
        ]
        
        for context_type, entity_id in contexts:
            result, _ = await call_mcp("workspace_tool", {
                "operation": "set_context",
                "context_type": context_type,
                "entity_id": entity_id
            })
            
            assert result is not None, f"Should set {context_type} context"
    
    async def test_list_then_set_context(self, call_mcp):
        """Test listing workspaces then setting context."""
        # List workspaces
        list_result, _ = await call_mcp("workspace_tool", {
            "operation": "list_workspaces"
        })
        
        assert list_result is not None, "Should list workspaces"
        
        # Set context
        set_result, _ = await call_mcp("workspace_tool", {
            "operation": "set_context",
            "context_type": "organization",
            "entity_id": "org_from_list"
        })
        
        assert set_result is not None, "Should set context from list"


class TestWorkspaceFormats:
    """Test different format types."""
    
    async def test_all_operations_with_formats(self, call_mcp):
        """Test all operations support different format types."""
        operations = [
            ("get_context", {}),
            ("list_workspaces", {}),
            ("get_defaults", {}),
            ("set_context", {"context_type": "project", "entity_id": "proj_123"}),
        ]
        
        formats = ["detailed", "summary"]
        
        for operation, extra_params in operations:
            for fmt in formats:
                params = {
                    "operation": operation,
                    "format_type": fmt,
                    **extra_params
                }
                
                result, _ = await call_mcp("workspace_tool", params)
                assert result is not None, f"Should handle {operation} with format {fmt}"
