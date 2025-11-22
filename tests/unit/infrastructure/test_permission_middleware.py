"""Tests for permission middleware."""

import pytest
from unittest.mock import AsyncMock, patch

from infrastructure.permission_middleware import (
    PermissionMiddleware,
    PermissionError,
    require_permission
)
from infrastructure.permissions import (
    Permission,
    create_user_context,
    create_resource_context
)

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestPermissionMiddleware:
    """Test permission middleware functionality."""
    
    @pytest.fixture
    def user_context(self):
        return create_user_context(
            user_id="test_user",
            workspace_memberships={"ws1": "workspace_member"}
        )
    
    @pytest.fixture
    def admin_context(self):
        return create_user_context(
            user_id="test_admin",
            workspace_memberships={"ws1": "workspace_admin"}
        )
    
    @pytest.fixture
    def middleware(self, user_context):
        async def get_user_ctx():
            return {
                "user_id": user_context.user_id,
                "username": user_context.username,
                "email": user_context.email,
                "workspace_memberships": user_context.workspace_memberships,
                "is_system_admin": user_context.is_system_admin
            }
        
        return PermissionMiddleware(get_user_ctx)
    
    async def test_create_permission_allowed(self, middleware, user_context):
        """Test create permission check when allowed."""
        # Member can create in their workspace
        await middleware.check_create_permission(
            "document",
            {"workspace_id": "ws1", "name": "Test Doc"}
        )
    
    async def test_create_permission_denied(self, middleware, user_context):
        """Test create permission check when denied."""
        # User not in workspace
        with pytest.raises(PermissionError):
            await middleware.check_create_permission(
                "document",
                {"workspace_id": "ws2", "name": "Test Doc"}
            )
    
    async def test_read_permission_with_entity_data(self, middleware, user_context):
        """Test read permission with entity data available."""
        # User can read in their workspace
        await middleware.check_read_permission(
            "document",
            "doc123",
            {"workspace_id": "ws1", "created_by": "other_user"}
        )
    
    async def test_read_permission_without_entity_data(self, middleware, user_context):
        """Test read permission without entity data (relies on RLS)."""
        # Should not raise error, rely on database RLS
        result = await middleware.check_read_permission("document", "doc123")
        assert result is True
    
    async def test_update_permission_allowed(self, middleware, user_context):
        """Test update permission when allowed."""
        # User can update in their workspace
        await middleware.check_update_permission(
            "document",
            "doc123",
            {"title": "Updated"},
            {"workspace_id": "ws1", "created_by": user_context.user_id}
        )
    
    async def test_update_permission_denied(self, middleware, user_context):
        """Test update permission when denied."""
        # User cannot update if not in workspace
        with pytest.raises(PermissionError):
            await middleware.check_update_permission(
                "document",
                "doc123",
                {"title": "Updated"},
                {"workspace_id": "ws2", "created_by": user_context.user_id}
            )
    
    async def test_delete_permission_allowed_for_owner(self, middleware, user_context):
        """Test delete permission allowed for resource owner."""
        # Member can delete their own resources
        await middleware.check_delete_permission(
            "document",
            "doc123",
            {"workspace_id": "ws1", "created_by": user_context.user_id}
        )
    
    async def test_delete_permission_denied_for_member(self, middleware, user_context):
        """Test delete permission denied for regular member."""
        # Member cannot delete others' resources
        with pytest.raises(PermissionError):
            await middleware.check_delete_permission(
                "document",
                "doc123",
                {"workspace_id": "ws1", "created_by": "other_user"}
            )
    
    async def test_list_permission_allowed(self, middleware, user_context):
        """Test list permission when allowed."""
        # Member can list in their workspace
        await middleware.check_list_permission(
            "document",
            "ws1"
        )
    
    async def test_list_permission_denied(self, middleware, user_context):
        """Test list permission when denied."""
        # User cannot list in workspace they're not member of
        with pytest.raises(PermissionError):
            await middleware.check_list_permission(
                "document",
                "ws2"
            )
    
    async def test_bulk_operation_permission_allowed(self, middleware, admin_context):
        """Test bulk operation permission when allowed."""
        # Admin can perform bulk operations
        await middleware.check_bulk_operation_permission(
            "archive",
            "document",
            "ws1"
        )
    
    async def test_bulk_operation_permission_denied(self, middleware, user_context):
        """Test bulk operation permission when denied."""
        # Member cannot perform bulk deletes
        with pytest.raises(PermissionError):
            await middleware.check_bulk_operation_permission(
                "delete",
                "document",
                "ws1"
            )
    
    async def test_filter_query_results(self, middleware, user_context):
        """Test filtering query results."""
        results = [
            {"id": "1", "entity_type": "document", "workspace_id": "ws1", "created_by": "user1"},
            {"id": "2", "entity_type": "document", "workspace_id": "ws1", "created_by": user_context.user_id},
            {"id": "3", "entity_type": "document", "workspace_id": "ws2", "created_by": "other"},
        ]
        
        filtered = await middleware.filter_query_results(
            user_context, results, "document"
        )
        
        # Should only include accessible documents from ws1
        assert len(filtered) == 2
        filtered_ids = {r["id"] for r in filtered}
        assert "1" in filtered_ids
        assert "2" in filtered_ids
        assert "3" not in filtered_ids


