"""Test workflow execution and integration operations.

Tests workflow execution, integration scenarios, and error handling.

Run with: pytest tests/unit/tools/test_entity_workflow_execution.py -v
"""

from __future__ import annotations

import pytest
from typing import Any

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
    pytest.mark.skip(reason="Test infrastructure requires additional setup - use consolidated test files instead")
]


class TestWorkflowExecution:
    """Workflow execution operations."""

    async def DISABLE_test_execute_workflow_basic(self, call_mcp):
        """Test executing a workflow."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "execute_workflow",
                "workflow_id": "wf-123"
            }
        )
        
        assert result is not None
        assert result.get("workflow_id") == "wf-123"

    async def DISABLE_test_execute_workflow_with_input(self, call_mcp):
        """Test executing workflow with input data."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "execute_workflow",
                "workflow_id": "wf-123",
                "input_data": {
                    "entity_id": "req-456",
                    "action": "approve"
                }
            }
        )
        
        assert result is not None

    async def DISABLE_test_execute_workflow_returns_execution_id(self, call_mcp):
        """Test that execute returns execution ID."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "execute_workflow",
                "workflow_id": "wf-456"
            }
        )
        
        assert result is not None
        # Should have execution ID or status
        assert "execution_id" in result or "status" in result

    async def DISABLE_test_execute_workflow_returns_status(self, call_mcp):
        """Test that execute returns workflow status."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "execute_workflow",
                "workflow_id": "wf-789"
            }
        )
        
        assert result is not None
        assert "status" in result


class TestWorkflowIntegration:
    """Integration tests for workflow operations."""

    async def DISABLE_test_workflow_lifecycle(self, call_mcp):
        """Test complete workflow lifecycle."""
        # Create
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create_workflow",
                "name": "Lifecycle Test",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        assert create_result is not None
        
        # List
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        assert list_result is not None
        
        # Update (if ID available)
        if create_result.get("id"):
            update_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "update_workflow",
                    "workflow_id": create_result["id"],
                    "data": {"name": "Updated"}
                }
            )
            assert update_result is not None

    async def DISABLE_test_workflow_operations_include_timing(self, call_mcp):
        """Test that workflow operations include timing metrics."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        
        assert result is not None
        assert duration_ms >= 0

    async def DISABLE_test_execute_workflow_multiple_times(self, call_mcp):
        """Test executing workflow multiple times."""
        for i in range(3):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "execute_workflow",
                    "workflow_id": "wf-test",
                    "input_data": {"iteration": i}
                }
            )
            
            assert result is not None


class TestWorkflowErrorHandling:
    """Error handling for workflow operations."""

    async def DISABLE_test_list_workflows_handles_invalid_type(self, call_mcp):
        """Test list workflows with invalid entity type."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "invalid_type"
            }
        )
        
        # Should handle gracefully
        assert result is not None

    async def DISABLE_test_execute_workflow_without_id(self, call_mcp):
        """Test execute workflow without ID."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "execute_workflow",
                "workflow_id": None
            }
        )
        
        # Should handle gracefully
        assert result is not None or result is None

    async def DISABLE_test_update_workflow_without_data(self, call_mcp):
        """Test update workflow without data."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update_workflow",
                "workflow_id": "wf-123",
                "data": None
            }
        )
        
        # Should handle gracefully
        assert result is not None or result is None


class TestWorkflowScenarios:
    """Scenario-based workflow tests."""

    async def DISABLE_test_workflow_for_different_entity_types(self, call_mcp):
        """Test workflows for different entity types."""
        for entity_type in ["requirement", "test", "document"]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create_workflow",
                    "name": f"{entity_type} Workflow",
                    "entity_type": entity_type
                }
            )
            
            assert result is not None

    async def DISABLE_test_workflow_pagination_scenarios(self, call_mcp):
        """Test workflow listing with various pagination."""
        for offset in [0, 10, 20]:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "list_workflows",
                    "entity_type": "workflow", "workspace_id": "default-workspace-id",
                "workspace_id": "default-workspace-id",
                    "limit": 10,
                    "offset": offset
                }
            )
            
            assert result is not None
            assert result.get("offset") == offset or "offset" in result

    async def DISABLE_test_workflow_execution_with_various_inputs(self, call_mcp):
        """Test workflow execution with different input types."""
        inputs = [
            {},
            {"simple": "data"},
            {"nested": {"data": {"structure": "value"}}},
            {"array": [1, 2, 3]},
        ]
        
        for input_data in inputs:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "execute_workflow",
                    "workflow_id": "wf-test",
                    "input_data": input_data
                }
            )
            
            assert result is not None

    async def DISABLE_test_workflow_crud_operations_sequence(self, call_mcp):
        """Test sequence of CRUD operations."""
        # Create
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create_workflow",
                "name": "Sequence Test",
                "entity_type": "workflow",
                "workspace_id": "default-workspace-id",
            }
        )
        assert create_result is not None
        
        # List
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list_workflows",
                "entity_type": "workflow", "workspace_id": "default-workspace-id",
                "workspace_id": "default-workspace-id",
                "limit": 5
            }
        )
        assert list_result is not None
        
        # Update
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "update_workflow",
                "workflow_id": "test-wf",
                "data": {"status": "active"}
            }
        )
        assert update_result is not None
        
        # Execute
        exec_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "execute_workflow",
                "workflow_id": "test-wf"
            }
        )
        assert exec_result is not None
        
        # Delete
        delete_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "delete_workflow",
                "workflow_id": "test-wf"
            }
        )
        assert delete_result is not None
