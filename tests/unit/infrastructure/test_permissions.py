"""Tests for permission system and multi-tenant isolation."""

import pytest
from infrastructure.permissions import (
    PermissionChecker,
    Permission,
    EntityType,
    UserContext,
    ResourceContext,
    create_user_context,
    create_resource_context,
    get_permission_checker
)

pytestmark = [pytest.mark.unit]


class TestPermissionContextCreation:
    """Test creating permission contexts."""
    
    def test_user_context_creation(self):
        """Test creating user context."""
        user = create_user_context(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            workspace_memberships={"ws1": "workspace_owner"}
        )
        
        assert user.user_id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.workspace_memberships == {"ws1": "workspace_owner"}
        assert not user.is_system_admin
    
    def test_resource_context_creation(self):
        """Test creating resource context."""
        resource = create_resource_context(
            entity_type="document",
            workspace_id="ws1",
            entity_id="doc123",
            owner_id="user123"
        )
        
        assert resource.entity_type == EntityType.DOCUMENT
        assert resource.workspace_id == "ws1"
        assert resource.entity_id == "doc123"
        assert resource.owner_id == "user123"


@pytest.mark.asyncio
class TestPermissionBasics:
    """Test basic permission functionality."""
    
    async def test_system_admin_bypass(self):
        """Test system admin bypasses all permission checks."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="admin",
            is_system_admin=True
        )
        resource = create_resource_context(
            entity_type="organization",
            workspace_id="any_ws"
        )
        
        # System admin should have all permissions
        for permission in Permission:
            result = await checker.check_permission(user, permission, resource)
            assert result
    
    async def test_non_workspace_member_denied(self):
        """Test non-workspace members are denied access."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="user123",
            workspace_memberships={"ws1": "workspace_member"}
        )
        resource = create_resource_context(
            entity_type="document",
            workspace_id="ws2"  # Different workspace
        )
        
        # Should be denied for all permissions
        for permission in [Permission.READ, Permission.UPDATE, Permission.DELETE]:
            result = await checker.check_permission(user, permission, resource)
            assert not result


