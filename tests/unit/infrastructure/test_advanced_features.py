"""Tests for advanced features adapter (search, export, import, permissions)."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


class TestAdvancedFeaturesAdapter:
    """Test AdvancedFeaturesAdapter for search, export, import, and permissions."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database adapter."""
        return AsyncMock()

    @pytest.fixture
    def adapter(self, mock_db):
        """Create an AdvancedFeaturesAdapter instance."""
        from infrastructure.advanced_features_adapter import AdvancedFeaturesAdapter
        return AdvancedFeaturesAdapter(mock_db)

    # =====================================================
    # SEARCH OPERATIONS
    # =====================================================

    @pytest.mark.asyncio
    async def test_index_entity_creates_new_index(self, adapter, mock_db):
        """Test indexing a new entity creates search index entry."""
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.insert = AsyncMock(return_value={"id": "idx-1", "entity_id": "ent-1"})

        result = await adapter.index_entity(
            entity_type="requirement",
            entity_id="ent-1",
            workspace_id="ws-1",
            title="Test Entity",
            content="Test content for indexing"
        )

        assert result is not None
        assert result["id"] == "idx-1"
        mock_db.get_single.assert_called_once()
        mock_db.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_entity_with_metadata(self, adapter, mock_db):
        """Test indexing entity with metadata."""
        mock_db.get_single = AsyncMock(return_value=None)
        mock_db.insert = AsyncMock(return_value={"id": "idx-2", "entity_id": "ent-2"})

        result = await adapter.index_entity(
            entity_type="requirement",
            entity_id="ent-2",
            workspace_id="ws-1",
            title="Test",
            content="Content",
            metadata={"status": "active", "priority": "high"}
        )

        assert result is not None
        # Verify metadata was passed to insert
        call_args = mock_db.insert.call_args
        assert call_args[0][0] == "search_index"
        assert call_args[0][1]["metadata"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_index_entity_updates_existing(self, adapter, mock_db):
        """Test indexing existing entity updates index."""
        existing_index = {"id": "idx-existing", "entity_id": "ent-1"}
        mock_db.get_single = AsyncMock(return_value=existing_index)
        mock_db.update = AsyncMock(return_value=[{"id": "idx-existing", "entity_id": "ent-1"}])

        result = await adapter.index_entity(
            entity_type="requirement",
            entity_id="ent-1",
            workspace_id="ws-1",
            title="Updated Title",
            content="Updated content"
        )

        assert result is not None
        mock_db.update.assert_called_once()
        mock_db.insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_advanced_search_basic(self, adapter, mock_db):
        """Test basic advanced search without query."""
        mock_db.query = AsyncMock(return_value=[
            {"id": "idx-1", "title": "Item 1"},
            {"id": "idx-2", "title": "Item 2"}
        ])
        mock_db.count_rows = AsyncMock(return_value=2)

        results, total, facets = await adapter.advanced_search(
            workspace_id="ws-1",
            entity_type="requirement"
        )

        assert len(results) == 2
        assert total == 2
        assert isinstance(facets, dict)
        mock_db.query.assert_called_once()
        mock_db.count_rows.assert_called_once()

    @pytest.mark.asyncio
    async def test_advanced_search_with_query(self, adapter, mock_db):
        """Test advanced search with query string."""
        mock_db.query = AsyncMock(return_value=[
            {"id": "idx-1", "title": "Test Requirement", "facets": {"status": ["active"]}}
        ])
        mock_db.count_rows = AsyncMock(return_value=1)

        results, total, facets = await adapter.advanced_search(
            workspace_id="ws-1",
            entity_type="requirement",
            query="test"
        )

        assert len(results) == 1
        assert total == 1
        # Verify facets were extracted
        call_args = mock_db.query.call_args
        assert call_args[1]["filters"]["search_vector"] == "test"

    @pytest.mark.asyncio
    async def test_advanced_search_with_pagination(self, adapter, mock_db):
        """Test advanced search with pagination."""
        mock_db.query = AsyncMock(return_value=[])
        mock_db.count_rows = AsyncMock(return_value=100)

        results, total, facets = await adapter.advanced_search(
            workspace_id="ws-1",
            entity_type="requirement",
            limit=20,
            offset=40
        )

        call_args = mock_db.query.call_args
        assert call_args[1]["limit"] == 20
        assert call_args[1]["offset"] == 40

    @pytest.mark.asyncio
    async def test_advanced_search_extracts_facets(self, adapter, mock_db):
        """Test that facets are properly extracted from results."""
        mock_db.query = AsyncMock(return_value=[
            {"id": "idx-1", "facets": {"status": ["active", "pending"]}},
            {"id": "idx-2", "facets": {"status": ["active"]}}
        ])
        mock_db.count_rows = AsyncMock(return_value=2)

        results, total, facets = await adapter.advanced_search(
            workspace_id="ws-1",
            entity_type="requirement"
        )

        assert "status" in facets
        assert facets["status"]["active"] == 2
        assert facets["status"]["pending"] == 1

    # =====================================================
    # EXPORT OPERATIONS
    # =====================================================

    @pytest.mark.asyncio
    async def test_create_export_job(self, adapter, mock_db):
        """Test creating an export job."""
        mock_db.insert = AsyncMock(return_value={"id": "job-1", "status": "queued"})

        result = await adapter.create_export_job(
            workspace_id="ws-1",
            entity_type="requirement",
            format="json",
            requested_by="user-1"
        )

        assert result is not None
        assert result["status"] == "queued"
        mock_db.insert.assert_called_once()
        call_args = mock_db.insert.call_args
        assert call_args[0][0] == "export_jobs"

    @pytest.mark.asyncio
    async def test_update_export_job_completed(self, adapter, mock_db):
        """Test updating export job to completed state."""
        mock_db.update = AsyncMock(return_value=[{
            "id": "job-1",
            "status": "completed",
            "file_path": "/exports/job-1.json",
            "file_size": 1024
        }])

        result = await adapter.update_export_job(
            job_id="job-1",
            status="completed",
            file_path="/exports/job-1.json",
            file_size=1024,
            row_count=100
        )

        assert result is not None
        assert result["status"] == "completed"
        mock_db.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_export_job_with_error(self, adapter, mock_db):
        """Test updating export job with error message."""
        mock_db.update = AsyncMock(return_value=[{
            "id": "job-1",
            "status": "failed",
            "error_message": "Export timeout"
        }])

        result = await adapter.update_export_job(
            job_id="job-1",
            status="failed",
            error_message="Export timeout"
        )

        assert result["status"] == "failed"
        call_args = mock_db.update.call_args
        assert call_args[1]["data"]["error_message"] == "Export timeout"

    # =====================================================
    # IMPORT OPERATIONS
    # =====================================================

    @pytest.mark.asyncio
    async def test_create_import_job(self, adapter, mock_db):
        """Test creating an import job."""
        mock_db.insert = AsyncMock(return_value={
            "id": "job-1",
            "status": "queued",
            "imported_rows": 0
        })

        result = await adapter.create_import_job(
            workspace_id="ws-1",
            entity_type="requirement",
            format="csv",
            file_name="requirements.csv",
            file_size=5120,
            requested_by="user-1"
        )

        assert result is not None
        assert result["status"] == "queued"
        mock_db.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_import_job_progress(self, adapter, mock_db):
        """Test updating import job progress."""
        mock_db.update = AsyncMock(return_value=[{
            "id": "job-1",
            "status": "processing",
            "total_rows": 100,
            "imported_rows": 50
        }])

        result = await adapter.update_import_job(
            job_id="job-1",
            status="processing",
            total_rows=100,
            imported_rows=50
        )

        assert result["imported_rows"] == 50
        call_args = mock_db.update.call_args
        assert call_args[1]["data"]["total_rows"] == 100

    @pytest.mark.asyncio
    async def test_update_import_job_completed(self, adapter, mock_db):
        """Test completing import job with counts."""
        mock_db.update = AsyncMock(return_value=[{
            "id": "job-1",
            "status": "completed",
            "total_rows": 100,
            "imported_rows": 95,
            "skipped_rows": 5,
            "error_rows": 0
        }])

        result = await adapter.update_import_job(
            job_id="job-1",
            status="completed",
            total_rows=100,
            imported_rows=95,
            skipped_rows=5,
            error_rows=0
        )

        assert result["status"] == "completed"
        assert result["imported_rows"] == 95

    # =====================================================
    # PERMISSION OPERATIONS
    # =====================================================

    @pytest.mark.asyncio
    async def test_get_entity_permissions(self, adapter, mock_db):
        """Test getting permissions for an entity."""
        mock_db.query = AsyncMock(return_value=[
            {"id": "perm-1", "user_id": "user-1", "permission_level": "edit"},
            {"id": "perm-2", "user_id": "user-2", "permission_level": "view"}
        ])

        result = await adapter.get_entity_permissions(
            entity_type="requirement",
            entity_id="ent-1"
        )

        assert len(result) == 2
        mock_db.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_grant_permission_to_user(self, adapter, mock_db):
        """Test granting permission to a user."""
        mock_db.insert = AsyncMock(return_value={
            "id": "perm-1",
            "user_id": "user-1",
            "permission_level": "edit"
        })

        result = await adapter.grant_permission(
            entity_type="requirement",
            entity_id="ent-1",
            workspace_id="ws-1",
            user_id="user-1",
            permission_level="edit",
            granted_by="admin-1"
        )

        assert result is not None
        assert result["permission_level"] == "edit"
        mock_db.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_grant_permission_to_role(self, adapter, mock_db):
        """Test granting permission to a role."""
        mock_db.insert = AsyncMock(return_value={
            "id": "perm-1",
            "role_id": "role-editor",
            "permission_level": "edit"
        })

        result = await adapter.grant_permission(
            entity_type="requirement",
            entity_id="ent-1",
            workspace_id="ws-1",
            role_id="role-editor",
            permission_level="edit"
        )

        assert result is not None
        call_args = mock_db.insert.call_args
        assert call_args[0][1]["role_id"] == "role-editor"

    @pytest.mark.asyncio
    async def test_grant_permission_with_expiration(self, adapter, mock_db):
        """Test granting time-limited permission."""
        mock_db.insert = AsyncMock(return_value={
            "id": "perm-1",
            "user_id": "user-1",
            "permission_level": "view",
            "expires_at": "2025-12-31T23:59:59Z"
        })

        result = await adapter.grant_permission(
            entity_type="requirement",
            entity_id="ent-1",
            workspace_id="ws-1",
            user_id="user-1",
            permission_level="view",
            expires_at="2025-12-31T23:59:59Z"
        )

        assert result["expires_at"] == "2025-12-31T23:59:59Z"

    @pytest.mark.asyncio
    async def test_revoke_permission(self, adapter, mock_db):
        """Test revoking a permission."""
        mock_db.delete = AsyncMock(return_value=True)

        result = await adapter.revoke_permission(permission_id="perm-1")

        assert result is True
        mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_permission_not_found(self, adapter, mock_db):
        """Test revoking non-existent permission."""
        mock_db.delete = AsyncMock(return_value=False)

        result = await adapter.revoke_permission(permission_id="perm-nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_permission_level(self, adapter, mock_db):
        """Test updating permission level."""
        mock_db.update = AsyncMock(return_value=[{
            "id": "perm-1",
            "permission_level": "admin"
        }])

        result = await adapter.update_permission(
            permission_id="perm-1",
            permission_level="admin"
        )

        assert result is not None
        assert result["permission_level"] == "admin"

    @pytest.mark.asyncio
    async def test_update_permission_expiration(self, adapter, mock_db):
        """Test updating permission expiration."""
        mock_db.update = AsyncMock(return_value=[{
            "id": "perm-1",
            "expires_at": "2025-06-30T23:59:59Z"
        }])

        result = await adapter.update_permission(
            permission_id="perm-1",
            expires_at="2025-06-30T23:59:59Z"
        )

        call_args = mock_db.update.call_args
        assert call_args[1]["data"]["expires_at"] == "2025-06-30T23:59:59Z"

    # =====================================================
    # ERROR HANDLING
    # =====================================================

    @pytest.mark.asyncio
    async def test_index_entity_handles_error(self, adapter, mock_db):
        """Test that index_entity handles database errors."""
        mock_db.get_single = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception):
            await adapter.index_entity(
                entity_type="requirement",
                entity_id="ent-1",
                workspace_id="ws-1",
                title="Test",
                content="Content"
            )

    @pytest.mark.asyncio
    async def test_advanced_search_handles_error(self, adapter, mock_db):
        """Test that advanced_search handles database errors."""
        mock_db.query = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception):
            await adapter.advanced_search(
                workspace_id="ws-1",
                entity_type="requirement"
            )

    @pytest.mark.asyncio
    async def test_grant_permission_handles_error(self, adapter, mock_db):
        """Test that grant_permission handles database errors."""
        mock_db.insert = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception):
            await adapter.grant_permission(
                entity_type="requirement",
                entity_id="ent-1",
                workspace_id="ws-1",
                user_id="user-1",
                permission_level="view"
            )
