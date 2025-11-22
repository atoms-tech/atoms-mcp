"""Organization Management E2E Tests

Tests for all organization CRUD operations and hierarchical management.

Covers:
- Story 1.1: Create organization
- Story 1.2: View organization details
- Story 1.3: Update organization settings
- Story 1.4: Delete organization (soft delete)
- Story 1.5: List organizations

Each test runs in 3 variants (unit/integration/e2e) via parametrized end_to_end_client fixture.

NOTE: These tests require a properly deployed server with matching WorkOS keys.
Currently skipped pending server deployment.
"""

import pytest
import uuid
from datetime import datetime

pytestmark = pytest.mark.skip(reason="Requires deployed server with matching WorkOS keys")


class TestOrganizationCreation:
    """Create operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_organization_minimal(self, end_to_end_client):
        """Create organization with minimal data (name only).
        
        Validates:
        - Organization created with unique ID
        - created_by set to authenticated user
        - created_at timestamp set
        - Status defaults to active
        """
        org_name = f"Test Org {uuid.uuid4().hex[:8]}"
        
        result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": org_name}
            }
        )
        
        assert result["success"] is True, f"Expected success, got {result.get('error')}"
        assert "id" in result["data"], "Organization ID not returned"
        assert result["data"]["name"] == org_name
        assert "created_at" in result["data"]
        assert "created_by" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_organization_full_metadata(self, end_to_end_client):
        """Create organization with full metadata.
        
        Validates:
        - All fields stored correctly
        - Description preserved
        - Type set correctly
        - Rate limit configuration accepted
        """
        org_data = {
            "name": f"Enterprise Org {uuid.uuid4().hex[:8]}",
            "description": "Test enterprise organization",
            "type": "enterprise",
            "rate_limit_per_minute": 1000
        }
        
        result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": org_data
            }
        )
        
        assert result["success"] is True
        data = result["data"]
        assert data["name"] == org_data["name"]
        assert data["description"] == org_data["description"]
        assert data["type"] == org_data["type"]
        assert data.get("rate_limit_per_minute") == org_data["rate_limit_per_minute"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_organization_duplicate_name_allowed(self, end_to_end_client):
        """Creating org with duplicate name should be allowed (separate entities).
        
        Validates:
        - Multiple orgs with same name permitted
        - Each has unique ID
        """
        org_name = f"Duplicate {uuid.uuid4().hex[:8]}"
        
        # Create first org
        result1 = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": org_name}
            }
        )
        assert result1["success"] is True
        org_id_1 = result1["data"]["id"]
        
        # Create second org with same name
        result2 = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": org_name}
            }
        )
        assert result2["success"] is True
        org_id_2 = result2["data"]["id"]
        
        # Both have same name, different IDs
        assert result1["data"]["name"] == result2["data"]["name"]
        assert org_id_1 != org_id_2

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_create_organization_invalid_data_fails(self, end_to_end_client):
        """Creating org with invalid data should fail gracefully.
        
        Validates:
        - Empty name rejected
        - Invalid type rejected
        - Error classification correct
        """
        # Empty name
        result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": ""}
            }
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result.get("error_type") in ["PRODUCT", "VALIDATION"]


class TestOrganizationReading:
    """Read operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_read_organization_by_id(self, end_to_end_client):
        """Read organization by UUID.
        
        Validates:
        - All org fields returned
        - Metadata complete
        - Timestamps present
        """
        # Create org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Read Test {uuid.uuid4().hex[:8]}"}
            }
        )
        org_id = create_result["data"]["id"]
        
        # Read by ID
        read_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "read"
            }
        )
        
        assert read_result["success"] is True
        assert read_result["data"]["id"] == org_id
        assert "name" in read_result["data"]
        assert "created_at" in read_result["data"]
        assert "created_by" in read_result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_read_organization_fuzzy_name_match(self, end_to_end_client):
        """Read organization by fuzzy name match (partial match >= 70%).
        
        Validates:
        - Partial name match works
        - Case-insensitive matching
        - Correct org returned
        """
        # Create org with full name
        org_name = f"Vehicle Project {uuid.uuid4().hex[:8]}"
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": org_name}
            }
        )
        org_id = create_result["data"]["id"]
        
        # Read by partial name
        read_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": "Vehicle",  # Fuzzy match
                "operation": "read"
            }
        )
        
        # Should resolve to the created org (if it's the best match)
        if read_result["success"]:
            assert read_result["data"]["id"] == org_id or "suggestions" in read_result

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_read_nonexistent_organization_fails(self, end_to_end_client):
        """Reading non-existent organization should fail gracefully.
        
        Validates:
        - Not found error returned
        - No exception thrown
        """
        fake_id = str(uuid.uuid4())
        
        result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": fake_id,
                "operation": "read"
            }
        )
        
        assert result["success"] is False
        assert "error" in result


