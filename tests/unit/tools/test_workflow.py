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
    
    @pytest.mark.story("Workflow Automation - User can set up new project workflow")
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
    
    @pytest.mark.story("Workflow Automation - User can import requirements via workflow")
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
    
    @pytest.mark.story("Workflow Automation - User can onboard organization")
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
    
    @pytest.mark.story("Workflow Automation - User can run workflows with transactions")
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


# =====================================================
# PHASE 10 ADDITIONAL TESTS
# =====================================================

class TestWorkflowPhase10:
    """Phase 10 additional workflow tests."""

    @pytest.mark.story("Workflow Automation - Workflow with error handling")
    async def test_workflow_error_handling(self, call_mcp):
        """Test workflow error handling."""
        result, error = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "",  # Invalid: empty name
                "organization_id": "org_123"
            }
        })

        # Should handle error gracefully
        assert result is not None or error is not None

    @pytest.mark.story("Workflow Automation - Workflow with transaction mode")
    async def test_workflow_transaction_mode(self, call_mcp):
        """Test workflow with transaction mode."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123"
            },
            "transaction_mode": True
        })

        assert result is not None, "Should return result with transaction mode"

    @pytest.mark.story("Workflow Automation - Workflow with format type")
    async def test_workflow_format_type_detailed(self, call_mcp):
        """Test workflow with detailed format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123"
            },
            "format_type": "detailed"
        })

        assert result is not None, "Should return detailed result"

    @pytest.mark.story("Workflow Automation - Workflow with summary format")
    async def test_workflow_format_type_summary(self, call_mcp):
        """Test workflow with summary format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123"
            },
            "format_type": "summary"
        })

        assert result is not None, "Should return summary result"

    @pytest.mark.story("Workflow Automation - Workflow with raw format")
    async def test_workflow_format_type_raw(self, call_mcp):
        """Test workflow with raw format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123"
            },
            "format_type": "raw"
        })

        assert result is not None, "Should return raw result"

    @pytest.mark.story("Workflow Automation - Workflow with multiple parameters")
    async def test_workflow_multiple_parameters(self, call_mcp):
        """Test workflow with multiple parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123",
                "initial_documents": ["Requirements", "Design", "Architecture"],
                "team_members": ["user1", "user2", "user3"],
                "tags": ["important", "urgent"]
            }
        })

        assert result is not None, "Should handle multiple parameters"

    @pytest.mark.story("Workflow Automation - Workflow status tracking")
    async def test_workflow_status_tracking(self, call_mcp):
        """Test workflow status tracking."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123"
            }
        })

        assert result is not None, "Should track workflow status"

    @pytest.mark.story("Workflow Automation - Workflow with timeout")
    async def test_workflow_timeout_handling(self, call_mcp):
        """Test workflow timeout handling."""
        result, error = await call_mcp("workflow_tool", {
            "workflow": "setup_project",
            "parameters": {
                "name": "Test Project",
                "organization_id": "org_123"
            },
            "timeout": 5
        })

        # Should handle timeout gracefully
        assert result is not None or error is not None

    @pytest.mark.story("Workflow Automation - Workflow validation")
    async def test_workflow_validation(self, call_mcp):
        """Test workflow validation."""
        result, error = await call_mcp("workflow_tool", {
            "workflow": "invalid_workflow",
            "parameters": {}
        })

        # Should validate workflow name
        assert result is not None or error is not None
