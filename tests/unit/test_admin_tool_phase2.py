"""Unit tests for Phase 2 Week 1: Admin Tool.

Tests workspace management, user management, and audit logging.
"""

import pytest
from tools.admin import get_admin_tool


class TestAdminToolPhase2:
    """Test Phase 2 admin tool functionality."""

    @pytest.fixture
    def admin_tool(self):
        """Get admin tool instance."""
        return get_admin_tool()

    # ========== Workspace Management Tests ==========

    @pytest.mark.asyncio
    async def test_create_workspace(self, admin_tool):
        """Test creating a workspace."""
        result = await admin_tool.create_workspace(
            organization_id="org-1",
            name="Test Workspace",
            description="Test workspace description"
        )

        assert result["success"] is True
        assert result["data"]["name"] == "Test Workspace"
        assert result["data"]["organization_id"] == "org-1"
        assert result["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_workspace_missing_required(self, admin_tool):
        """Test creating workspace with missing required fields."""
        result = await admin_tool.create_workspace(
            organization_id="",
            name="Test"
        )

        assert result["success"] is False
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_create_workspace_with_settings(self, admin_tool):
        """Test creating workspace with settings."""
        settings = {"theme": "dark", "language": "en"}
        result = await admin_tool.create_workspace(
            organization_id="org-1",
            name="Test Workspace",
            settings=settings
        )

        assert result["success"] is True
        assert result["data"]["settings"] == settings

    # ========== User Management Tests ==========

    @pytest.mark.asyncio
    async def test_invite_user(self, admin_tool):
        """Test inviting user to workspace."""
        result = await admin_tool.invite_user(
            workspace_id="ws-1",
            email="user@example.com",
            role="editor"
        )

        assert result["success"] is True
        assert result["data"]["email"] == "user@example.com"
        assert result["data"]["role"] == "editor"
        assert result["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_invite_user_invalid_role(self, admin_tool):
        """Test inviting user with invalid role."""
        result = await admin_tool.invite_user(
            workspace_id="ws-1",
            email="user@example.com",
            role="invalid"
        )

        assert result["success"] is False
        assert "Invalid role" in result["error"]

    @pytest.mark.asyncio
    async def test_invite_user_missing_required(self, admin_tool):
        """Test inviting user with missing required fields."""
        result = await admin_tool.invite_user(
            workspace_id="",
            email="user@example.com"
        )

        assert result["success"] is False
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_user(self, admin_tool):
        """Test removing user from workspace."""
        result = await admin_tool.remove_user(
            workspace_id="ws-1",
            user_id="user-1"
        )

        assert result["success"] is True
        assert "removed" in result["message"]

    @pytest.mark.asyncio
    async def test_remove_user_missing_required(self, admin_tool):
        """Test removing user with missing required fields."""
        result = await admin_tool.remove_user(
            workspace_id="",
            user_id="user-1"
        )

        assert result["success"] is False
        assert "required" in result["error"]

    # ========== Audit Logging Tests ==========

    @pytest.mark.asyncio
    async def test_audit_log_created_on_workspace_create(self, admin_tool):
        """Test audit log entry created on workspace creation."""
        await admin_tool.create_workspace(
            organization_id="org-1",
            name="Test Workspace"
        )

        logs = admin_tool.get_audit_log_entries()
        assert len(logs) > 0
        assert logs[-1]["action"] == "create_workspace"

    @pytest.mark.asyncio
    async def test_audit_log_created_on_user_invite(self, admin_tool):
        """Test audit log entry created on user invite."""
        await admin_tool.invite_user(
            workspace_id="ws-1",
            email="user@example.com"
        )

        logs = admin_tool.get_audit_log_entries()
        assert len(logs) > 0
        assert logs[-1]["action"] == "invite_user"

    @pytest.mark.asyncio
    async def test_get_audit_log(self, admin_tool):
        """Test retrieving audit log."""
        # Create some events
        await admin_tool.create_workspace(
            organization_id="org-1",
            name="Workspace 1"
        )
        await admin_tool.create_workspace(
            organization_id="org-1",
            name="Workspace 2"
        )

        result = await admin_tool.get_audit_log(
            workspace_id="org-1",
            limit=10
        )

        assert result["success"] is True
        assert "data" in result
        assert "pagination" in result

    @pytest.mark.asyncio
    async def test_get_audit_log_pagination(self, admin_tool):
        """Test audit log pagination."""
        # Create multiple events
        for i in range(5):
            await admin_tool.create_workspace(
                organization_id="org-1",
                name=f"Workspace {i}"
            )

        result = await admin_tool.get_audit_log(
            workspace_id="org-1",
            limit=2,
            offset=0
        )

        assert result["success"] is True
        assert len(result["data"]) <= 2
        assert result["pagination"]["has_next"] is True

    @pytest.mark.asyncio
    async def test_get_audit_log_missing_workspace_id(self, admin_tool):
        """Test getting audit log with missing workspace_id."""
        result = await admin_tool.get_audit_log(
            workspace_id="",
            limit=10
        )

        assert result["success"] is False
        assert "required" in result["error"]

    # ========== Settings Management Tests ==========

    @pytest.mark.asyncio
    async def test_update_workspace_settings(self, admin_tool):
        """Test updating workspace settings."""
        settings = {"theme": "dark", "language": "en"}
        result = await admin_tool.update_workspace_settings(
            workspace_id="ws-1",
            settings=settings
        )

        assert result["success"] is True
        assert result["data"] == settings

    @pytest.mark.asyncio
    async def test_update_workspace_settings_missing_required(self, admin_tool):
        """Test updating settings with missing required fields."""
        result = await admin_tool.update_workspace_settings(
            workspace_id="",
            settings={}
        )

        assert result["success"] is False
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_audit_log_created_on_settings_update(self, admin_tool):
        """Test audit log entry created on settings update."""
        await admin_tool.update_workspace_settings(
            workspace_id="ws-1",
            settings={"theme": "dark"}
        )

        logs = admin_tool.get_audit_log_entries()
        assert len(logs) > 0
        assert logs[-1]["action"] == "update_workspace_settings"