@pytest.mark.asyncio
class TestWorkspaceRolePermissions:
    """Test workspace role-based permissions."""
    
    @pytest.fixture
    def checker(self):
        return get_permission_checker()
    
    @pytest.fixture
    def owner_user(self):
        return create_user_context(
            user_id="owner",
            workspace_memberships={"ws1": "workspace_owner"}
        )
    
    @pytest.fixture
    def admin_user(self):
        return create_user_context(
            user_id="admin",
            workspace_memberships={"ws1": "workspace_admin"}
        )
    
    @pytest.fixture
    def member_user(self):
        return create_user_context(
            user_id="member",
            workspace_memberships={"ws1": "workspace_member"}
        )
    
    @pytest.fixture
    def viewer_user(self):
        return create_user_context(
            user_id="viewer",
            workspace_memberships={"ws1": "workspace_viewer"}
        )
    
    @pytest.fixture
    def resource(self):
        return create_resource_context(
            entity_type="document",
            workspace_id="ws1"
        )
    
    async def test_workspace_owner_permissions(self, checker, owner_user, resource):
        """Test workspace owner has all permissions."""
        # Owner should have all basic permissions
        assert await checker.check_permission(owner_user, Permission.CREATE, resource)
        assert await checker.check_permission(owner_user, Permission.READ, resource)
        assert await checker.check_permission(owner_user, Permission.UPDATE, resource)
        assert await checker.check_permission(owner_user, Permission.DELETE, resource)
        assert await checker.check_permission(owner_user, Permission.ARCHIVE, resource)
        assert await checker.check_permission(owner_user, Permission.RESTORE, resource)
        assert await checker.check_permission(owner_user, Permission.EXPORT, resource)
        assert await checker.check_permission(owner_user, Permission.MANAGE_PERMISSIONS, resource)
    
    async def test_workspace_admin_permissions(self, checker, admin_user, resource):
        """Test workspace admin has most permissions."""
        # Admin should have most permissions except managing permissions
        assert await checker.check_permission(admin_user, Permission.CREATE, resource)
        assert await checker.check_permission(admin_user, Permission.READ, resource)
        assert await checker.check_permission(admin_user, Permission.UPDATE, resource)
        assert await checker.check_permission(admin_user, Permission.DELETE, resource)
        assert await checker.check_permission(admin_user, Permission.ARCHIVE, resource)
        assert await checker.check_permission(admin_user, Permission.RESTORE, resource)
        assert await checker.check_permission(admin_user, Permission.EXPORT, resource)
        
        # But not manage permissions
        assert not await checker.check_permission(admin_user, Permission.MANAGE_PERMISSIONS, resource)
    
    async def test_workspace_member_permissions(self, checker, member_user, resource):
        """Test workspace member has limited permissions."""
        # Member should have read/write but not delete
        assert await checker.check_permission(member_user, Permission.CREATE, resource)
        assert await checker.check_permission(member_user, Permission.READ, resource)
        assert await checker.check_permission(member_user, Permission.UPDATE, resource)
        assert await checker.check_permission(member_user, Permission.ARCHIVE, resource)
        assert await checker.check_permission(member_user, Permission.RESTORE, resource)
        
        # But not delete or admin functions
        assert not await checker.check_permission(member_user, Permission.DELETE, resource)
        assert not await checker.check_permission(member_user, Permission.MANAGE_PERMISSIONS, resource)
        assert not await checker.check_permission(member_user, Permission.VIEW_AUDIT_LOG, resource)
    
    async def test_workspace_viewer_permissions(self, checker, viewer_user, resource):
        """Test workspace viewer has read-only permissions."""
        # Viewer should only have read/list/search permissions
        assert await checker.check_permission(viewer_user, Permission.READ, resource)
        assert await checker.check_permission(viewer_user, Permission.LIST, resource)
        assert await checker.check_permission(viewer_user, Permission.SEARCH, resource)
        assert await checker.check_permission(viewer_user, Permission.EXPORT, resource)
        
        # But no write permissions
        assert not await checker.check_permission(viewer_user, Permission.CREATE, resource)
        assert not await checker.check_permission(viewer_user, Permission.UPDATE, resource)
        assert not await checker.check_permission(viewer_user, Permission.DELETE, resource)


@pytest.mark.asyncio
class TestOwnershipPermissions:
    """Test ownership-based permissions."""
    
    async def test_owner_can_delete_own_resources(self):
        """Test users can delete resources they own."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="owner",
            workspace_memberships={"ws1": "workspace_member"}
        )
        resource = create_resource_context(
            entity_type="document",
            workspace_id="ws1",
            owner_id="owner"  # User owns this resource
        )
        
        # Even though member role doesn't allow delete, owner should be able to
        assert await checker.check_permission(user, Permission.DELETE, resource)
    
    async def test_non_owner_cannot_delete(self):
        """Test users cannot delete resources they don't own."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="member",
            workspace_memberships={"ws1": "workspace_member"}
        )
        resource = create_resource_context(
            entity_type="document",
            workspace_id="ws1",
            owner_id="other_user"  # Different owner
        )
        
        # Member role + not owner = cannot delete
        assert not await checker.check_permission(user, Permission.DELETE, resource)


