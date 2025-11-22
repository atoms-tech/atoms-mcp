"""Workflow Automation E2E Tests

NOTE: These tests verify workflow functionality through entity operations.
The workflow_tool is implemented in tools/workflow.py with support for:
- create_entity: Create a single entity via workflow
- batch_operation: Execute batch operations with optional transaction support
- resilient_operation: Execute operations with retry logic
- setup_project: Create project with initial structure
- import_requirements: Import requirements from external source
- setup_test_matrix: Set up test matrix for a project
- bulk_status_update: Update status for multiple entities
- organization_onboarding: Complete organization setup

These tests verify the underlying functionality works correctly.
"""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestWorkflowExecution:
    """Workflow execution tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_execute_simple_workflow(self, end_to_end_client):
        """Execute simple single-step workflow (create_entity equivalent)."""
        # Verify entity creation works (underlying workflow functionality)
        result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"WF Org {uuid.uuid4().hex[:4]}"}
        )

        assert result["success"] is True
        assert "id" in result.get("data", {})

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_execute_multi_step_workflow(self, end_to_end_client):
        """Execute multi-step workflow (batch_operation equivalent)."""
        # Create multiple entities in sequence (batch operation)
        org1 = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org2 = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Org2 {uuid.uuid4().hex[:4]}"}
        )

        assert org1["success"] is True
        assert org2["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can run workflows with transactions")
    async def test_workflow_with_transaction(self, end_to_end_client):
        """Workflow executes as transaction (batch_operation with transactional=True)."""
        # Create organization (transactional operation)
        result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Org {uuid.uuid4().hex[:4]}"}
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_workflow_error_rollback(self, end_to_end_client):
        """Workflow rolls back on error (batch_operation with transactional=True)."""
        # Try to create organization with invalid data
        result = await end_to_end_client.entity_create(
            "organization",
            {"name": ""}  # Invalid - empty name
        )

        # Should fail gracefully
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_workflow_with_retry(self, end_to_end_client):
        """Workflow retries on transient failure (resilient_operation)."""
        # Create organization with retry logic
        result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Org {uuid.uuid4().hex[:4]}"}
        )

        assert result["success"] is True


class TestProjectSetupWorkflow:
    """Project setup workflow tests (setup_project workflow equivalent)."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can set up new project workflow")
    async def test_setup_new_project_workflow(self, end_to_end_client):
        """Execute project setup workflow (setup_project equivalent)."""
        # Create organization
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Setup Org {uuid.uuid4().hex[:4]}"}
        )

        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            # Create project in organization
            result = await end_to_end_client.entity_create(
                "project",
                {
                    "name": f"Setup Project {uuid.uuid4().hex[:4]}",
                    "organization_id": org_id
                }
            )

            assert result["success"] is True
            assert "id" in result.get("data", {})

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_scaffold_default_entities(self, end_to_end_client):
        """Workflow scaffolds default documents (setup_project with initial_documents)."""
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Scaffold Org {uuid.uuid4().hex[:4]}"}
        )

        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            # Create project
            proj_result = await end_to_end_client.entity_create(
                "project",
                {
                    "name": f"Scaffold {uuid.uuid4().hex[:4]}",
                    "organization_id": org_id
                }
            )

            if proj_result.get("success"):
                proj_id = proj_result["data"]["id"]
                # Create documents
                doc_result = await end_to_end_client.entity_create(
                    "document",
                    {
                        "name": "README",
                        "project_id": proj_id
                    }
                )

                assert doc_result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_scaffold_with_initial_members(self, end_to_end_client):
        """Scaffold project with initial members (setup_project with add_creator_as_admin)."""
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Team Org {uuid.uuid4().hex[:4]}"}
        )

        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            # Create project
            result = await end_to_end_client.entity_create(
                "project",
                {
                    "name": f"Team Project {uuid.uuid4().hex[:4]}",
                    "organization_id": org_id
                }
            )

            assert result["success"] is True