class TestPermissionDecorator:
    """Test permission decorator functionality."""
    
    @pytest.fixture
    def mock_instance(self):
        """Create a mock instance with permission middleware."""
        instance = AsyncMock()
        
        # Add permission middleware
        async def get_user_ctx():
            return {
                "user_id": "test_user",
                "workspace_memberships": {"ws1": "workspace_member"}
            }
        
        instance._permission_middleware = PermissionMiddleware(get_user_ctx)
        return instance
    
    async def test_require_permission_decorator_success(self, mock_instance):
        """Test decorator allows operation when permitted."""
        
        @require_permission("read")
        async def read_method(self, entity_type: str, entity_id: str):
            return f"Read {entity_type}:{entity_id}"
        
        mock_instance.read_method = read_method.__get__(mock_instance)
        
        # Should succeed
        result = await mock_instance.read_method("document", "doc123")
        assert result == "Read document:doc123"
    
    async def test_require_permission_decorator_failure(self, mock_instance):
        """Test decorator denies operation when not permitted."""
        
        @require_permission("delete")
        async def delete_method(self, entity_type: str, entity_id: str, entity_data: dict = None):
            return f"Deleted {entity_type}:{entity_id}"
        
        mock_instance.delete_method = delete_method.__get__(mock_instance)
        
        # Should fail - member cannot delete in workspace they're not in
        with pytest.raises(PermissionError):
            await mock_instance.delete_method(
                "document", 
                "doc123",
                entity_data={"workspace_id": "ws2", "created_by": "other_user"}
            )
    
    async def test_require_permission_decorator_with_kwargs(self, mock_instance):
        """Test decorator works with keyword arguments."""
        
        @require_permission("update")
        async def update_method(self, entity_type: str, entity_id: str, data: dict):
            return f"Updated {entity_type}:{entity_id} with {data}"
        
        mock_instance.update_method = update_method.__get__(mock_instance)
        
        # Should succeed
        result = await mock_instance.update_method(
            entity_type="document",
            entity_id="doc123",
            data={"title": "New Title"}
        )
        assert result == "Updated document:doc123 with {'title': 'New Title'}"
    
    async def test_require_permission_decorator_missing_entity_type(self, mock_instance):
        """Test decorator fails when entity_type missing."""
        
        @require_permission("read")
        async def read_method(self):
            return "Read something"
        
        mock_instance.read_method = read_method.__get__(mock_instance)
        
        # Should fail - entity_type required
        with pytest.raises(PermissionError):
            await mock_instance.read_method()
    
    async def test_require_permission_decorator_unknown_permission(self, mock_instance):
        """Test decorator fails with unknown permission type."""
        
        @require_permission("unknown_permission")
        async def some_method(self, entity_type: str):
            return f"Operation on {entity_type}"
        
        mock_instance.some_method = some_method.__get__(mock_instance)
        
        # Should fail - unknown permission type
        with pytest.raises(PermissionError):
            await mock_instance.some_method("document")