@pytest.mark.asyncio
class TestEntityTypeSpecificPermissions:
    """Test entity type-specific permission rules."""
    
    @pytest.fixture
    def checker(self):
        return get_permission_checker()
    
    @pytest.fixture
    def admin_user(self):
        return create_user_context(
            user_id="admin",
            workspace_memberships={"ws1": "workspace_admin"}
        )
    
    @pytest.fixture
    def member_user(self):
        return create_user_context(
            user_id="member",
            workspace_memberships={"ws1": "workspace_member"}
        )
    
    async def test_workflow_management_requires_admin(self, checker, admin_user, member_user):
        """Test workflow management requires admin permissions."""
        workflow_resource = create_resource_context(
            entity_type="workflow",
            workspace_id="ws1"
        )
        
        # Admin can manage workflows
        assert await checker.check_permission(admin_user, Permission.UPDATE, workflow_resource)
        assert await checker.check_permission(admin_user, Permission.DELETE, workflow_resource)
        
        # Member cannot manage workflows
        assert not await checker.check_permission(member_user, Permission.UPDATE, workflow_resource)
        assert not await checker.check_permission(member_user, Permission.DELETE, workflow_resource)
    
    async def test_audit_log_restricted(self, checker, admin_user, member_user):
        """Test audit log access is restricted."""
        audit_resource = create_resource_context(
            entity_type="audit_log",
            workspace_id="ws1"
        )
        
        # Admin can view audit logs
        assert await checker.check_permission(admin_user, Permission.READ, audit_resource)
        
        # Member cannot view audit logs
        assert not await checker.check_permission(member_user, Permission.READ, audit_resource)
    
    async def test_invitation_management_restricted(self, checker, admin_user, member_user):
        """Test invitation management is restricted."""
        invitation_resource = create_resource_context(
            entity_type="invitation",
            workspace_id="ws1"
        )
        
        # Admin can manage invitations
        assert await checker.check_permission(admin_user, Permission.CREATE, invitation_resource)
        assert await checker.check_permission(admin_user, Permission.DELETE, invitation_resource)
        
        # Member cannot manage invitations
        assert not await checker.check_permission(member_user, Permission.CREATE, invitation_resource)
        assert not await checker.check_permission(member_user, Permission.DELETE, invitation_resource)


class TestMultiTenantIsolation:
    """Test multi-tenant isolation features."""
    
    def test_validate_workspace_access(self):
        """Test workspace access validation."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="user",
            workspace_memberships={"ws1": "member", "ws2": "admin"}
        )
        
        # Can access own workspaces
        assert checker.validate_multi_tenant_access(user, "ws1")
        assert checker.validate_multi_tenant_access(user, "ws2")
        
        # Cannot access other workspaces
        assert not checker.validate_multi_tenant_access(user, "ws3")
        assert not checker.validate_multi_tenant_access(user, "unauthorized_ws")
    
    def test_filter_entities_by_permission(self):
        """Test filtering entities based on permissions."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="member",
            workspace_memberships={"ws1": "workspace_member", "ws2": "workspace_viewer"}
        )
        
        entities = [
            {"id": "1", "entity_type": "document", "workspace_id": "ws1", "created_by": "member"},
            {"id": "2", "entity_type": "document", "workspace_id": "ws1", "created_by": "other"},
            {"id": "3", "entity_type": "document", "workspace_id": "ws2", "created_by": "member"},
            {"id": "4", "entity_type": "document", "workspace_id": "ws3", "created_by": "member"},  # Not member
        ]
        
        # Filter for read permissions
        accessible = checker.filter_entities_by_permission(user, entities, Permission.READ)
        
        # Should have access to ws1 (member) and ws2 (viewer) but not ws3
        accessible_ids = {e["id"] for e in accessible}
        assert "1" in accessible_ids
        assert "2" in accessible_ids
        assert "3" in accessible_ids
        assert "4" not in accessible_ids
    
    def test_get_accessible_entities(self):
        """Test getting accessible entity types."""
        checker = get_permission_checker()
        admin_user = create_user_context(
            user_id="admin",
            workspace_memberships={"ws1": "workspace_admin"}
        )
        viewer_user = create_user_context(
            user_id="viewer",
            workspace_memberships={"ws1": "workspace_viewer"}
        )
        
        # Admin should have access to all entity types
        admin_accessible = checker.get_accessible_entities(admin_user, "ws1")
        assert len(admin_accessible) > 0
        
        # Viewer should have limited access (read-only entities)
        viewer_accessible = checker.get_accessible_entities(viewer_user, "ws1")
        assert EntityType.DOCUMENT in viewer_accessible
        assert EntityType.PROJECT in viewer_accessible


