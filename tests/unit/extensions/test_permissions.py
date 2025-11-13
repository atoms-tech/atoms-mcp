"""Tests for permission enforcement on all operations."""

import pytest
from infrastructure.permission_manager import PermissionManager
from infrastructure.advanced_features_adapter import AdvancedFeaturesAdapter
from infrastructure.mock_adapters import InMemoryDatabaseAdapter


class TestPermissionLevels:
    """Test permission level hierarchy."""

    def test_permission_level_hierarchy(self):
        """Test permission level values."""
        assert PermissionManager.PERMISSION_LEVELS["view"] == 1
        assert PermissionManager.PERMISSION_LEVELS["edit"] == 2
        assert PermissionManager.PERMISSION_LEVELS["admin"] == 3

    def test_operation_permission_mapping(self):
        """Test operations mapped to permission levels."""
        # Read operations require view
        assert PermissionManager.OPERATION_PERMISSIONS["read"] == "view"
        assert PermissionManager.OPERATION_PERMISSIONS["search"] == "view"
        assert PermissionManager.OPERATION_PERMISSIONS["list"] == "view"

        # Write operations require edit
        assert PermissionManager.OPERATION_PERMISSIONS["create"] == "edit"
        assert PermissionManager.OPERATION_PERMISSIONS["update"] == "edit"

        # Delete operations require admin
        assert PermissionManager.OPERATION_PERMISSIONS["delete"] == "admin"
        assert PermissionManager.OPERATION_PERMISSIONS["archive"] == "admin"


class TestPermissionChecks:
    """Test permission checking logic."""

    @pytest.fixture
    def db(self):
        """Create in-memory database."""
        return InMemoryDatabaseAdapter()

    @pytest.fixture
    def permission_manager(self, db):
        """Create permission manager."""
        adapter = AdvancedFeaturesAdapter(db)
        return PermissionManager(db, adapter)

    @pytest.mark.asyncio
    async def test_user_with_view_permission_can_read(self, permission_manager, db):
        """Test user with view permission can read."""
        # Setup: grant view permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "view",
                "expires_at": None,
            }]}
        )()

        # Check: can read
        allowed = await permission_manager.check_permission(
            "user-1", "requirement", "req-123", "read"
        )
        assert allowed is True

    @pytest.mark.asyncio
    async def test_user_with_view_permission_cannot_update(self, permission_manager, db):
        """Test user with view permission cannot update."""
        # Setup: grant view permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "view",
                "expires_at": None,
            }]}
        )()

        # Check: cannot update
        allowed = await permission_manager.check_permission(
            "user-1", "requirement", "req-123", "update"
        )
        assert allowed is False

    @pytest.mark.asyncio
    async def test_user_with_edit_permission_cannot_delete(self, permission_manager, db):
        """Test user with edit permission cannot delete."""
        # Setup: grant edit permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "edit",
                "expires_at": None,
            }]}
        )()

        # Check: cannot delete
        allowed = await permission_manager.check_permission(
            "user-1", "requirement", "req-123", "delete"
        )
        assert allowed is False

    @pytest.mark.asyncio
    async def test_user_with_admin_permission_can_delete(self, permission_manager, db):
        """Test user with admin permission can delete."""
        # Setup: grant admin permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "admin",
                "expires_at": None,
            }]}
        )()

        # Check: can delete
        allowed = await permission_manager.check_permission(
            "user-1", "requirement", "req-123", "delete"
        )
        assert allowed is True

    @pytest.mark.asyncio
    async def test_user_without_permission_denied(self, permission_manager, db):
        """Test user without permission is denied."""
        # Setup: no permission
        db._tables["entity_permissions"] = type("Table", (), {"rows": []})()

        # Check: denied
        allowed = await permission_manager.check_permission(
            "user-1", "requirement", "req-123", "read"
        )
        assert allowed is False

    @pytest.mark.asyncio
    async def test_expired_permission_rejected(self, permission_manager, db):
        """Test expired permission is rejected."""
        # Setup: expired permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "edit",
                "expires_at": "2020-01-01T00:00:00",  # In past
            }]}
        )()

        # Check: rejected
        allowed = await permission_manager.check_permission(
            "user-1", "requirement", "req-123", "update"
        )
        assert allowed is False


class TestPermissionEnforcement:
    """Test permission enforcement (raises errors)."""

    @pytest.fixture
    def db(self):
        """Create in-memory database."""
        return InMemoryDatabaseAdapter()

    @pytest.fixture
    def permission_manager(self, db):
        """Create permission manager."""
        adapter = AdvancedFeaturesAdapter(db)
        return PermissionManager(db, adapter)

    @pytest.mark.asyncio
    async def test_enforce_permission_allowed(self, permission_manager, db):
        """Test enforce_permission succeeds when allowed."""
        # Setup: grant permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "edit",
                "expires_at": None,
            }]}
        )()

        # Should not raise
        await permission_manager.enforce_permission(
            "user-1", "requirement", "req-123", "update"
        )

    @pytest.mark.asyncio
    async def test_enforce_permission_denied(self, permission_manager, db):
        """Test enforce_permission raises when denied."""
        # Setup: no permission
        db._tables["entity_permissions"] = type("Table", (), {"rows": []})()

        # Should raise
        with pytest.raises(PermissionError):
            await permission_manager.enforce_permission(
                "user-1", "requirement", "req-123", "delete"
            )


