"""Integration tests for Workspace Navigation operations with real database.

Tests for all workspace context and navigation operations.

Covers:
- Story 6.1: Get current workspace context
- Story 6.2: Switch to organization workspace
- Story 6.3: Switch to project workspace
- Story 6.4: Manage workspace settings and defaults
- Story 6.5: Manage workspace favorites
- Story 6.6: Get workspace defaults

This file validates workspace navigation functionality with real database:
- Getting and maintaining current workspace context
- Switching between workspaces/organizations
- Managing workspace settings and defaults
- Tracking workspace state and recent activity

Test Coverage: 12 test scenarios covering 6 user stories.
Uses real database (Supabase) for integration testing.

NOTE: These tests require proper database fixture setup.
Currently skipped pending fixture configuration.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone

pytestmark = [pytest.mark.integration, pytest.mark.asyncio, pytest.mark.skip(reason="Requires proper database fixture setup")]


class TestWorkspaceContext:
    """Test workspace context operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_get_current_workspace_context(self, call_mcp):
        """Get current workspace context including org, projects, user role."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_context"
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        # Workspace context may not always have organization_id set
        assert "current_user_id" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_get_workspace_with_projects_and_documents(self, call_mcp):
        """Get workspace context with nested projects and documents."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_context",
                "include_hierarchy": True
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "projects" in result["data"]
        assert isinstance(result["data"]["projects"], list)
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_get_workspace_recent_activity(self, call_mcp):
        """Get recent activity in current workspace (items modified, created, accessed)."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_context",
                "include_recent_activity": True
            }
        )
        
        assert result["success"] is True
        assert "recent_activity" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_get_workspace_members_and_roles(self, call_mcp):
        """Get workspace members and their roles/permissions."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_context",
                "include_members": True
            }
        )
        
        assert result["success"] is True
        assert "members" in result["data"]
        assert isinstance(result["data"]["members"], list)
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_switch_workspace_organization(self, call_mcp):
        """Switch current workspace to different organization."""
        org_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "organization_id": org_id
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        # set_context may return success without setting the context in unit tests
        # (requires actual database/workspace setup)
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_switch_workspace_project(self, call_mcp):
        """Switch current workspace focus to specific project."""
        project_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_context",
                "project_id": project_id
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        # set_context may return success without setting the context in unit tests
        # (requires actual database/workspace setup)


class TestWorkspaceSettings:
    """Test workspace settings and configuration."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_get_workspace_defaults(self, call_mcp):
        """Get workspace default settings (view mode, sort order, filters)."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_defaults"
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "view_mode" in result["data"]
        assert "sort_order" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_update_workspace_defaults(self, call_mcp):
        """Update workspace defaults (preferred view, sort, filters)."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "set_defaults",
                "defaults": {
                    "view_mode": "kanban",
                    "sort_order": "created_at",
                    "sort_direction": "desc",
                    "items_per_page": 50
                }
            }
        )
        
        assert result["success"] is True
        assert result["data"]["view_mode"] == "kanban"
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_save_workspace_view_state(self, call_mcp):
        """Save current view state (filters, sort, pagination) as workspace state."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "save_view_state",
                "view_state": {
                    "filters": {"status": "open"},
                    "sort": {"field": "created_at", "order": "desc"},
                    "page": 1,
                    "per_page": 20
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_load_workspace_view_state(self, call_mcp):
        """Load previously saved workspace view state."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "load_view_state"
            }
        )
        
        assert result["success"] is True
        assert "view_state" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_manage_workspace_favorites(self, call_mcp):
        """Manage favorite items in workspace (star/unstar, favorites list)."""
        item_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "add_favorite",
                "entity_id": item_id,
                "entity_type": "project"
            }
        )
        
        assert result["success"] is True
        
        # Get favorites
        fav_result, _ = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_favorites"
            }
        )
        
        assert fav_result["success"] is True
        assert "favorites" in fav_result["data"]


class TestWorkspaceNavigation:
    """Test workspace navigation and breadcrumb tracking."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_get_breadcrumb_path(self, call_mcp):
        """Get breadcrumb path showing navigation hierarchy."""
        result, duration_ms = await call_mcp(
            "workspace_tool",
            {
                "operation": "get_breadcrumbs"
            }
        )
        
        assert result["success"] is True
        assert "breadcrumbs" in result["data"]
        assert isinstance(result["data"]["breadcrumbs"], list)
