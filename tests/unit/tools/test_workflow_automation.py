"""E2E tests for Workflow Automation operations.

This file validates end-to-end workflow automation functionality:
- Running workflows with transactional consistency
- Setting up new project workflows and automation rules
- Importing data via workflows (requirements, test cases)
- Bulk update operations through workflows
- Organization onboarding workflows

Test Coverage: 13 test scenarios covering 5 user stories.
File follows canonical naming - describes WHAT is tested (workflow automation).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestWorkflowTransactions:
    """Test workflow execution with transactional consistency."""
    
    @pytest.mark.asyncio
    async def test_run_workflow_with_transactions(self, call_mcp):
        """Execute workflow with transactional consistency (all or nothing)."""
        org_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "create_organization_structure",
                "parameters": {
                    "organization_id": org_id,
                    "name": "Acme Corp",
                    "projects": [
                        {"name": "Project A", "description": "First project"},
                        {"name": "Project B", "description": "Second project"}
                    ]
                },
                "transaction_mode": True
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "organization_id" in result["data"]


class TestProjectOnboarding:
    """Test new project setup and workflow configuration."""
    
    @pytest.mark.asyncio
    async def test_set_up_new_project_workflow(self, call_mcp):
        """Set up workflow for new project creation with default components."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "setup_new_project",
                "parameters": {
                    "project_name": "Data Platform",
                    "organization_id": str(uuid.uuid4()),
                    "include_documents": True,
                    "include_requirements": True,
                    "include_test_framework": True
                }
            }
        )
        
        assert result["success"] is True
        assert "project_id" in result["data"]
    
    @pytest.mark.asyncio
    async def test_set_up_project_with_templates(self, call_mcp):
        """Set up new project using predefined templates."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "setup_new_project",
                "parameters": {
                    "project_name": "Mobile App",
                    "organization_id": str(uuid.uuid4()),
                    "template": "agile_development"
                }
            }
        )
        
        assert result["success"] is True
        assert "project_id" in result["data"]


class TestRequirementImport:
    """Test importing requirements via workflows."""
    
    @pytest.mark.asyncio
    async def test_import_requirements_from_document(self, call_mcp):
        """Import requirements from document via workflow."""
        doc_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "import_requirements",
                "parameters": {
                    "source_document_id": doc_id,
                    "target_project_id": str(uuid.uuid4()),
                    "import_mode": "create_new"
                }
            }
        )
        
        assert result["success"] is True
        assert "requirements_imported" in result["data"]
    
    @pytest.mark.asyncio
    async def test_import_requirements_with_mapping(self, call_mcp):
        """Import requirements with field mapping configuration."""
        doc_id = str(uuid.uuid4())
        
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "import_requirements",
                "parameters": {
                    "source_document_id": doc_id,
                    "target_project_id": str(uuid.uuid4()),
                    "field_mapping": {
                        "document_heading": "requirement_title",
                        "document_description": "requirement_description",
                        "acceptance_criteria": "test_cases"
                    }
                }
            }
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_import_requirements_with_validation(self, call_mcp):
        """Import requirements with validation and error handling."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "import_requirements",
                "parameters": {
                    "source_document_id": str(uuid.uuid4()),
                    "target_project_id": str(uuid.uuid4()),
                    "validate_on_import": True,
                    "skip_invalid": True
                }
            }
        )
        
        assert result["success"] is True
        assert "validation_results" in result["data"]


class TestBulkUpdates:
    """Test bulk update operations through workflows."""
    
    @pytest.mark.asyncio
    async def test_bulk_update_status(self, call_mcp):
        """Update status for multiple entities in bulk."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "bulk_update_status",
                "parameters": {
                    "entity_type": "requirement",
                    "filters": {"status": "draft"},
                    "new_status": "pending_review",
                    "update_reason": "Automated bulk status update"
                }
            }
        )
        
        assert result["success"] is True
        assert "updated_count" in result["data"]
    
    @pytest.mark.asyncio
    async def test_bulk_update_with_validation(self, call_mcp):
        """Bulk update with validation of each entity."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "bulk_update_status",
                "parameters": {
                    "entity_type": "test_case",
                    "filters": {"status": "pending"},
                    "new_status": "in_progress",
                    "validate_before_update": True
                }
            }
        )
        
        assert result["success"] is True
        assert "validation_results" in result["data"]
    
    @pytest.mark.asyncio
    async def test_bulk_update_preserve_history(self, call_mcp):
        """Bulk update with audit trail preservation."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "bulk_update_status",
                "parameters": {
                    "entity_type": "requirement",
                    "entities": [str(uuid.uuid4()) for _ in range(5)],
                    "new_status": "completed",
                    "track_changes": True
                }
            }
        )
        
        assert result["success"] is True
        assert "audit_trail" in result["data"]


class TestOrganizationOnboarding:
    """Test organization onboarding workflows."""
    
    @pytest.mark.asyncio
    async def test_organization_onboarding_workflow(self, call_mcp):
        """Execute complete organization onboarding workflow."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "organization_onboarding",
                "parameters": {
                    "organization_name": "Tech Startup Inc",
                    "admin_email": "admin@startup.com",
                    "team_size": 10,
                    "industry": "software"
                }
            }
        )
        
        assert result["success"] is True
        assert "organization_id" in result["data"]
        assert "workspace_initialized" in result["data"]
    
    @pytest.mark.asyncio
    async def test_organization_onboarding_with_templates(self, call_mcp):
        """Onboarding with predefined templates (processes, templates, settings)."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "organization_onboarding",
                "parameters": {
                    "organization_name": "Enterprise Corp",
                    "admin_email": "admin@enterprise.com",
                    "template": "enterprise_large_team"
                }
            }
        )
        
        assert result["success"] is True
        assert "organization_id" in result["data"]
    
    @pytest.mark.asyncio
    async def test_organization_onboarding_with_sample_data(self, call_mcp):
        """Onboarding with sample data and example projects."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "organization_onboarding",
                "parameters": {
                    "organization_name": "Demo Company",
                    "admin_email": "admin@demo.com",
                    "populate_sample_data": True,
                    "create_example_projects": 3
                }
            }
        )
        
        assert result["success"] is True
        assert "sample_projects_created" in result["data"]
    
    @pytest.mark.asyncio
    async def test_organization_onboarding_invite_members(self, call_mcp):
        """Onboarding with inviting initial team members."""
        result, duration_ms = await call_mcp(
            "workflow_execute",
            {
                "workflow_name": "organization_onboarding",
                "parameters": {
                    "organization_name": "Collaborative Team",
                    "admin_email": "admin@team.com",
                    "invite_members": [
                        {"email": "dev@team.com", "role": "developer"},
                        {"email": "pm@team.com", "role": "project_manager"},
                        {"email": "qa@team.com", "role": "qa_engineer"}
                    ]
                }
            }
        )
        
        assert result["success"] is True
        assert "invitations_sent" in result["data"]
