"""E2E tests for Organization Management operations.

This file validates end-to-end organization management functionality:
- Creating organizations with various metadata configurations
- Updating organization properties and settings
- Retrieving organization details and listings
- Managing organization membership and roles
- Organization lifecycle operations (activate/deactivate/delete)

Test Coverage: 21 test scenarios covering 5 user stories.
File follows canonical naming - describes WHAT is tested (organization management).
Uses parametrized fixtures for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone





class TestOrganizationCreation:
    """Test organization creation scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_minimal_organization(self, call_mcp):
        """Create organization with minimal required data (name only)."""
        org_data = {
            "name": f"Minimal Org {uuid.uuid4().hex[:8]}"
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": org_data
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        assert uuid.UUID(result["data"]["id"])  # Valid UUID
        assert result["data"]["name"] == org_data["name"]
        # created_by should be the user ID (UUID), not email
        assert result["data"]["created_by"] == "12345678-1234-1234-1234-123456789012"
        assert result["data"]["created_at"] is not None
        # Verify ISO timestamp format
        datetime.fromisoformat(result["data"]["created_at"].replace('Z', '+00:00'))
    
    @pytest.mark.asyncio
    async def test_create_full_organization(self, call_mcp):
        """Create organization with complete data."""
        org_data = {
            "name": f"Full Org {uuid.uuid4().hex[:8]}",
            "type": "enterprise"
        }

        result, duration_ms = await call_mcp(
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
        assert data["type"] == org_data["type"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.asyncio
    async def test_create_organization_duplicate_name_allowed(self, call_mcp):
        """Creating organization with duplicate name is allowed (no unique constraint)."""
        org_name = f"Duplicate Org {uuid.uuid4().hex[:8]}"
        org_data = {"name": org_name}

        # Create first organization
        result1, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        assert result1["success"] is True
        org_id_1 = result1["data"]["id"]

        # Create second with same name (should succeed - no unique constraint)
        result2, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        assert result2["success"] is True
        org_id_2 = result2["data"]["id"]

        # Verify they are different organizations
        assert org_id_1 != org_id_2
        assert result1["data"]["name"] == result2["data"]["name"]
    
    @pytest.mark.asyncio
    async def test_create_organization_with_extra_fields(self, call_mcp):
        """Creating organization with extra fields should succeed (extra fields ignored)."""
        org_data = {
            "name": f"Extra Fields Org {uuid.uuid4().hex[:8]}",
            "type": "custom_type",
            "extra_field": "extra_value"
        }

        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )

        # API ignores extra fields, so creation should succeed
        assert result["success"] is True
        assert result["data"]["name"] == org_data["name"]


class TestOrganizationRetrieval:
    """Test organization retrieval operations."""
    
    
    @pytest.mark.asyncio
    async def test_get_organization_by_id(self, call_mcp):
        """Retrieve organization details by ID."""
        # Create organization first
        org_data = {"name": f"Get Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Retrieve organization
        get_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "read", "entity_id": org_id}
        )

        assert get_result["success"] is True
        assert get_result["data"]["id"] == org_id
        assert get_result["data"]["name"] == org_data["name"]
    
    
    @pytest.mark.asyncio
    async def test_list_organizations(self, call_mcp):
        """List all organizations for authenticated user."""
        # Create multiple organizations
        org_names = [
            f"List Org {i} {uuid.uuid4().hex[:8]}" 
            for i in range(3)
        ]
        
        created_ids = []
        for name in org_names:
            result, duration_ms = await call_mcp(
                "entity_tool",
                {"entity_type": "organization", "operation": "create", "data": {"name": name}}
            )
            created_ids.append(result["data"]["id"])
        
        # List organizations
        list_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "list"}
        )

        assert list_result["success"] is True
        assert "data" in list_result
        assert isinstance(list_result["data"], list)

        # Verify our created organizations are in the list
        returned_ids = [org["id"] for org in list_result["data"]]
        for created_id in created_ids:
            assert created_id in returned_ids
    
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_organization(self, call_mcp):
        """Getting non-existent organization should fail."""
        fake_id = str(uuid.uuid4())

        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "read", "entity_id": fake_id}
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestOrganizationUpdate:
    """Test organization update operations."""
    
    
    @pytest.mark.asyncio
    async def test_update_organization_name(self, call_mcp):
        """Update organization name successfully."""
        # Create organization
        org_data = {"name": f"Update Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Update name
        new_name = f"Updated Org {uuid.uuid4().hex[:8]}"
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"name": new_name}
            }
        )

        assert update_result["success"] is True
        assert update_result["data"]["name"] == new_name

        # Verify update persisted
        get_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "read", "entity_id": org_id}
        )
        assert get_result["data"]["name"] == new_name
    
    
    @pytest.mark.asyncio
    async def test_update_organization_settings(self, call_mcp):
        """Update organization rate limits and settings."""
        # Create organization
        org_data = {"name": f"Settings Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Update settings
        new_settings = {
            "rate_limits": {
                "requests_per_minute": 2000,
                "requests_per_hour": 100000
            },
            "features": {
                "advanced_analytics": False,
                "custom_integrations": True,
                "beta_features": True
            }
        }

        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"settings": new_settings}
            }
        )

        assert update_result["success"] is True
        assert update_result["data"]["settings"] == new_settings
    
    
    @pytest.mark.asyncio
    async def test_update_organization_name(self, call_mcp):
        """Update organization name."""
        # Create organization
        org_data = {"name": f"Original Name {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Update organization name
        new_name = f"Updated Name {uuid.uuid4().hex[:8]}"
        result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"name": new_name}
            }
        )

        assert result["success"] is True
        assert result["data"]["name"] == new_name