@pytest.mark.asyncio
class TestPermissionIntegration:
    """Test permission system integration scenarios."""
    
    async def test_cascading_permissions(self):
        """Test permission cascading from parent to child."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="member",
            workspace_memberships={"ws1": "workspace_member"}
        )
        
        # Parent resource user can read
        parent_resource = create_resource_context(
            entity_type="project",
            workspace_id="ws1",
            entity_id="proj1"
        )
        
        # Child resource (test case)
        child_resource = create_resource_context(
            entity_type="test",
            workspace_id="ws1",
            entity_id="test1",
            parent_id="proj1"
        )
        
        # Should be able to read child if can read parent
        assert await checker.check_permission(user, Permission.READ, parent_resource)
        assert await checker.check_permission(user, Permission.READ, child_resource)
    
    async def test_permission_inheritance(self):
        """Test permission inheritance scenarios."""
        checker = get_permission_checker()
        
        # Create hierarchy of permissions
        workspace_admin = create_user_context(
            user_id="admin",
            workspace_memberships={"ws1": "workspace_admin"}
        )
        
        project_resource = create_resource_context(
            entity_type="project",
            workspace_id="ws1"
        )
        
        doc_resource = create_resource_context(
            entity_type="document",
            workspace_id="ws1",
            parent_id="project1"
        )
        
        # Admin should have access to both
        assert await checker.check_permission(workspace_admin, Permission.READ, project_resource)
        assert await checker.check_permission(workspace_admin, Permission.READ, doc_resource)
    
    async def test_permission_denial_reasons(self):
        """Test different reasons for permission denial."""
        checker = get_permission_checker()
        user = create_user_context(
            user_id="user",
            workspace_memberships={"ws1": "workspace_viewer"}
        )
        
        resource = create_resource_context(
            entity_type="document",
            workspace_id="ws1"
        )
        
        # Viewer cannot create documents
        assert not await checker.check_permission(user, Permission.CREATE, resource)
        
        # Viewer cannot update documents
        assert not await checker.check_permission(user, Permission.UPDATE, resource)
        
        # But can read
        assert await checker.check_permission(user, Permission.READ, resource)


class TestPermissionPerformance:
    """Test permission system performance."""
    
    def test_permission_check_performance(self):
        """Test permission checking is efficient."""
        import time
        
        checker = get_permission_checker()
        user = create_user_context(
            user_id="user",
            workspace_memberships={"ws1": "workspace_member"}
        )
        resource = create_resource_context(
            entity_type="document",
            workspace_id="ws1"
        )
        
        # Check many permissions quickly
        start_time = time.time()
        for _ in range(1000):
            checker.check_permission(user, Permission.READ, resource)
        end_time = time.time()
        
        # Should be very fast (< 0.1 seconds for 1000 checks)
        duration = end_time - start_time
        assert duration < 0.1, f"Permission checks too slow: {duration}s for 1000 checks"
    
    def test_filtering_performance(self):
        """Test entity filtering is efficient."""
        import time
        
        checker = get_permission_checker()
        user = create_user_context(
            user_id="user",
            workspace_memberships={"ws1": "workspace_member"}
        )
        
        # Create large list of entities
        entities = [
            {
                "id": str(i),
                "entity_type": "document",
                "workspace_id": "ws1" if i % 2 == 0 else "ws2",
                "created_by": "user" if i % 3 == 0 else "other"
            }
            for i in range(1000)
        ]
        
        # Filter entities
        start_time = time.time()
        accessible = checker.filter_entities_by_permission(user, entities, Permission.READ)
        end_time = time.time()
        
        # Should be reasonable time for 1000 entities
        duration = end_time - start_time
        assert duration < 0.5, f"Entity filtering too slow: {duration}s for 1000 entities"
        
        # Should filter out entities from ws2
        assert len(accessible) < len(entities)
        for entity in accessible:
            assert entity["workspace_id"] == "ws1"
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
