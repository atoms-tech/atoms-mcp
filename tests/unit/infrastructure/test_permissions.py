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


class TestPermissionBasics:
    """Test basic permission functionality."""
    
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
    
    def test_system_admin_bypass(self):
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
            assert checker.check_permission(user, permission, resource)
    
    def test_non_workspace_member_denied(self):
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
            assert not checker.check_permission(user, permission, resource)


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
    
    def test_workspace_owner_permissions(self, checker, owner_user, resource):
        """Test workspace owner has all permissions."""
        # Owner should have all basic permissions
        assert checker.check_permission(owner_user, Permission.CREATE, resource)
        assert checker.check_permission(owner_user, Permission.READ, resource)
        assert checker.check_permission(owner_user, Permission.UPDATE, resource)
        assert checker.check_permission(owner_user, Permission.DELETE, resource)
        assert checker.check_permission(owner_user, Permission.ARCHIVE, resource)
        assert checker.check_permission(owner_user, Permission.RESTORE, resource)
        assert checker.check_permission(owner_user, Permission.EXPORT, resource)
        assert checker.check_permission(owner_user, Permission.MANAGE_PERMISSIONS, resource)
    
    def test_workspace_admin_permissions(self, checker, admin_user, resource):
        """Test workspace admin has most permissions."""
        # Admin should have most permissions except managing permissions
        assert checker.check_permission(admin_user, Permission.CREATE, resource)
        assert checker.check_permission(admin_user, Permission.READ, resource)
        assert checker.check_permission(admin_user, Permission.UPDATE, resource)
        assert checker.check_permission(admin_user, Permission.DELETE, resource)
        assert checker.check_permission(admin_user, Permission.ARCHIVE, resource)
        assert checker.check_permission(admin_user, Permission.RESTORE, resource)
        assert checker.check_permission(admin_user, Permission.EXPORT, resource)
        
        # But not manage permissions
        assert not checker.check_permission(admin_user, Permission.MANAGE_PERMISSIONS, resource)
    
    def test_workspace_member_permissions(self, checker, member_user, resource):
        """Test workspace member has limited permissions."""
        # Member should have read/write but not delete
        assert checker.check_permission(member_user, Permission.CREATE, resource)
        assert checker.check_permission(member_user, Permission.READ, resource)
        assert checker.check_permission(member_user, Permission.UPDATE, resource)
        assert checker.check_permission(member_user, Permission.ARCHIVE, resource)
        assert checker.check_permission(member_user, Permission.RESTORE, resource)
        
        # But not delete or admin functions
        assert not checker.check_permission(member_user, Permission.DELETE, resource)
        assert not checker.check_permission(member_user, Permission.MANAGE_PERMISSIONS, resource)
        assert not checker.check_permission(member_user, Permission.VIEW_AUDIT_LOG, resource)
    
    def test_workspace_viewer_permissions(self, checker, viewer_user, resource):
        """Test workspace viewer has read-only permissions."""
        # Viewer should only have read/list/search permissions
        assert checker.check_permission(viewer_user, Permission.READ, resource)
        assert checker.check_permission(viewer_user, Permission.LIST, resource)
        assert checker.check_permission(viewer_user, Permission.SEARCH, resource)
        assert checker.check_permission(viewer_user, Permission.EXPORT, resource)
        
        # But no write permissions
        assert not checker.check_permission(viewer_user, Permission.CREATE, resource)
        assert not checker.check_permission(viewer_user, Permission.UPDATE, resource)
        assert not checker.check_permission(viewer_user, Permission.DELETE, resource)


class TestOwnershipPermissions:
    """Test ownership-based permissions."""
    
    def test_owner_can_delete_own_resources(self):
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
        assert checker.check_permission(user, Permission.DELETE, resource)
    
    def test_non_owner_cannot_delete(self):
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
        assert not checker.check_permission(user, Permission.DELETE, resource)


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
    
    def test_workflow_management_requires_admin(self, checker, admin_user, member_user):
        """Test workflow management requires admin permissions."""
        workflow_resource = create_resource_context(
            entity_type="workflow",
            workspace_id="ws1"
        )
        
        # Admin can manage workflows
        assert checker.check_permission(admin_user, Permission.UPDATE, workflow_resource)
        assert checker.check_permission(admin_user, Permission.DELETE, workflow_resource)
        
        # Member cannot manage workflows
        assert not checker.check_permission(member_user, Permission.UPDATE, workflow_resource)
        assert not checker.check_permission(member_user, Permission.DELETE, workflow_resource)
    
    def test_audit_log_restricted(self, checker, admin_user, member_user):
        """Test audit log access is restricted."""
        audit_resource = create_resource_context(
            entity_type="audit_log",
            workspace_id="ws1"
        )
        
        # Admin can view audit logs
        assert checker.check_permission(admin_user, Permission.READ, audit_resource)
        
        # Member cannot view audit logs
        assert not checker.check_permission(member_user, Permission.READ, audit_resource)
    
    def test_invitation_management_restricted(self, checker, admin_user, member_user):
        """Test invitation management is restricted."""
        invitation_resource = create_resource_context(
            entity_type="invitation",
            workspace_id="ws1"
        )
        
        # Admin can manage invitations
        assert checker.check_permission(admin_user, Permission.CREATE, invitation_resource)
        assert checker.check_permission(admin_user, Permission.DELETE, invitation_resource)
        
        # Member cannot manage invitations
        assert not checker.check_permission(member_user, Permission.CREATE, invitation_resource)
        assert not checker.check_permission(member_user, Permission.DELETE, invitation_resource)


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


class TestPermissionIntegration:
    """Test permission system integration scenarios."""
    
    def test_cascading_permissions(self):
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
        assert checker.check_permission(user, Permission.READ, parent_resource)
        assert checker.check_permission(user, Permission.READ, child_resource)
    
    def test_permission_inheritance(self):
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
        assert checker.check_permission(workspace_admin, Permission.READ, project_resource)
        assert checker.check_permission(workspace_admin, Permission.READ, doc_resource)
    
    def test_permission_denial_reasons(self):
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
        assert not checker.check_permission(user, Permission.CREATE, resource)
        
        # Viewer cannot update documents
        assert not checker.check_permission(user, Permission.UPDATE, resource)
        
        # But can read
        assert checker.check_permission(user, Permission.READ, resource)


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