class TestPermissionGranting:
    """Test granting and revoking permissions."""

    @pytest.fixture
    def db(self):
        """Create in-memory database."""
        return InMemoryDatabaseAdapter()

    @pytest.fixture
    def permission_manager(self, db):
        """Create permission manager."""
        adapter = AdvancedFeaturesAdapter(db)
        return PermissionManager(db, adapter)

    @pytest.mark.asyncio
    async def test_grant_permission(self, permission_manager):
        """Test granting permission."""
        # Should not raise
        perm = await permission_manager.grant_permission(
            user_id="user-1",
            entity_type="requirement",
            entity_id="req-123",
            workspace_id="ws-1",
            permission_level="edit",
        )
        assert perm is not None

    @pytest.mark.asyncio
    async def test_grant_invalid_permission_level(self, permission_manager):
        """Test granting invalid permission level."""
        with pytest.raises(ValueError):
            await permission_manager.grant_permission(
                user_id="user-1",
                entity_type="requirement",
                entity_id="req-123",
                workspace_id="ws-1",
                permission_level="invalid",
            )

    @pytest.mark.asyncio
    async def test_revoke_permission(self, permission_manager, db):
        """Test revoking permission."""
        # Setup: grant permission
        db._tables["entity_permissions"] = type(
            "Table", (), {"rows": [{
                "id": "perm-1",
                "user_id": "user-1",
                "entity_type": "requirement",
                "entity_id": "req-123",
                "permission_level": "edit",
                "expires_at": None,
            }]}
        )()

        # Revoke
        result = await permission_manager.revoke_permission(
            "user-1", "requirement", "req-123"
        )
        assert result is True


class TestBulkOperationPermissions:
    """Test permissions on bulk operations."""

    @pytest.fixture
    def db(self):
        """Create in-memory database."""
        return InMemoryDatabaseAdapter()

    @pytest.fixture
    def permission_manager(self, db):
        """Create permission manager."""
        adapter = AdvancedFeaturesAdapter(db)
        return PermissionManager(db, adapter)

    @pytest.mark.asyncio
    async def test_bulk_update_requires_edit(self, permission_manager):
        """Test bulk_update requires edit permission."""
        required = PermissionManager.OPERATION_PERMISSIONS["bulk_update"]
        assert required == "edit"

    @pytest.mark.asyncio
    async def test_bulk_delete_requires_admin(self, permission_manager):
        """Test bulk_delete requires admin permission."""
        required = PermissionManager.OPERATION_PERMISSIONS["bulk_delete"]
        assert required == "admin"


class TestWorkflowPermissions:
    """Test permissions on workflow operations."""

    def test_list_workflows_requires_view(self):
        """Test list_workflows requires view."""
        required = PermissionManager.OPERATION_PERMISSIONS["list_workflows"]
        assert required == "view"

    def test_create_workflow_requires_edit(self):
        """Test create_workflow requires edit."""
        required = PermissionManager.OPERATION_PERMISSIONS["create_workflow"]
        assert required == "edit"

    def test_delete_workflow_requires_admin(self):
        """Test delete_workflow requires admin."""
        required = PermissionManager.OPERATION_PERMISSIONS["delete_workflow"]
        assert required == "admin"


class TestAdvancedFeaturePermissions:
    """Test permissions on advanced features."""

    def test_export_requires_view(self):
        """Test export requires view permission."""
        required = PermissionManager.OPERATION_PERMISSIONS.get("export", "view")
        assert required == "view"

    def test_import_requires_edit(self):
        """Test import requires edit permission."""
        required = PermissionManager.OPERATION_PERMISSIONS["import"]
        assert required == "edit"

    def test_get_permissions_requires_view(self):
        """Test get_permissions requires view."""
        required = PermissionManager.OPERATION_PERMISSIONS["get_permissions"]
        assert required == "view"

    def test_update_permissions_requires_admin(self):
        """Test update_permissions requires admin."""
        required = PermissionManager.OPERATION_PERMISSIONS["update_permissions"]
        assert required == "admin"


class TestPermissionCaching:
    """Test permission caching behavior."""

    @pytest.fixture
    def permission_manager(self):
        """Create permission manager."""
        db = InMemoryDatabaseAdapter()
        adapter = AdvancedFeaturesAdapter(db)
        return PermissionManager(db, adapter)

    def test_cache_invalidation(self, permission_manager):
        """Test cache is invalidated on permission changes."""
        # Add to cache
        permission_manager.cache["user-1:requirement:req-123"] = (True, 1000000000)

        # Invalidate
        permission_manager._invalidate_cache("user-1", "requirement", "req-123")

        # Should be gone
        assert "user-1:requirement:req-123" not in permission_manager.cache
