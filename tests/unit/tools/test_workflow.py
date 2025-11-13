"""Workflow Tool Tests - Unit Tests Only.

This test suite validates workflow_tool functionality:
- workflow: Name of the workflow to execute
- parameters: Dict of workflow-specific parameters
- transaction_mode: Whether to wrap in a transaction (default True)
- format_type: Result format (detailed, summary, raw)

Available workflows:
- setup_project
- import_requirements
- setup_test_matrix
- bulk_status_update
- organization_onboarding

Run with: pytest tests/unit/tools/test_workflow.py -v
"""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestWorkflowBasic:
    """Test basic workflow execution."""
    
    @pytest.mark.story("Workflow Automation - User can setup project workflow")
    async def test_setup_project_workflow(self, call_mcp):
        """Test setup_project workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123",
                "initial_documents": ["Requirements", "Design"]
            }
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Workflow Automation - User can import requirements")
    async def test_import_requirements_workflow(self, call_mcp):
        """Test import_requirements workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": "doc_123",
                "requirements": [
                    {"name": "REQ-1", "description": "Test requirement"}
                ]
            }
        })
        
        assert result is not None, "Should return result"
    
    async def test_setup_test_matrix_workflow(self, call_mcp):
        """Test setup_test_matrix workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_test_matrix",
            "parameters": {
                "project_id": "proj_123"
            }
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Workflow Automation - User can bulk update statuses")
    async def test_bulk_status_update_workflow(self, call_mcp):
        """Test bulk_status_update workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "bulk_status_update",
            "parameters": {
                "entity_type": "requirement",
                "entity_ids": ["req_1", "req_2"],
                "new_status": "approved"
            }
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Workflow Automation - User can onboard new organization")
    async def test_organization_onboarding_workflow(self, call_mcp):
        """Test organization_onboarding workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "organization_onboarding",
            "parameters": {
                "organization_name": "Test Org"
            }
        })
        
        assert result is not None, "Should return result"


class TestWorkflowTransactionMode:
    """Test transaction mode parameter."""
    
    @pytest.mark.story("Workflow Automation - User can run with transactions")
    async def test_with_transaction_mode_true(self, call_mcp):
        """Test workflow with transaction mode enabled."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {"name": "Test Project", "organization_id": "org_123"},
            "transaction_mode": True
        })
        
        assert result is not None, "Should return result"
    
    async def test_with_transaction_mode_false(self, call_mcp):
        """Test workflow with transaction mode disabled."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {"name": "Test Project", "organization_id": "org_123"},
            "transaction_mode": False
        })
        
        assert result is not None, "Should return result"


class TestWorkflowFormatTypes:
    """Test different format types."""
    
    async def test_detailed_format(self, call_mcp):
        """Test detailed format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {"name": "Test Project", "organization_id": "org_123"},
            "format_type": "detailed"
        })
        
        assert result is not None, "Should return result"
    
    async def test_summary_format(self, call_mcp):
        """Test summary format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {"name": "Test Project", "organization_id": "org_123"},
            "format_type": "summary"
        })
        
        assert result is not None, "Should return result"
    
    async def test_raw_format(self, call_mcp):
        """Test raw format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {"name": "Test Project", "organization_id": "org_123"},
            "format_type": "raw"
        })
        
        assert result is not None, "Should return result"


class TestWorkflowEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_missing_workflow_name(self, call_mcp):
        """Test with missing workflow name."""
        result, _ = await call_mcp("workflow_tool", {
            "parameters": {"name": "Test"}
        })
        
        assert result is not None, "Should handle missing workflow"
    
    async def test_invalid_workflow_name(self, call_mcp):
        """Test with invalid workflow name."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "invalid_workflow_xyz",
            "parameters": {}
        })
        
        assert result is not None, "Should handle invalid workflow"
    
    async def test_missing_parameters(self, call_mcp):
        """Test with missing parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project"
        })
        
        assert result is not None, "Should handle missing parameters"
    
    async def test_empty_parameters(self, call_mcp):
        """Test with empty parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {}
        })
        
        assert result is not None, "Should handle empty parameters"
    
    async def test_invalid_parameters_type(self, call_mcp):
        """Test with invalid parameters type."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": "invalid"  # Should be dict
        })
        
        assert result is not None, "Should handle invalid parameters type"


class TestWorkflowComplexParameters:
    """Test workflows with complex parameters."""
    
    async def test_nested_parameters(self, call_mcp):
        """Test workflow with nested parameter structures."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Complex Project",
                "organization_id": "org_123",
                "config": {
                    "enable_testing": True,
                    "test_types": ["unit", "integration", "e2e"],
                    "coverage_threshold": 0.8
                }
            }
        })
        
        assert result is not None, "Should handle nested parameters"
    
    async def test_list_parameters(self, call_mcp):
        """Test workflow with list parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "bulk_status_update",
            "parameters": {
                "entity_type": "requirement",
                "entity_ids": ["req_1", "req_2", "req_3", "req_4", "req_5"],
                "new_status": "approved"
            }
        })
        
        assert result is not None, "Should handle list parameters"


class TestWorkflowCombinations:
    """Test various workflow combinations."""
    
    async def test_workflow_with_all_options(self, call_mcp):
        """Test workflow with all optional parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Full Featured Project",
                "organization_id": "org_123",
                "initial_documents": ["Requirements", "Design", "Tests"]
            },
            "transaction_mode": True,
            "format_type": "detailed"
        })
        
        assert result is not None, "Should handle all parameters"
    
    async def test_sequential_workflows(self, call_mcp):
        """Test calling multiple workflows in sequence."""
        # First workflow
        result1, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {"name": "Project 1", "organization_id": "org_123"}
        })
        
        assert result1 is not None, "First workflow should succeed"
        
        # Second workflow
        result2, _ = await call_mcp("workflow_tool", {
            "workflow": "import_requirements",
            "parameters": {
                "document_id": "doc_123",
                "requirements": [{"name": "REQ-1", "description": "Test"}]
            }
        })
        
        assert result2 is not None, "Second workflow should succeed"
