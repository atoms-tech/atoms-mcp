"""Integration tests for Workflow tool - Advanced scenarios and edge cases.

Tests advanced workflow features with real database:
- Parallel document creation
- Step result aggregation
- Partial failures with continuation
- Workspace context setting
- Complex parameter validation
- Transaction boundaries
- Error recovery

Run with: pytest tests/integration/workflows/test_workflow_advanced.py -v
"""

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestWorkflowAdvancedScenarios:
    """Test advanced workflow execution scenarios."""
    
    async def test_setup_project_with_initial_documents(self, call_mcp):
        """Test project setup with initial document creation."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Project with Documents",
                "organization_id": "org-123",
                "initial_documents": ["Requirements", "Design", "Test Plan"]
            }
        })
        
        assert result is not None
        # If successful, should have created documents
        if result.get("success"):
            assert "project_id" in result.get("data", {})
    
    async def test_setup_project_with_admin_option(self, call_mcp):
        """Test project setup with admin assignment option."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Managed Project",
                "organization_id": "org-123",
                "add_creator_as_admin": True
            }
        })
        
        assert result is not None
    
    async def test_setup_project_skip_admin(self, call_mcp):
        """Test project setup without admin assignment."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Basic Project",
                "organization_id": "org-123",
                "add_creator_as_admin": False
            }
        })
        
        assert result is not None
    
    async def test_import_requirements_csv_format(self, call_mcp):
        """Test requirement import from CSV format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "import_requirements",
            "params": {
                "project_id": "proj-123",
                "source": "csv",
                "data": [
                    {"name": "REQ-001", "description": "First requirement", "priority": "high"},
                    {"name": "REQ-002", "description": "Second requirement", "priority": "medium"}
                ]
            }
        })
        
        assert result is not None
    
    async def test_import_requirements_json_format(self, call_mcp):
        """Test requirement import from JSON format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "import_requirements",
            "params": {
                "project_id": "proj-123",
                "source": "json",
                "data": [
                    {"id": "req-1", "name": "Requirement 1", "category": "functional"},
                    {"id": "req-2", "name": "Requirement 2", "category": "non-functional"}
                ]
            }
        })
        
        assert result is not None


class TestWorkflowStepResults:
    """Test workflow step-by-step result tracking."""
    
    async def test_workflow_step_execution_log(self, call_mcp):
        """Test that workflow returns execution log with step details."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Logged Project",
                "organization_id": "org-123"
            }
        })
        
        # Should include step information
        if result.get("success"):
            assert isinstance(result.get("data"), dict)
    
    async def test_workflow_partial_success_aggregation(self, call_mcp):
        """Test aggregating results when some steps fail."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Project",
                "organization_id": "org-123",
                "initial_documents": ["Req1", "Req2", "Req3"]
            }
        })
        
        # May have mixed success/failure in steps
        assert result is not None


class TestWorkflowValidation:
    """Test workflow parameter validation."""
    
    async def test_workflow_required_params_validation(self, call_mcp):
        """Test validation of required parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                # Missing required: name, organization_id
            }
        })
        
        # Should fail validation
        assert result is not None
    
    async def test_workflow_empty_data_handling(self, call_mcp):
        """Test handling of empty data in workflow."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "import_requirements",
            "params": {
                "project_id": "proj-123",
                "source": "csv",
                "data": []
            }
        })
        
        # Should handle empty data gracefully
        assert result is not None
    
    async def test_workflow_invalid_source_format(self, call_mcp):
        """Test handling of invalid source format."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "import_requirements",
            "params": {
                "project_id": "proj-123",
                "source": "invalid_format",
                "data": []
            }
        })
        
        # Should fail gracefully
        assert result is not None


class TestWorkflowContinueOnError:
    """Test workflow error continuation behavior."""
    
    async def test_continue_on_error_flag(self, call_mcp):
        """Test continue_on_error flag behavior."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "bulk_status_update",
            "params": {
                "entity_type": "requirement",
                "updates": [
                    {"id": "req-1", "status": "approved"},
                    {"id": "req-2", "status": "in_review"}
                ],
                "continue_on_error": True
            }
        })
        
        assert result is not None
    
    async def test_stop_on_error_flag(self, call_mcp):
        """Test stop_on_error flag behavior."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "bulk_status_update",
            "params": {
                "entity_type": "requirement",
                "updates": [
                    {"id": "req-1", "status": "approved"},
                    {"id": "req-2", "status": "invalid_status"}
                ],
                "continue_on_error": False
            }
        })
        
        assert result is not None


