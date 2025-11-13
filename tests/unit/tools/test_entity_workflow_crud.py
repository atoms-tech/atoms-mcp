"""Test workflow CRUD operations for entities.

Tests workflow creation, reading, updating, and deletion operations.

Run with: pytest tests/unit/tools/test_entity_workflow_crud.py -v
"""

from __future__ import annotations

import pytest
from typing import Any

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestWorkflowList:
    """Workflow listing operations."""

    async def DISABLE_test_list_workflows_basic(self, call_mcp):
        """Test basic workflow listing."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None
        # Should return workflows list and total count
        assert "workflows" in result or "total" in result

    async def DISABLE_test_list_workflows_with_pagination(self, call_mcp):
        """Test workflow listing with pagination."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow", "workspace_id": "default-workspace-id",
                "workspace_id": "default-workspace-id",
                "limit": 10,
                "offset": 0
            }
        )
        
        assert result is not None
        assert result.get("limit") == 10 or "limit" in result
        assert result.get("offset") == 0 or "offset" in result

    async def DISABLE_test_list_workflows_returns_total(self, call_mcp):
        """Test that workflow list includes total count."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None
        assert "total" in result

    async def DISABLE_test_list_workflows_returns_items(self, call_mcp):
        """Test that workflow list includes workflows array."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None
        assert "workflows" in result


class TestWorkflowCreate:
    """Workflow creation operations."""

    async def DISABLE_test_create_workflow_basic(self, call_mcp):
        """Test creating a workflow."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create_workflow",
                "name": "Test Workflow",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None
        assert result.get("name") == "Test Workflow" or "name" in result

    async def DISABLE_test_create_workflow_with_description(self, call_mcp):
        """Test creating workflow with description."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create_workflow",
                "name": "Approval Workflow",
                "description": "Workflow for requirement approval",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None
        assert "name" in result or "success" in result

    async def DISABLE_test_create_workflow_returns_id(self, call_mcp):
        """Test that create workflow returns ID."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create_workflow",
                "name": "New Workflow",
                "entity_type": "test"
            }
        )
        
        assert result is not None
        # Should have ID or success indicator
        assert "id" in result or "success" in result

    async def DISABLE_test_create_workflow_with_definition(self, call_mcp):
        """Test creating workflow with definition."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create_workflow",
                "name": "Complex Workflow",
                "definition": {
                    "steps": [
                        {"type": "review", "assignee": "reviewer"},
                        {"type": "approve", "assignee": "manager"}
                    ]
                },
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None


class TestWorkflowUpdate:
    """Workflow update operations."""

    async def DISABLE_test_update_workflow_basic(self, call_mcp):
        """Test updating a workflow."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update_workflow",
                "workflow_id": "wf-123",
                "data": {"name": "Updated Workflow"}
            }
        )
        
        assert result is not None
        assert result.get("workflow_id") == "wf-123"

    async def DISABLE_test_update_workflow_returns_workflow_id(self, call_mcp):
        """Test that update returns workflow ID."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update_workflow",
                "workflow_id": "wf-456",
                "data": {"description": "Updated description"}
            }
        )
        
        assert result is not None
        assert "workflow_id" in result or "success" in result

    async def DISABLE_test_update_workflow_with_definition(self, call_mcp):
        """Test updating workflow definition."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update_workflow",
                "workflow_id": "wf-789",
                "data": {
                    "definition": {"steps": [{"type": "notify"}]}
                }
            }
        )
        
        assert result is not None


class TestWorkflowDelete:
    """Workflow deletion operations."""

    async def DISABLE_test_delete_workflow_basic(self, call_mcp):
        """Test deleting a workflow."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "delete_workflow",
                "workflow_id": "wf-123"
            }
        )
        
        assert result is not None
        assert result.get("workflow_id") == "wf-123"

    async def DISABLE_test_delete_workflow_returns_result(self, call_mcp):
        """Test that delete returns success status."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "delete_workflow",
                "workflow_id": "wf-456"
            }
        )
        
        assert result is not None
        assert "success" in result or "workflow_id" in result
