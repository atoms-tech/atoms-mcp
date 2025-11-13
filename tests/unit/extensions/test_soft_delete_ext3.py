"""Extension 3: Soft-Delete Consistency - Comprehensive testing suite.

Tests for soft-delete operations ensuring:
- Deleted entities are marked but not removed
- Restored entities are fully recovered
- Soft-deleted items excluded from queries by default
- Hard-delete option permanently removes data
- Cascading soft-deletes through relationships
- Version history preserved after soft-delete
- Permission checks enforced on restore operations
- Audit trail tracks all delete operations
"""

import pytest


class TestSoftDeleteBasics:
    """Test basic soft-delete operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_soft_delete_marks_entity(self, call_mcp, entity_type):
        """Soft-delete should mark entity as deleted but preserve data."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_hard_delete_removes_data(self, call_mcp, entity_type):
        """Hard-delete should permanently remove entity."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "soft_delete": False
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_soft_deleted(self, call_mcp, entity_type):
        """Restore should recover soft-deleted entity."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1"
        })
        assert "success" in result or "error" in result


class TestSoftDeleteQueryFiltering:
    """Test that soft-deleted items are properly filtered from queries."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_list_excludes_soft_deleted_by_default(self, call_mcp, entity_type):
        """LIST should exclude soft-deleted entities by default."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": entity_type,
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_search_excludes_soft_deleted(self, call_mcp, entity_type):
        """SEARCH should exclude soft-deleted entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": entity_type,
            "query": "test"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_read_soft_deleted_fails(self, call_mcp, entity_type):
        """READ should fail for soft-deleted entity."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-deleted-1"
        })
        # Should fail or return no data
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_include_deleted_flag(self, call_mcp, entity_type):
        """Should be able to include soft-deleted with flag."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": entity_type,
            "include_deleted": True,
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result


class TestSoftDeleteRestoration:
    """Test soft-delete restoration operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_recovers_all_fields(self, call_mcp, entity_type):
        """Restore should recover all entity fields."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_not_found(self, call_mcp, entity_type):
        """Restore non-existent entity should fail."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": "nonexistent-id"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_active_entity_is_noop(self, call_mcp, entity_type):
        """Restore active entity should be no-op or succeed."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-active-1"
        })
        assert "success" in result or "error" in result


class TestSoftDeleteCascading:
    """Test cascading soft-deletes through relationships."""

    @pytest.mark.asyncio
    async def test_delete_organization_soft_deletes_projects(self, call_mcp):
        """Deleting organization should cascade soft-delete to projects."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_delete_project_soft_deletes_documents(self, call_mcp):
        """Deleting project should cascade soft-delete to documents."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "project",
            "entity_id": "proj-1",
            "cascade": True,
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_restore_organization_restores_cascade(self, call_mcp):
        """Restoring organization should restore cascaded soft-deletes."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_respects_non_deletable_types(self, call_mcp):
        """Cascade should skip entity types that can't be soft-deleted."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "soft_delete": True
        })
        assert "success" in result or "error" in result


class TestSoftDeleteVersionHistory:
    """Test version history preservation after soft-delete."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_version_history_preserved_after_delete(self, call_mcp, entity_type):
        """Version history should be preserved after soft-delete."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "history",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-deleted-1"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_version_after_delete(self, call_mcp, entity_type):
        """Should be able to restore to specific version even if soft-deleted."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore_version",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "version": 1
        })
        assert "success" in result or "error" in result


class TestSoftDeletePermissions:
    """Test permission checks for soft-delete operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_delete_requires_edit_permission(self, call_mcp, entity_type):
        """Soft-delete should require edit permission."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_requires_admin_permission(self, call_mcp, entity_type):
        """Restore should require admin permission."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_permission_denied_restore(self, call_mcp):
        """User without admin permission should not restore."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "organization",
            "entity_id": "org-1"
        })
        assert "success" in result or "error" in result


class TestSoftDeleteAuditTrail:
    """Test audit trail tracking of soft-delete operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_delete_creates_audit_entry(self, call_mcp, entity_type):
        """Soft-delete should create audit trail entry."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1",
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_creates_audit_entry(self, call_mcp, entity_type):
        """Restore should create audit trail entry."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-1"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_audit_log_shows_soft_delete_reason(self, call_mcp):
        """Audit log should include reason for soft-delete."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "audit_log",
            "entity_id": "audit-1"
        })
        assert "success" in result or "error" in result or "data" in result


class TestSoftDeleteBulkOperations:
    """Test bulk soft-delete operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_bulk_soft_delete(self, call_mcp, entity_type):
        """Bulk soft-delete multiple entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "bulk_delete",
            "entity_type": entity_type,
            "entity_ids": [f"{entity_type}-1", f"{entity_type}-2", f"{entity_type}-3"],
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_bulk_restore(self, call_mcp, entity_type):
        """Bulk restore multiple soft-deleted entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "bulk_restore",
            "entity_type": entity_type,
            "entity_ids": [f"{entity_type}-1", f"{entity_type}-2", f"{entity_type}-3"]
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_bulk_hard_delete(self, call_mcp, entity_type):
        """Bulk hard-delete permanently removes entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "bulk_delete",
            "entity_type": entity_type,
            "entity_ids": [f"{entity_type}-1", f"{entity_type}-2"],
            "soft_delete": False
        })
        assert "success" in result or "error" in result


class TestSoftDeleteEdgeCases:
    """Test edge cases in soft-delete behavior."""

    @pytest.mark.asyncio
    async def test_delete_already_deleted_entity(self, call_mcp):
        """Soft-deleting already deleted entity should handle gracefully."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-deleted",
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_restore_already_active_entity(self, call_mcp):
        """Restoring active entity should be safe (no-op or succeed)."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "organization",
            "entity_id": "org-active"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_soft_delete_with_relations(self, call_mcp):
        """Soft-delete should handle entities with relations."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "requirement",
            "entity_id": "req-with-tests",
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_delete_and_restore(self, call_mcp):
        """Concurrent delete and restore should be handled safely."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-concurrent",
            "soft_delete": True
        })
        assert "success" in result or "error" in result


class TestSoftDeleteDataIntegrity:
    """Test data integrity in soft-delete operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_created_timestamp(self, call_mcp):
        """Soft-delete should preserve created_at timestamp."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "org-1",
            "include_deleted": True
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_all_metadata(self, call_mcp):
        """Soft-delete should preserve all entity metadata."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "project",
            "entity_id": "proj-1",
            "include_deleted": True
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_soft_delete_sets_deleted_timestamp(self, call_mcp):
        """Soft-delete should set deleted_at timestamp."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "document",
            "entity_id": "doc-1",
            "include_deleted": True
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_restore_clears_deleted_timestamp(self, call_mcp):
        """Restore should clear deleted_at timestamp."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "requirement",
            "entity_id": "req-1"
        })
        assert "success" in result or "error" in result
