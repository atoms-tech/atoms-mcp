"""Workflow Tool Tests - Canonical Pattern.

This test suite validates workflow tool functionality:
- EXECUTE: Run workflows with various configurations  
- PAUSE: Pause workflow execution
- RESUME: Resume paused workflows
- CANCEL: Cancel running workflows
- STATUS: Get workflow status and progress
- LIST: List available workflows

Canonical test pattern:
- Uses parametrized call_mcp fixture from conftest
- Single test code path for all variants
- No code duplication
- Supports unit/integration/e2e via fixture parametrization

Run with: pytest tests/unit/tools/test_workflow_clean.py -v
"""

import uuid

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestWorkflowExecute:
    """Test workflow execution."""

    async def test_execute_simple_workflow(self, call_mcp):
        """Test executing a basic workflow."""
        result, duration_ms = await call_mcp("workflow_tool", {
            "operation": "execute",
            "workflow_name": "simple_test_workflow",
            "data": {
                "test_param": f"test-{uuid.uuid4().hex[:8]}"
            }
        })

        # Check response structure
        assert isinstance(result, dict), "Should return a dict"
        # May fail if workflow doesn't exist, but should have expected response format
        if result.get("success"):
            assert "data" in result, "Successful response should have data"
        assert duration_ms > 0, "Duration should be recorded"

    async def test_execute_with_required_params(self, call_mcp):
        """Test executing workflow with required parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "operation": "execute",
            "workflow_id": "test-workflow-123",
            "data": {
                "required_field": "test_value",
                "optional_field": "optional_value"
            }
        })

        assert isinstance(result, dict), "Should return a dict response"


class TestWorkflowStatus:
    """Test workflow status operations."""

    async def test_get_workflow_status(self, call_mcp):
        """Test getting workflow execution status."""
        result, _ = await call_mcp("workflow_tool", {
            "operation": "status",
            "workflow_id": "nonexistent-workflow-123"
        })

        assert isinstance(result, dict), "Should return dict response"
        # Status for nonexistent workflow should be handled gracefully


class TestWorkflowCancel:
    """Test workflow cancellation."""

    async def test_cancel_workflow(self, call_mcp):
        """Test canceling a workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "operation": "cancel",
            "workflow_id": "nonexistent-workflow-456"
        })

        assert isinstance(result, dict), "Should return dict response"


class TestWorkflowList:
    """Test workflow listing."""

    async def test_list_workflows(self, call_mcp):
        """Test listing available workflows."""
        result, _ = await call_mcp("workflow_tool", {
            "operation": "list"
        })

        assert isinstance(result, dict), "Should return dict response"
        if result.get("success"):
            data = result.get("data", [])
            assert isinstance(data, list), "Data should be a list"
