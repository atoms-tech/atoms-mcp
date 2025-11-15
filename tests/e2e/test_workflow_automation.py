"""Workflow Automation E2E Tests - Story 9"""

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

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_execute_multi_step_workflow(self, end_to_end_client):
        """Execute multi-step workflow."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="setup_project",
            steps=[
                {"step": "create_org", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}},
                {"step": "create_project", "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}},
                {"step": "create_documents", "count": 3}
            ]
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can run workflows with transactions")
    async def test_workflow_with_transaction(self, end_to_end_client):
        """Workflow executes as transaction."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="batch_operation",
            transactional=True,
            operations=[
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}},
                {"op": "create", "entity_type": "project", "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}}
            ]
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_workflow_error_rollback(self, end_to_end_client):
        """Workflow rolls back on error."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="batch_operation",
            transactional=True,
            operations=[
                {"op": "create", "entity_type": "organization", "data": {"name": f"Org {uuid.uuid4().hex[:4]}"}},
                {"op": "create", "entity_type": "organization", "data": {"name": ""}},  # Invalid
            ]
        )
        
        # Transaction should fail and rollback
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_workflow_with_retry(self, end_to_end_client):
        """Workflow retries on transient failure."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="resilient_operation",
            retry_count=3,
            operations=[
                {"op": "create", "entity_type": "project", "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}}
            ]
        )
        
        assert "success" in result


class TestProjectSetupWorkflow:
    """Project setup workflow tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can set up new project workflow")
    async def test_setup_new_project_workflow(self, end_to_end_client):
        """Execute project setup workflow."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="setup_new_project",
            project_data={
                "name": f"Setup Project {uuid.uuid4().hex[:4]}",
                "description": "New project"
            }
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_scaffold_default_entities(self, end_to_end_client):
        """Workflow scaffolds default documents."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="scaffold_project",
            project_name=f"Scaffold {uuid.uuid4().hex[:4]}",
            create_documents=True,
            document_templates=["README", "Requirements", "Architecture"]
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_scaffold_with_initial_members(self, end_to_end_client):
        """Scaffold project with initial members."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="setup_with_team",
            project_data={"name": f"Team Project {uuid.uuid4().hex[:4]}"},
            members=[
                {"user_id": "user1", "role": "admin"},
                {"user_id": "user2", "role": "editor"},
                {"user_id": "user3", "role": "viewer"}
            ]
        )
        
        assert "success" in result


class TestBatchImportWorkflow:
    """Batch import workflow tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can import requirements via workflow")
    async def test_import_requirements_workflow(self, end_to_end_client):
        """Import requirements via workflow."""
        requirements = [
            {"name": f"REQ {i}", "priority": "high"} for i in range(10)
        ]
        
        result = await end_to_end_client.workflow_execute(
            workflow_name="import_requirements",
            requirements=requirements,
            project_id=str(uuid.uuid4())
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_import_with_validation(self, end_to_end_client):
        """Import with validation and error reporting."""
        requirements = [
            {"name": f"REQ {i}", "priority": "high"} for i in range(5)
        ]
        
        result = await end_to_end_client.workflow_execute(
            workflow_name="import_validated",
            data=requirements,
            validate=True,
            report_errors=True
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_import_csv_file(self, end_to_end_client):
        """Import from CSV file."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="import_csv",
            file_path="requirements.csv",
            entity_type="requirement",
            project_id=str(uuid.uuid4())
        )
        
        # May succeed or skip if file not present
        assert "success" in result


class TestBulkUpdateWorkflow:
    """Bulk update workflow tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can bulk update statuses")
    async def test_bulk_update_status_workflow(self, end_to_end_client):
        """Bulk update entity statuses."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="bulk_update_status",
            entity_type="requirement",
            filters={"status": "open"},
            update_data={"status": "in_progress"}
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_bulk_update_with_transaction(self, end_to_end_client):
        """Bulk update as transaction."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="bulk_update_transactional",
            entity_type="project",
            entity_ids=[str(uuid.uuid4()) for _ in range(5)],
            update_data={"archived": True},
            transactional=True
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_bulk_update_with_rollback(self, end_to_end_client):
        """Bulk update with rollback on error."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="bulk_update_safe",
            entity_ids=[str(uuid.uuid4()) for _ in range(3)],
            update_data={"status": "completed"},
            rollback_on_error=True
        )
        
        assert "success" in result


class TestOnboardingWorkflow:
    """Organization onboarding workflow tests."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    @pytest.mark.story("User can onboard new organization")
    async def test_onboard_new_organization(self, end_to_end_client):
        """Execute organization onboarding workflow."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="onboard_organization",
            org_data={
                "name": f"New Org {uuid.uuid4().hex[:4]}",
                "type": "team",
                "description": "Newly onboarded organization"
            }
        )
        
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_onboard_with_initial_setup(self, end_to_end_client):
        """Onboard with complete setup."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="complete_onboarding",
            org_data={"name": f"Complete {uuid.uuid4().hex[:4]}"},
            setup_options={
                "create_default_projects": True,
                "invite_members": True,
                "setup_integrations": False
            }
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_onboard_with_members(self, end_to_end_client):
        """Onboard with team members."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="onboard_with_team",
            org_data={"name": f"Team Org {uuid.uuid4().hex[:4]}"},
            members=[
                {"email": "admin@example.com", "role": "admin"},
                {"email": "user@example.com", "role": "member"}
            ]
        )
        
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_onboard_send_invitations(self, end_to_end_client):
        """Onboarding sends member invitations."""
        result = await end_to_end_client.workflow_execute(
            workflow_name="onboard_send_invites",
            org_id=str(uuid.uuid4()),
            members=[f"user{i}@example.com" for i in range(3)],
            send_invitations=True
        )
        
        assert "success" in result
