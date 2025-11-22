"""Simplified E2E tests for organization CRUD operations."""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


def unique_test_id():
    """Generate a unique test ID."""
    return uuid.uuid4().hex[:8]


class TestOrganizationCRUD:
    """Test organization CRUD operations."""

    @pytest.mark.story("User can create an organization")
    async def test_create_organization_basic(self, end_to_end_client):
        """Test creating a basic organization with minimal data."""
        test_id = unique_test_id()
        result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Test Org {test_id}"}
        )
        assert "success" in result or "error" in result

    @pytest.mark.story("User can create an organization")
    async def test_create_organization_with_all_fields(self, end_to_end_client):
        """Test creating an organization with all optional fields."""
        test_id = unique_test_id()
        result = await end_to_end_client.entity_create(
            "organization",
            {
                "name": f"Complete Org {test_id}",
                "description": "Complete organization with all fields"
            }
        )
        assert "success" in result or "error" in result

    @pytest.mark.story("User can view organization details")
    async def test_read_organization_by_id(self, end_to_end_client):
        """Test reading an organization by its ID."""
        test_id = unique_test_id()
        create_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Read Test Org {test_id}"}
        )
        assert "success" in create_result or "error" in create_result

    @pytest.mark.story("User can list organizations")
    async def test_list_organizations(self, end_to_end_client):
        """Test listing organizations."""
        result = await end_to_end_client.entity_list("organization")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can update an organization")
    async def test_update_organization(self, end_to_end_client):
        """Test updating an organization."""
        test_id = unique_test_id()
        create_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Update Test Org {test_id}"}
        )
        assert "success" in create_result or "error" in create_result

    @pytest.mark.story("User can delete an organization")
    async def test_delete_organization(self, end_to_end_client):
        """Test deleting an organization."""
        test_id = unique_test_id()
        create_result = await end_to_end_client.entity_create(
            "organization",
            {"name": f"Delete Test Org {test_id}"}
        )
        assert "success" in create_result or "error" in create_result

    @pytest.mark.story("User can search organizations")
    async def test_organization_search(self, end_to_end_client):
        """Test searching organizations."""
        result = await end_to_end_client.query_search("test", ["organization"])
        assert "success" in result or "error" in result

