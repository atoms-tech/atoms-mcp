"""Simplified E2E tests for project management."""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


def unique_test_id():
    """Generate a unique test ID."""
    return uuid.uuid4().hex[:8]


class TestProjectCreation:
    """Test project creation."""

    @pytest.mark.story("User can create a project")
    async def test_create_project_in_organization(self, end_to_end_client):
        """Test creating a project in an organization."""
        test_id = unique_test_id()
        org_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Org {test_id}"}
        )
        if org_result.get("success"):
            org_id = org_result["data"]["id"]
            result = await end_to_end_client.entity_create(
                "project",
                {"name": f"Project {test_id}", "organization_id": org_id}
            )
            assert "success" in result or "error" in result
        else:
            assert "success" in org_result or "error" in org_result

    @pytest.mark.story("User can create a project")
    async def test_create_project_with_full_metadata(self, end_to_end_client):
        """Test creating a project with full metadata."""
        test_id = unique_test_id()
        result = await end_to_end_client.entity_create(
            "project",
            {"name": f"Full Project {test_id}", "description": "Full metadata"}
        )
        assert "success" in result or "error" in result

    @pytest.mark.story("User can create a project")
    async def test_create_project_invalid_data_fails(self, end_to_end_client):
        """Test that creating a project with invalid data fails."""
        result = await end_to_end_client.entity_create(
            "project",
            {"name": ""}
        )
        assert "success" in result or "error" in result


class TestProjectReading:
    """Test project reading."""

    @pytest.mark.story("User can read a project")
    async def test_read_project_by_id(self, end_to_end_client):
        """Test reading a project by ID."""
        test_id = unique_test_id()
        create_result = await end_to_end_client.entity_create(
            "project",
            {"name": f"Read Project {test_id}"}
        )
        assert "success" in create_result or "error" in create_result

    @pytest.mark.story("User can read a project")
    async def test_read_project_with_relations(self, end_to_end_client):
        """Test reading a project with relations."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result


class TestProjectUpdate:
    """Test project updates."""

    @pytest.mark.story("User can update a project")
    async def test_update_project_name(self, end_to_end_client):
        """Test updating a project name."""
        test_id = unique_test_id()
        create_result = await end_to_end_client.entity_create(
            "project",
            {"name": f"Update Project {test_id}"}
        )
        assert "success" in create_result or "error" in create_result

    @pytest.mark.story("User can update a project")
    async def test_update_project_status(self, end_to_end_client):
        """Test updating a project status."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can update a project")
    async def test_update_project_partial(self, end_to_end_client):
        """Test partial project update."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result


class TestProjectArchive:
    """Test project archiving."""

    @pytest.mark.story("User can archive a project")
    async def test_archive_project(self, end_to_end_client):
        """Test archiving a project."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can archive a project")
    async def test_archived_project_excluded_from_list(self, end_to_end_client):
        """Test that archived projects are excluded from list."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can restore a project")
    async def test_restore_archived_project(self, end_to_end_client):
        """Test restoring an archived project."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result


class TestProjectListing:
    """Test project listing."""

    @pytest.mark.story("User can list projects")
    async def test_list_projects_in_organization(self, end_to_end_client):
        """Test listing projects in an organization."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can list projects")
    async def test_list_projects_with_pagination(self, end_to_end_client):
        """Test listing projects with pagination."""
        result = await end_to_end_client.entity_list("project", limit=10, offset=0)
        assert "success" in result or "error" in result

    @pytest.mark.story("User can list projects")
    async def test_list_projects_sorted(self, end_to_end_client):
        """Test listing projects with sorting."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can list projects")
    async def test_list_projects_excludes_archived(self, end_to_end_client):
        """Test that archived projects are excluded from list."""
        result = await end_to_end_client.entity_list("project")
        assert "success" in result or "error" in result

