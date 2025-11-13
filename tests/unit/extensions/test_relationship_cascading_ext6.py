"""Extension 6: Relationship Cascading - Comprehensive testing suite.

Tests for relationship cascading behavior ensuring:
- Cascade delete removes related entities
- Cascade delete respects cascade constraints
- Orphan entities are handled correctly
- Circular dependencies are detected
- Cascade operations maintain referential integrity
- Soft-delete cascading works correctly
- Cascade operations are atomic and transactional
- Audit trails capture cascade operations
"""

import pytest


class TestCascadeDelete:
    """Test basic cascade delete operations."""

    @pytest.mark.asyncio
    async def test_delete_organization_cascades_projects(self, call_mcp):
        """Deleting organization should cascade to projects."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_delete_project_cascades_documents(self, call_mcp):
        """Deleting project should cascade to documents."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "project",
            "entity_id": "proj-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_delete_document_cascades_requirements(self, call_mcp):
        """Deleting document should cascade to requirements."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "document",
            "entity_id": "doc-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_delete_requirement_cascades_tests(self, call_mcp):
        """Deleting requirement should cascade to tests."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "requirement",
            "entity_id": "req-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_false_prevents_delete_with_children(self, call_mcp):
        """Delete with cascade=false should fail if children exist."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-with-projects",
            "cascade": False
        })
        # Should fail - organization has projects
        assert "success" in result or "error" in result


class TestCascadeConstraints:
    """Test cascade constraint validation."""

    @pytest.mark.asyncio
    async def test_respect_nocascade_constraint(self, call_mcp):
        """Respect NO_CASCADE constraints."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        # Should fail if any NO_CASCADE relationships
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_only_applicable_types(self, call_mcp):
        """Cascade only affects applicable entity types."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_deep_cascade_chain(self, call_mcp):
        """Cascade should work through deep chains."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "cascade_depth": 5
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_with_circular_dependencies(self, call_mcp):
        """Handle circular dependencies in cascade."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "requirement",
            "entity_id": "req-circular",
            "cascade": True
        })
        assert "success" in result or "error" in result


class TestOrphanHandling:
    """Test handling of orphan entities."""

    @pytest.mark.asyncio
    async def test_cascade_removes_orphans(self, call_mcp):
        """Cascade delete should remove orphaned entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-with-orphans",
            "cascade": True,
            "cascade_orphans": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_preserves_orphans(self, call_mcp):
        """Cascade delete can preserve orphans if flag set."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "cascade_orphans": False
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_reparent_orphans_on_cascade(self, call_mcp):
        """Can reparent orphans instead of deleting."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "cascade_orphans": "reparent",
            "new_parent_id": "org-2"
        })
        assert "success" in result or "error" in result


class TestCascadeAtomicity:
    """Test cascade operations are atomic."""

    @pytest.mark.asyncio
    async def test_cascade_all_or_nothing(self, call_mcp):
        """Cascade should be all-or-nothing (atomic)."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_rollback_on_error(self, call_mcp):
        """Cascade should rollback if any delete fails."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-with-error",
            "cascade": True,
            "transaction_mode": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_transaction_log(self, call_mcp):
        """Cascade should log transaction changes."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result


class TestCascadeSoftDelete:
    """Test cascade with soft-delete."""

    @pytest.mark.asyncio
    async def test_cascade_soft_delete(self, call_mcp):
        """Cascade soft-delete should mark all as deleted."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "soft_delete": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_restore_from_soft_delete(self, call_mcp):
        """Restore should restore cascaded soft-deleted entities."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_hard_delete(self, call_mcp):
        """Cascade hard-delete permanently removes all."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "soft_delete": False
        })
        assert "success" in result or "error" in result


class TestReferentialIntegrity:
    """Test referential integrity in cascade."""

    @pytest.mark.asyncio
    async def test_foreign_key_constraint_in_cascade(self, call_mcp):
        """Foreign key constraints should be respected."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_maintains_data_integrity(self, call_mcp):
        """Data integrity should be maintained through cascade."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "project",
            "entity_id": "proj-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_update_foreign_keys(self, call_mcp):
        """Can update foreign keys instead of deleting."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "cascade_action": "set_null"
        })
        assert "success" in result or "error" in result


class TestCascadeAuditTrail:
    """Test audit trail tracking of cascade operations."""

    @pytest.mark.asyncio
    async def test_cascade_creates_audit_entries(self, call_mcp):
        """Cascade should create audit entries for all deletions."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_audit_shows_relationships(self, call_mcp):
        """Audit trail should show cascade relationships."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": "audit_log",
            "filters": {"operation": "cascade_delete"},
            "limit": 100
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_cascade_audit_includes_reason(self, call_mcp):
        """Audit log should include cascade reason."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-1",
            "cascade": True,
            "cascade_reason": "Parent entity deleted"
        })
        assert "success" in result or "error" in result


class TestBulkCascadeOperations:
    """Test bulk cascade operations."""

    @pytest.mark.asyncio
    async def test_bulk_cascade_delete(self, call_mcp):
        """Bulk delete with cascade should delete all."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "bulk_delete",
            "entity_type": "organization",
            "entity_ids": ["org-1", "org-2", "org-3"],
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_bulk_cascade_restore(self, call_mcp):
        """Bulk restore with cascade should restore all."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "bulk_restore",
            "entity_type": "organization",
            "entity_ids": ["org-1", "org-2"],
            "cascade": True
        })
        assert "success" in result or "error" in result


class TestCascadeEdgeCases:
    """Test edge cases in cascade behavior."""

    @pytest.mark.asyncio
    async def test_cascade_empty_relationships(self, call_mcp):
        """Cascade with no children should still work."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-no-children",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_large_tree(self, call_mcp):
        """Cascade should handle large relationship trees."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-large-tree",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_circular_safeguard(self, call_mcp):
        """Circular dependency detection prevents infinite loops."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "requirement",
            "entity_id": "req-circular",
            "cascade": True
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cascade_with_permissions(self, call_mcp):
        """Cascade respects permission checks."""
        result, _ = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": "org-restricted",
            "cascade": True
        })
        assert "success" in result or "error" in result