class TestPermissionMiddlewareEdgeCases:
    """Test permission middleware edge cases."""
    
    @pytest.fixture
    def middleware(self):
        async def get_user_ctx():
            return {
                "user_id": "test_user",
                "workspace_memberships": {"ws1": "workspace_member"}
            }
        
        return PermissionMiddleware(get_user_ctx)
    
    async def test_create_permission_missing_workspace_id(self, middleware):
        """Test create permission fails without workspace_id."""
        with pytest.raises(PermissionError):
            await middleware.check_create_permission(
                "document",
                {"name": "Test Doc"}  # No workspace_id
            )
    
    async def test_list_permission_missing_workspace_id(self, middleware):
        """Test list permission fails without workspace_id."""
        with pytest.raises(PermissionError):
            await middleware.check_list_permission(
                "document",
                None  # No workspace_id
            )
    
    async def test_bulk_operation_unknown_operation(self, middleware):
        """Test bulk operation fails with unknown operation."""
        with pytest.raises(PermissionError):
            await middleware.check_bulk_operation_permission(
                "unknown_operation",
                "document",
                "ws1"
            )
    
    async def test_bulk_operation_permission_workflow_admin_required(self, middleware):
        """Test bulk operation on workflow requires admin."""
        async def get_admin_ctx():
            return {
                "user_id": "admin_user",
                "workspace_memberships": {"ws1": "workspace_admin"}
            }
        
        middleware_admin = PermissionMiddleware(get_admin_ctx)
        
        # Admin should be able to bulk archive workflows
        await middleware_admin.check_bulk_operation_permission(
            "archive",
            "workflow",
            "ws1"
        )
    
    async def test_filter_query_results_empty(self, middleware):
        """Test filtering empty results."""
        filtered = await middleware.filter_query_results(
            None, [], "document"
        )
        assert filtered == []
    
    async def test_filter_query_results_none(self, middleware):
        """Test filtering None results."""
        filtered = await middleware.filter_query_results(
            None, None, "document"
        )
        assert filtered is None
    
    async def test_system_admin_bypass_all_checks(self):
        """Test system admin bypasses all permission checks."""
        async def get_admin_ctx():
            return {
                "user_id": "system_admin",
                "is_system_admin": True,
                "workspace_memberships": {}  # Not needed for admin
            }
        
        middleware = PermissionMiddleware(get_admin_ctx)
        
        # System admin can do anything
        await middleware.check_create_permission("document", {"workspace_id": "any_ws"})
        await middleware.check_delete_permission("document", "doc123")
        await middleware.check_list_permission("document", "any_ws")
        await middleware.check_bulk_operation_permission("delete", "document", "any_ws")


class TestPermissionMiddlewareIntegration:
    """Test permission middleware integration scenarios."""
    
    async def test_user_context_conversion(self):
        """Test conversion of user data to UserContext."""
        async def get_user_ctx():
            return {
                "user_id": "user123",
                "username": "testuser",
                "email": "test@example.com",
                "workspace_memberships": {
                    "ws1": "member",
                    "ws2": "admin"
                },
                "is_system_admin": False
            }
        
        middleware = PermissionMiddleware(get_user_ctx)
        user_ctx = await middleware._get_user_context()
        
        assert user_ctx.user_id == "user123"
        assert user_ctx.username == "testuser"
        assert user_ctx.email == "test@example.com"
        assert user_ctx.workspace_memberships == {"ws1": "member", "ws2": "admin"}
        assert not user_ctx.is_system_admin
    
    # Note: test_permission_error_messages, test_workspace_membership_validation,
    # and test_role_based_permission_differences have been moved to e2e tests
    # (tests/e2e/test_permission_middleware.py) to test with real authentication
    # and database operations.