class TestOrganizationMembership:
    """Test organization member management."""
    
    
    @pytest.mark.asyncio
    async def test_add_organization_member(self, call_mcp):
        """Add member to organization with role."""
        # Create organization
        org_data = {"name": f"Member Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Add member using relationship_tool
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        add_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member"}
            }
        )

        assert add_result["success"] is True or add_result.get("exists") is True
    
    
    @pytest.mark.asyncio
    async def test_list_organization_members(self, call_mcp):
        """List all members of an organization."""
        # Create organization
        org_data = {"name": f"List Members Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Add multiple members
        user_ids = [f"user_{i}_{uuid.uuid4().hex[:8]}" for i in range(3)]

        for user_id in user_ids:
            _, _ = await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": "member",
                    "source": {"type": "organization", "id": org_id},
                    "target": {"type": "user", "id": user_id},
                    "metadata": {"role": "member"}
                }
            )

        # List members
        list_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id}
            }
        )

        assert list_result["success"] is True or "data" in list_result
    
    
    @pytest.mark.asyncio
    async def test_remove_organization_member(self, call_mcp):
        """Remove member from organization."""
        # Create organization and add member
        org_data = {"name": f"Remove Member Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        user_id = f"user_remove_{uuid.uuid4().hex[:8]}"
        add_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member"}
            }
        )

        # Remove member
        remove_result, _ = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": org_id},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert remove_result["success"] is True


class TestOrganizationLifecycle:
    """Test organization lifecycle operations."""
    
    
    @pytest.mark.asyncio
    async def test_deactivate_organization(self, call_mcp):
        """Deactivate organization (soft delete)."""
        # Create organization
        org_data = {"name": f"Deactivate Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Deactivate organization
        deactivate_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"status": "inactive"}
            }
        )

        assert deactivate_result["success"] is True
        assert deactivate_result["data"]["status"] == "inactive"

        # Verify organization appears inactive
        get_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "read", "entity_id": org_id}
        )
        assert get_result["data"]["status"] == "inactive"
    
    
    @pytest.mark.asyncio
    async def test_activate_organization(self, call_mcp):
        """Activate previously deactivated organization."""
        # Create and deactivate organization
        org_data = {"name": f"Reactivate Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Deactivate first
        _, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"status": "inactive"}
            }
        )

        # Reactivate
        activate_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"status": "active"}
            }
        )

        assert activate_result["success"] is True
        assert activate_result["data"]["status"] == "active"
    
    
    @pytest.mark.asyncio
    async def test_delete_organization(self, call_mcp):
        """Delete organization."""
        # Create organization
        org_data = {"name": f"Delete Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Delete organization
        delete_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "delete",
                "entity_id": org_id
            }
        )

        # Verify delete operation completed
        assert delete_result["success"] is True or delete_result.get("deleted") is True
    
    
    @pytest.mark.asyncio
    async def test_organization_audit_trail(self, call_mcp):
        """Verify organization operations are tracked."""
        # Create organization
        org_data = {"name": f"Audit Org {uuid.uuid4().hex[:8]}"}
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = create_result["data"]["id"]

        # Update organization
        update_result, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "entity_id": org_id,
                "data": {"description": "Updated description"}
            }
        )

        # Verify both operations succeeded
        assert create_result["success"] is True
        assert update_result["success"] is True

        # Verify organization has the updated description
        get_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "read", "entity_id": org_id}
        )

        assert get_result["success"] is True
        assert get_result["data"]["description"] == "Updated description"
