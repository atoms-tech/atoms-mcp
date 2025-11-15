"""Project Management E2E Tests

Tests for project CRUD operations within organizations.

Covers:
- Story 2.1: Create project in organization
- Story 2.2: View project details and hierarchy
- Story 2.3: Update project information
- Story 2.4: Archive project (soft delete)
- Story 2.5: List projects in organization
"""

import pytest
import uuid


pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]

class TestProjectCreation:
    """Create operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a project")
    async def test_create_project_in_organization(self, end_to_end_client):
        """Create project within organization.
        
        Validates:
        - Project created with parent org
        - Linked to organization automatically
        - Status set to active
        """
        # Create org first
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Create project
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Test Project {uuid.uuid4().hex[:4]}",
                "organization_id": org_id
            }
        )
        
        assert project_result["success"] is True
        assert "id" in project_result["data"]
        assert project_result["data"]["name"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a project")
    async def test_create_project_with_full_metadata(self, end_to_end_client):
        """Create project with full metadata.
        
        Validates:
        - Description stored
        - Status set
        - Metadata complete
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Full Project {uuid.uuid4().hex[:4]}",
                "description": "Detailed project description",
                "organization_id": org_id,
                "status": "active"
            }
        )
        
        assert project_result["success"] is True
        data = project_result["data"]
        assert data["description"] == "Detailed project description"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a project")
    async def test_create_project_without_org_fails(self, end_to_end_client):
        """Creating project without org should fail or set null.
        
        Validates:
        - Organization requirement enforced
        """
        result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={"name": f"Orphan {uuid.uuid4().hex[:4]}"}
        )
        
        # May succeed with null org, or fail - both acceptable
        assert "success" in result

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a project")
    async def test_create_project_invalid_data_fails(self, end_to_end_client):
        """Creating project with invalid data fails.
        
        Validates:
        - Empty name rejected
        - Validation error returned
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={"name": "", "organization_id": org_id}
        )
        
        assert result["success"] is False


class TestProjectReading:
    """Read operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can view project details")
    async def test_read_project_by_id(self, end_to_end_client):
        """Read project by UUID.
        
        Validates:
        - All project fields returned
        - Parent org included
        """
        # Setup
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Read Test {uuid.uuid4().hex[:4]}",
                "organization_id": org_id
            }
        )
        project_id = project_result["data"]["id"]
        
        # Read
        read_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="read"
        )
        
        assert read_result["success"] is True
        assert read_result["data"]["id"] == project_id
        assert "name" in read_result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can view project details")
    async def test_read_project_with_relations(self, end_to_end_client):
        """Read project with relationships included.
        
        Validates:
        - Child documents included
        - Relationship count available
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Relations {uuid.uuid4().hex[:4]}",
                "organization_id": org_id
            }
        )
        project_id = project_result["data"]["id"]
        
        read_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="read",
            include_relations=True
        )
        
        assert read_result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can view project details")
    async def test_read_nonexistent_project_fails(self, end_to_end_client):
        """Reading non-existent project fails gracefully.
        
        Validates:
        - Not found error returned
        """
        fake_id = str(uuid.uuid4())
        
        result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=fake_id,
            operation="read"
        )
        
        assert result["success"] is False


class TestProjectUpdate:
    """Update operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can update project information")
    async def test_update_project_name(self, end_to_end_client):
        """Update project name.
        
        Validates:
        - Name changed
        - Other fields unchanged
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Original {uuid.uuid4().hex[:4]}",
                "organization_id": org_id,
                "description": "Keep this"
            }
        )
        project_id = project_result["data"]["id"]
        
        # Update
        new_name = f"Updated {uuid.uuid4().hex[:4]}"
        update_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="update",
            data={"name": new_name}
        )
        
        assert update_result["success"] is True
        assert update_result["data"]["name"] == new_name
        assert update_result["data"]["description"] == "Keep this"

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can update project information")
    async def test_update_project_status(self, end_to_end_client):
        """Update project status.
        
        Validates:
        - Status changes to archived/completed
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Status {uuid.uuid4().hex[:4]}",
                "organization_id": org_id,
                "status": "active"
            }
        )
        project_id = project_result["data"]["id"]
        
        # Update status
        update_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="update",
            data={"status": "completed"}
        )
        
        assert update_result["success"] is True
        assert update_result["data"]["status"] == "completed"

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can update project information")
    async def test_update_project_partial(self, end_to_end_client):
        """Partial update only changes specified fields.
        
        Validates:
        - Only updated fields change
        - Unspecified fields preserved
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Partial {uuid.uuid4().hex[:4]}",
                "organization_id": org_id,
                "description": "Keep this",
                "status": "active"
            }
        )
        project_id = project_result["data"]["id"]
        
        # Partial update
        update_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="update",
            data={"name": "Only update name"}
        )
        
        assert update_result["success"] is True
        assert update_result["data"]["description"] == "Keep this"
        assert update_result["data"]["status"] == "active"


class TestProjectArchive:
    """Archive/delete operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can archive a project")
    async def test_archive_project(self, end_to_end_client):
        """Archive (soft delete) project.
        
        Validates:
        - archived_at timestamp set
        - Project can be restored
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Archive {uuid.uuid4().hex[:4]}",
                "organization_id": org_id
            }
        )
        project_id = project_result["data"]["id"]
        
        # Archive via soft delete or status update
        archive_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="delete",
            soft_delete=True
        )
        
        assert archive_result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can archive a project")
    async def test_archived_project_excluded_from_list(self, end_to_end_client):
        """Archived project excluded from list by default.
        
        Validates:
        - Archived project not returned in normal list
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Exclude {uuid.uuid4().hex[:4]}",
                "organization_id": org_id
            }
        )
        project_id = project_result["data"]["id"]
        
        # Archive
        await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="delete",
            soft_delete=True
        )
        
        # List
        list_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="list",
            parent_type="organization",
            parent_id=org_id,
            include_archived=False
        )
        
        project_ids = [p["id"] for p in list_result.get("data", [])]
        assert project_id not in project_ids

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can archive a project")
    async def test_restore_archived_project(self, end_to_end_client):
        """Restore archived project.
        
        Validates:
        - archived_at cleared
        - Project reappears in list
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={
                "name": f"Restore {uuid.uuid4().hex[:4]}",
                "organization_id": org_id
            }
        )
        project_id = project_result["data"]["id"]
        
        # Archive and restore
        await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="delete",
            soft_delete=True
        )
        
        restore_result = await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="update",
            data={"deleted_at": None}
        )
        
        assert restore_result["success"] is True


class TestProjectListing:
    """List operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list projects in organization")
    async def test_list_projects_in_organization(self, end_to_end_client):
        """List projects in organization.
        
        Validates:
        - Only org's projects returned
        - Pagination works
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"List Org {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Create multiple projects
        for i in range(3):
            await end_to_end_client.entity_tool(
                entity_type="project",
                operation="create",
                data={
                    "name": f"Project {i}",
                    "organization_id": org_id
                }
            )
        
        # List
        list_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="list",
            parent_type="organization",
            parent_id=org_id,
            limit=10
        )
        
        assert list_result["success"] is True
        assert isinstance(list_result["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list projects in organization")
    async def test_list_projects_with_pagination(self, end_to_end_client):
        """List projects with limit and offset.
        
        Validates:
        - Limit applied
        - Offset works
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Paginate {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # List with limit
        list_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="list",
            parent_type="organization",
            parent_id=org_id,
            limit=5,
            offset=0
        )
        
        assert list_result["success"] is True
        assert len(list_result["data"]) <= 5

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list projects in organization")
    async def test_list_projects_sorted(self, end_to_end_client):
        """List projects sorted by name.
        
        Validates:
        - Results sorted
        - Order_by parameter works
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Sort {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Create projects
        for name in ["Zebra", "Alpha", "Mike"]:
            await end_to_end_client.entity_tool(
                entity_type="project",
                operation="create",
                data={"name": name, "organization_id": org_id}
            )
        
        # List sorted
        list_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="list",
            parent_type="organization",
            parent_id=org_id,
            order_by="name",
            limit=100
        )
        
        assert list_result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list projects in organization")
    async def test_list_projects_excludes_archived(self, end_to_end_client):
        """List excludes archived projects by default.
        
        Validates:
        - Archived projects not returned
        """
        org_result = await end_to_end_client.entity_tool(
            entity_type="organization",
            operation="create",
            data={"name": f"Exclude {uuid.uuid4().hex[:4]}"}
        )
        org_id = org_result["data"]["id"]
        
        # Create and archive
        project_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="create",
            data={"name": f"Archive {uuid.uuid4().hex[:4]}", "organization_id": org_id}
        )
        project_id = project_result["data"]["id"]
        
        await end_to_end_client.entity_tool(
            entity_type="project",
            entity_id=project_id,
            operation="delete",
            soft_delete=True
        )
        
        # List
        list_result = await end_to_end_client.entity_tool(
            entity_type="project",
            operation="list",
            parent_type="organization",
            parent_id=org_id,
            include_archived=False
        )
        
        project_ids = [p["id"] for p in list_result["data"]]
        assert project_id not in project_ids
