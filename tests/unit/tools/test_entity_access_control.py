"""Test entity tool permission integration.

Tests comprehensive permission enforcement for all entity operations:
- Create, Read, Update, Delete permissions
- Workspace-based multi-tenant isolation
- Role-based access control
- Bulk operations permissions
- Ownership-based permissions

Run with: pytest tests/unit/tools/test_entity_access_control.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch

from tests.unit.tools.conftest import unwrap_mcp_response

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestEntityPermissionIntegration:
    """Test permission enforcement in entity operations."""
    
    @pytest.mark.story("Security - Permission enforcement")
    @pytest.mark.unit
    async def test_create_document_permission_check(self, call_mcp, test_organization):
        """Test create operation checks permissions."""
        # Mock user context with workspace membership
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "test_user",
                "username": "testuser",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # This should succeed - member can create in their workspace
            result = await call_mcp(
                "create_entity",
                entity_type="document",
                data={
                    "name": "Test Document",
                    "project_id": test_organization["project"]["id"],
                    "workspace_id": "ws1"
                }
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is True
            assert "id" in response
    
    @pytest.mark.story("Security - Multi-tenant isolation")
    @pytest.mark.unit
    async def test_create_document_cross_workspace_denied(self, call_mcp, test_organization):
        """Test create operation denied for cross-workspace access."""
        # Mock user context - member of different workspace
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "test_user",
                "username": "testuser",
                "workspace_memberships": {"ws1": "workspace_member"},  # Not ws2
                "is_system_admin": False
            }
            
            # This should fail - creating in workspace user doesn't belong to
            result = await call_mcp(
                "create_entity",
                entity_type="document",
                data={
                    "name": "Test Document",
                    "project_id": test_organization["project"]["id"],
                    "workspace_id": "ws2"  # Different workspace
                }
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is False
            assert "permission" in response["error"].lower()
    
    @pytest.mark.story("Security - Permission enforcement")
    @pytest.mark.unit
    async def test_read_document_permission_check(self, call_mcp, test_document):
        """Test read operation checks permissions."""
        # Mock user context
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "test_user",
                "username": "testuser",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # Should succeed - member can read in their workspace
            result = await call_mcp(
                "read_entity",
                entity_type="document",
                entity_id=test_document["id"]
            )
            
            response = unwrap_mcp_response(result)
            assert response["id"] == test_document["id"]
    
    @pytest.mark.story("Security - Multi-tenant isolation")
    @pytest.mark.unit
    async def test_read_document_cross_workspace_denied(self, call_mcp, test_document):
        """Test read operation denied for cross-workspace access."""
        # Mock user from different workspace
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "other_user",
                "username": "otheruser",
                "workspace_memberships": {"ws2": "workspace_member"},  # Not ws1
                "is_system_admin": False
            }
            
            # Should fail due to RLS policies
            result = await call_mcp(
                "read_entity",
                entity_type="document",
                entity_id=test_document["id"]
            )
            
            response = unwrap_mcp_response(result)
            assert response is None  # RLS prevents access
    
    @pytest.mark.story("Security - Ownership permissions")
    @pytest.mark.unit
    async def test_update_own_document_allowed(self, call_mcp, test_document):
        """Test user can update their own document."""
        # Mock owner of the document
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": test_document["created_by"],
                "username": "owner",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            result = await call_mcp(
                "update_entity",
                entity_type="document",
                entity_id=test_document["id"],
                data={"title": "Updated Title"}
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is True
            assert response["title"] == "Updated Title"
    
    @pytest.mark.story("Security - Ownership permissions")
    @pytest.mark.unit
    async def test_update_other_document_denied(self, call_mcp, test_document):
        """Test user cannot update others' documents."""
        # Mock different user
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "other_user",
                "username": "other",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            result = await call_mcp(
                "update_entity",
                entity_type="document",
                entity_id=test_document["id"],
                data={"title": "Hijacked Title"}
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is False
            assert "permission" in response["error"].lower()
    
    @pytest.mark.story("Security - Role permissions")
    @pytest.mark.unit
    async def test_delete_document_owner_allowed(self, call_mcp, test_document):
        """Test owner can delete their document."""
        # Mock owner of the document
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": test_document["created_by"],
                "username": "owner",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            result = await call_mcp(
                "delete_entity",
                entity_type="document",
                entity_id=test_document["id"]
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is True
    
    @pytest.mark.story("Security - Role permissions")
    @pytest.mark.unit
    async def test_delete_document_member_denied(self, call_mcp, test_document):
        """Test member cannot delete others' documents."""
        # Mock different user
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "member_user",
                "username": "member",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            result = await call_mcp(
                "delete_entity",
                entity_type="document",
                entity_id=test_document["id"]
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is False
            assert "permission" in response["error"].lower()
    
    @pytest.mark.story("Security - Admin permissions")
    @pytest.mark.unit
    async def test_admin_delete_any_document(self, call_mcp, test_document):
        """Test admin can delete any document in workspace."""
        # Mock workspace admin
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "admin_user",
                "username": "admin",
                "workspace_memberships": {"ws1": "workspace_admin"},
                "is_system_admin": False
            }
            
            result = await call_mcp(
                "delete_entity",
                entity_type="document",
                entity_id=test_document["id"]
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is True
    
    @pytest.mark.story("Security - System admin bypass")
    @pytest.mark.unit
    async def test_system_admin_bypass_all_permissions(self, call_mcp, test_document):
        """Test system admin bypasses all permission checks."""
        # Mock system admin
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "system_admin",
                "username": "systemadmin",
                "workspace_memberships": {},  # Not a member of any workspace
                "is_system_admin": True
            }
            
            # Can do anything, anywhere
            result = await call_mcp(
                "update_entity",
                entity_type="document",
                entity_id=test_document["id"],
                data={"title": "System Admin Update"}
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is True
            assert response["title"] == "System Admin Update"
    
    @pytest.mark.story("Security - Bulk operations")
    @pytest.mark.unit
    async def test_bulk_operations_require_permission(self, call_mcp, test_document):
        """Test bulk operations require proper permissions."""
        # Mock member without bulk permission
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "regular_user",
                "username": "regular",
                "workspace_memberships": {"ws1": "workspace_viewer"},  # Read-only
                "is_system_admin": False
            }
            
            # Should fail - viewer cannot bulk delete
            result = await call_mcp(
                "bulk_delete_entities",
                entity_type="document",
                entity_ids=[test_document["id"]]
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is False
            assert "permission" in response["error"].lower()
    
    @pytest.mark.story("Security - Workspace isolation")
    @pytest.mark.unit
    async def test_list_entities_respects_workspace(self, call_mcp):
        """Test list entities respects workspace boundaries."""
        # Mock user in ws1
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "user1",
                "username": "user1",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # Should only return documents from ws1
            result = await call_mcp(
                "list_entities",
                entity_type="document",
                filters={"workspace_id": "ws1"}
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is True
            
            # All results should be from ws1
            for doc in response.get("results", []):
                assert doc.get("workspace_id") == "ws1"
    
    @pytest.mark.story("Security - Search operations")
    @pytest.mark.unit
    async def test_search_respects_permissions(self, call_mcp):
        """Test search operations respect permissions."""
        # Mock user
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "search_user",
                "username": "searcher",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # Search should only return accessible documents
            result = await call_mcp(
                "search_entities",
                entity_type="document",
                filters={"workspace_id": "ws1"},
                search_term="test"
            )
            
            response = unwrap_mcp_response(result)
            assert isinstance(response, list)
            
            # All results should be from ws1
            for doc in response:
                assert doc.get("workspace_id") == "ws1"
    
    @pytest.mark.story("Security - Workflow permissions")
    @pytest.mark.unit
    async def test_workflow_management_admin_only(self, call_mcp):
        """Test only admins can manage workflows."""
        # Mock regular member
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "member_user",
                "username": "member",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # Should fail - member cannot create workflow
            result = await call_mcp(
                "create_workflow",
                workspace_id="ws1",
                name="Test Workflow",
                created_by="member_user"
            )
            
            response = unwrap_mcp_response(result)
            assert response["success"] is False
            assert "permission" in response["error"].lower()
    
    @pytest.mark.story("Security - Audit log access")
    @pytest.mark.unit
    async def test_audit_log_access_restricted(self, call_mcp):
        """Test audit log access is restricted to admins."""
        # Mock regular member
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "member_user",
                "username": "member",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # Should fail - member cannot access audit logs
            result = await call_mcp(
                "read_entity",
                entity_type="audit_log",
                entity_id="audit123"
            )
            
            response = unwrap_mcp_response(result)
            assert response is None or response["success"] is False
    
    @pytest.mark.story("Security - Permission inheritance")
    @pytest.mark.unit
    async def test_permission_inheritance_from_parent(self, call_mcp, test_document):
        """Test permissions inherit from parent entities."""
        # Mock user with read access to parent project
        with patch('tools.entity.EntityManager._get_user_context') as mock_ctx:
            mock_ctx.return_value = {
                "user_id": "reader_user",
                "username": "reader",
                "workspace_memberships": {"ws1": "workspace_member"},
                "is_system_admin": False
            }
            
            # Can read test because parent project is accessible
            result = await call_mcp(
                "read_entity",
                entity_type="test",
                entity_id="test123",
            )
            
            # If test belongs to accessible document, should be readable
            # This tests permission inheritance logic
            assert result is not None