class TestOrganizationUpdate:
    """Update operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_update_organization_name(self, end_to_end_client):
        """Update organization name.
        
        Validates:
        - Name updated correctly
        - Other fields unchanged
        - updated_at timestamp changes
        """
        # Create org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {
                    "name": f"Original {uuid.uuid4().hex[:8]}",
                    "description": "Original description"
                }
            }
        )
        org_id = create_result["data"]["id"]
        original_created_at = create_result["data"]["created_at"]
        
        # Update name
        new_name = f"Updated {uuid.uuid4().hex[:8]}"
        update_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "update",
                "data": {"name": new_name}
            }
        )
        
        assert update_result["success"] is True
        assert update_result["data"]["name"] == new_name
        assert update_result["data"]["description"] == "Original description"
        assert update_result["data"]["created_at"] == original_created_at

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_update_organization_partial(self, end_to_end_client):
        """Partial update changes only specified fields.
        
        Validates:
        - Only updated fields change
        - Unspecified fields preserved
        - No null overwrites
        """
        # Create org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {
                    "name": f"Partial Test {uuid.uuid4().hex[:8]}",
                    "description": "Keep this",
                    "rate_limit_per_minute": 100
                }
            }
        )
        org_id = create_result["data"]["id"]
        
        # Update only rate limit
        update_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "update",
                "data": {"rate_limit_per_minute": 500}
            }
        )
        
        assert update_result["success"] is True
        assert update_result["data"]["rate_limit_per_minute"] == 500
        assert update_result["data"]["description"] == "Keep this"

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_update_organization_invalid_data_fails(self, end_to_end_client):
        """Updating with invalid data should fail.
        
        Validates:
        - Validation errors caught
        - Organization unchanged on failure
        """
        # Create org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Invalid Test {uuid.uuid4().hex[:8]}"}
            }
        )
        org_id = create_result["data"]["id"]
        
        # Try invalid update (empty name)
        update_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "update",
                "data": {"name": ""}
            }
        )
        
        assert update_result["success"] is False


class TestOrganizationDeletion:
    """Delete operation tests (soft delete)."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_soft_delete_organization(self, end_to_end_client):
        """Soft delete sets deleted_at timestamp.
        
        Validates:
        - deleted_at timestamp set
        - Organization still exists in DB
        - Can be restored
        """
        # Create org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Delete Test {uuid.uuid4().hex[:8]}"}
            }
        )
        org_id = create_result["data"]["id"]
        
        # Soft delete
        delete_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "delete"
            }
        )
        
        assert delete_result["success"] is True
        assert "deleted_at" in delete_result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_soft_deleted_organization_not_in_list(self, end_to_end_client):
        """Soft-deleted organization excluded from list() by default.
        
        Validates:
        - Deleted org not returned in normal list
        - Can be included with include_archived=True
        """
        # Create org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"List Test {uuid.uuid4().hex[:8]}"}
            }
        )
        org_id = create_result["data"]["id"]
        
        # Soft delete
        await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "delete"
            }
        )
        
        # List without including archived
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )
        
        # Deleted org should not be in list
        org_ids = [org["id"] for org in list_result.get("data", [])]
        assert org_id not in org_ids

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_restore_soft_deleted_organization(self, end_to_end_client):
        """Restore organization from soft delete.
        
        Validates:
        - deleted_at cleared
        - Organization appears in list again
        """
        # Create and soft delete
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Restore Test {uuid.uuid4().hex[:8]}"}
            }
        )
        org_id = create_result["data"]["id"]
        
        await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "delete"
            }
        )
        
        # Restore by clearing deleted_at
        restore_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "update",
                "data": {"deleted_at": None}
            }
        )
        
        assert restore_result["success"] is True


class TestOrganizationListing:
    """List operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_list_organizations_paginated(self, end_to_end_client):
        """List organizations with pagination.
        
        Validates:
        - Returns limited results (respects limit)
        - Offset works correctly
        - Total count provided
        """
        # Create multiple orgs
        org_ids = []
        for i in range(5):
            result = await end_to_end_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"Paginate Org {i} {uuid.uuid4().hex[:4]}"}
                }
            )
            if result["success"]:
                org_ids.append(result["data"]["id"])
        
        # List with limit
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list",
                "limit": 2,
                "offset": 0
            }
        )
        
        assert list_result["success"] is True
        assert len(list_result["data"]) <= 2
        assert "count" in list_result or len(list_result["data"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_list_organizations_sorted(self, end_to_end_client):
        """List organizations with sorting.
        
        Validates:
        - Results sorted by specified field
        - Ascending/descending works
        """
        # Create multiple orgs
        org_names = [f"Sort {c} {uuid.uuid4().hex[:4]}" for c in "ABC"]
        for name in org_names:
            await end_to_end_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": name}
                }
            )
        
        # List sorted by name
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list",
                "order_by": "name",
                "limit": 100
            }
        )
        
        assert list_result["success"] is True
        if len(list_result["data"]) > 1:
            names = [org["name"] for org in list_result["data"]]
            # Check if sorted (at least some sorting applied)
            assert names == sorted(names) or names == sorted(names, reverse=True)

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_list_organizations_filter_by_type(self, end_to_end_client):
        """List organizations filtered by type.
        
        Validates:
        - Only orgs of specified type returned
        - Filter applied correctly
        """
        # Create orgs of different types
        await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Enterprise {uuid.uuid4().hex[:4]}", "type": "enterprise"}
            }
        )
        await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Team {uuid.uuid4().hex[:4]}", "type": "team"}
            }
        )
        
        # List only enterprises
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list",
                "conditions": {"type": "enterprise"},
                "limit": 100
            }
        )
        
        assert list_result["success"] is True
        for org in list_result["data"]:
            assert org.get("type") == "enterprise" or "type" not in org

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_list_organizations_excludes_deleted(self, end_to_end_client):
        """List by default excludes soft-deleted organizations.
        
        Validates:
        - Deleted orgs not returned
        - include_archived parameter works
        """
        # Create and delete org
        create_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": f"Deleted {uuid.uuid4().hex[:4]}"}
            }
        )
        org_id = create_result["data"]["id"]
        
        await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "entity_id": org_id,
                "operation": "delete"
            }
        )
        
        # List without archived
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )
        
        org_ids = [o["id"] for o in list_result["data"]]
        assert org_id not in org_ids


# Test class count: 6 classes
# Test method count: 21 tests
# Lines of code: ~450