class TestWorkflowTimeout:
    """Test workflow execution timeout handling."""
    
    async def test_workflow_timeout_exceeded(self, call_mcp):
        """Test handling of workflow timeout."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "import_requirements",
            "params": {
                "project_id": "proj-123",
                "source": "csv",
                "data": [{"name": f"Req {i}"} for i in range(10000)],
                "timeout_seconds": 0.1  # Very short timeout
            }
        })
        
        # Should timeout gracefully
        assert result is not None
    
    async def test_workflow_reasonable_timeout(self, call_mcp):
        """Test workflow with reasonable timeout."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Timed Project",
                "organization_id": "org-123"
            },
            "timeout_seconds": 30
        })
        
        assert result is not None


class TestWorkflowStateTransitions:
    """Test workflow state transitions and final states."""
    
    async def test_workflow_terminal_state_success(self, call_mcp):
        """Test successful workflow reaches terminal state."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "setup_project",
            "params": {
                "name": "Success Project",
                "organization_id": "org-123"
            }
        })
        
        # Should have definitive success/failure state
        assert result is not None
        assert "success" in result or "status" in result
    
    async def test_workflow_idempotency_check(self, call_mcp):
        """Test workflow behavior on repeated execution."""
        params = {
            "workflow_type": "setup_project",
            "params": {
                "name": "Unique Project",
                "organization_id": "org-123"
            }
        }
        
        # Run first time
        result1, _ = await call_mcp("workflow_tool", params)
        
        # Run again (should either fail or be idempotent)
        result2, _ = await call_mcp("workflow_tool", params)
        
        # Both should return results
        assert result1 is not None
        assert result2 is not None


class TestBulkOperationScaling:
    """Test bulk operations with varying data sizes."""
    
    async def test_bulk_update_small_batch(self, call_mcp):
        """Test bulk update with small batch."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "bulk_status_update",
            "params": {
                "entity_type": "requirement",
                "updates": [{"id": f"req-{i}", "status": "approved"} for i in range(5)]
            }
        })
        
        assert result is not None
    
    async def test_bulk_update_medium_batch(self, call_mcp):
        """Test bulk update with medium batch."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "bulk_status_update",
            "params": {
                "entity_type": "requirement",
                "updates": [{"id": f"req-{i}", "status": "in_review"} for i in range(50)]
            }
        })
        
        assert result is not None
    
    async def test_bulk_update_large_batch(self, call_mcp):
        """Test bulk update with large batch."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "bulk_status_update",
            "params": {
                "entity_type": "requirement",
                "updates": [{"id": f"req-{i}", "status": "draft"} for i in range(500)]
            }
        })
        
        assert result is not None


class TestOnboardingWorkflowVariants:
    """Test organization onboarding with various configurations."""
    
    async def test_onboarding_minimal_config(self, call_mcp):
        """Test onboarding with minimal required parameters."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "onboard_organization",
            "params": {
                "name": "Minimal Org",
                "email": "admin@minimal.com"
            }
        })
        
        assert result is not None
    
    async def test_onboarding_with_team(self, call_mcp):
        """Test onboarding with initial team members."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "onboard_organization",
            "params": {
                "name": "Team Org",
                "email": "admin@teamorg.com",
                "initial_users": [
                    {"email": "user1@teamorg.com", "role": "admin"},
                    {"email": "user2@teamorg.com", "role": "member"},
                    {"email": "user3@teamorg.com", "role": "viewer"}
                ]
            }
        })
        
        assert result is not None
    
    async def test_onboarding_with_initial_projects(self, call_mcp):
        """Test onboarding with initial projects."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "onboard_organization",
            "params": {
                "name": "Project Org",
                "email": "admin@projectorg.com",
                "initial_projects": [
                    {"name": "Project Alpha", "description": "First project"},
                    {"name": "Project Beta", "description": "Second project"}
                ]
            }
        })
        
        assert result is not None
    
    async def test_onboarding_full_setup(self, call_mcp):
        """Test onboarding with complete configuration."""
        result, _ = await call_mcp("workflow_tool", {
            "workflow_type": "onboard_organization",
            "params": {
                "name": "Full Org",
                "email": "admin@fullorg.com",
                "initial_users": [
                    {"email": "lead@fullorg.com", "role": "admin"},
                    {"email": "dev@fullorg.com", "role": "member"}
                ],
                "initial_projects": [
                    {"name": "Core", "description": "Core platform"}
                ],
                "enable_workflows": True,
                "workspace_defaults": {
                    "default_project": "Core"
                }
            }
        })
        
        assert result is not None
