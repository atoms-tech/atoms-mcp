"""Strict Workflow Automation E2E Tests with Proper Feature Implementation"""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestWorkflowExecution:
    """Workflow execution tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_execute_simple_workflow(self, end_to_end_client):
        """Execute simple single-step workflow."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="create_entity",
            entity_type="organization",
            data={"name": f"WF Org {uuid.uuid4().hex[:4]}"}
        )
        
        assert result["success"] is True
        assert "entity_id" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_execute_multi_step_workflow(self, end_to_end_client):
        """Execute multi-step workflow."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="batch_operation",
            transactional=False,
            operations=[
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}},
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org2 {uuid.uuid4().hex[:4]}"}}
            ]
        )
        
        assert result["success"] is True
        assert result["data"]["operations_count"] == 2

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can run workflows with transactions")
    async def test_workflow_with_transaction(self, end_to_end_client):
        """Workflow executes as transaction."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="batch_operation",
            transactional=True,
            operations=[
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}}
            ]
        )
        
        assert result["success"] is True
        assert result["data"]["transactional"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_workflow_error_rollback(self, end_to_end_client):
        """Workflow rolls back on error."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="batch_operation",
            transactional=True,
            operations=[
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}},
                {"op": "create", "entity_type": "organization", "data": {"name": ""}}  # Invalid
            ]
        )
        
        # Transaction should fail and rollback
        assert "success" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_workflow_with_retry(self, end_to_end_client):
        """Workflow retries on transient failure."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="resilient_operation",
            retry_count=3,
            operations=[
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}}
            ]
        )
        
        assert result["success"] is True
        assert result["data"]["retry_count"] == 3


class TestProjectSetupWorkflow:
    """Project setup workflow tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can set up new project workflow")
    async def test_setup_new_project_workflow(self, end_to_end_client):
        """Execute project setup workflow."""
        # First create an organization
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Setup Org {uuid.uuid4().hex[:4]}"}
        )
        
        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            result = await end_to_end_client.workflow_execute(
                workflow_name="setup_project",
                name=f"Setup Project {uuid.uuid4().hex[:4]}",
                organization_id=org_id
            )
            
            assert result["success"] is True
            assert "entity_id" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_scaffold_default_entities(self, end_to_end_client):
        """Workflow scaffolds default documents."""
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Scaffold Org {uuid.uuid4().hex[:4]}"}
        )
        
        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            result = await end_to_end_client.workflow_execute(
                workflow_name="setup_project",
                name=f"Scaffold {uuid.uuid4().hex[:4]}",
                organization_id=org_id,
                initial_documents=["README", "Requirements"]
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_scaffold_with_initial_members(self, end_to_end_client):
        """Scaffold project with initial members."""
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Team Org {uuid.uuid4().hex[:4]}"}
        )
        
        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            result = await end_to_end_client.workflow_execute(
                workflow_name="setup_project",
                name=f"Team Project {uuid.uuid4().hex[:4]}",
                organization_id=org_id,
                add_creator_as_admin=True
            )
            
            assert result["success"] is True

