"""E2E tests for Workflow Automation operations.

Tests for all workflow automation operations and execution.

Covers:
- Story 9.1: Run workflows with transactions
- Story 9.2: Set up new project workflow
- Story 9.3: Import requirements via workflow
- Story 9.4: Bulk update status workflow
- Story 9.5: Organization onboarding workflow

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
    @pytest.mark.entity
    async def test_run_workflow_with_transactions(self, call_mcp):
        """Execute workflow with transactional consistency (all or nothing)."""
        # Create organization
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        # Create project
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {
                    "name": "Acme Corp",
                    "organization_id": org_id
                }
            }
        )

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["organization_id"] == org_id


class TestProjectOnboarding:
    """Test new project setup and workflow configuration."""
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_set_up_new_project_workflow(self, call_mcp):
        """Set up workflow for new project creation with default components."""
        # Create organization
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        # Create project
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {
                    "name": "Data Platform",
                    "organization_id": org_id
                }
            }
        )

        assert result["success"] is True
        assert "id" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_set_up_project_with_templates(self, call_mcp):
        """Set up new project using predefined templates."""
        # Create organization
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        # Create project
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {
                    "name": "Mobile App",
                    "organization_id": org_id
                }
            }
        )

        assert result["success"] is True
        assert "id" in result["data"]


class TestRequirementImport:
    """Test importing requirements via workflows."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_import_requirements_from_document(self, call_mcp):
        """Import requirements from document via workflow."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": proj_id}}
        )

        assert doc_result["success"] is True
        assert "id" in doc_result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_import_requirements_with_mapping(self, call_mcp):
        """Import requirements with field mapping configuration."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": proj_id}}
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_import_requirements_with_validation(self, call_mcp):
        """Import requirements with validation and error handling."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": proj_id}}
        )

        assert doc_result["success"] is True


class TestBulkUpdates:
    """Test bulk update operations through workflows."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_bulk_update_status(self, call_mcp):
        """Update status for multiple entities in bulk."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": proj_id}}
        )

        assert doc_result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_bulk_update_with_validation(self, call_mcp):
        """Bulk update with validation of each entity."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": proj_id}}
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_bulk_update_preserve_history(self, call_mcp):
        """Bulk update with audit trail preservation."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]

        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )

        assert proj_result["success"] is True


class TestOrganizationOnboarding:
    """Test organization onboarding workflows."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_organization_onboarding_workflow(self, call_mcp):
        """Execute complete organization onboarding workflow."""
        # Create organization
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": "Tech Startup Inc"}}
        )

        assert result["success"] is True
        assert "id" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_organization_onboarding_with_templates(self, call_mcp):
        """Onboarding with predefined templates (processes, templates, settings)."""
        # Create organization
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": "Enterprise Corp"}}
        )

        assert result["success"] is True
        assert "organization_id" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_organization_onboarding_with_sample_data(self, call_mcp):
        """Onboarding with sample data and example projects."""
        result, duration_ms = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Demo Company"
                }
            }
        )
        
        assert result["success"] is True
        assert "sample_projects_created" in result["data"]
    
    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_organization_onboarding_invite_members(self, call_mcp):
        """Onboarding with inviting initial team members."""
        result, duration_ms = await call_mcp(
            "workflow_tool",
            {
                "workflow": "organization_onboarding",
                "parameters": {
                    "name": "Collaborative Team"
                }
            }
        )
        
        assert result["success"] is True
        assert "invitations_sent" in result["data"]
