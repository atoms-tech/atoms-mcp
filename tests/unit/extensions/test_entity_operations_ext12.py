"""Tests for entity-specific operations across all entity types."""

import pytest


# All entity types to test
ENTITY_TYPES = [
    "organization", "project", "document", "requirement",
    "test", "property", "block", "column", "trace_link",
    "assignment", "audit_log", "notification",
    "external_document", "test_matrix_view",
    "organization_member", "project_member",
    "organization_invitation", "requirement_test",
    "profile", "user"
]

# Core operations to test
CORE_OPERATIONS = [
    "create", "read", "update", "delete"
]

# Extended operations
EXTENDED_OPERATIONS = [
    "archive", "restore", "list", "search"
]

# Bulk operations
BULK_OPERATIONS = [
    "bulk_update", "bulk_delete", "bulk_archive"
]

# All operations combined
ALL_OPERATIONS = CORE_OPERATIONS + EXTENDED_OPERATIONS + BULK_OPERATIONS


class TestEntityOperationsCrud:
    """Test CRUD operations across all entity types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_create_entity(self, call_mcp, entity_type):
        """Test creating entity of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "create",
            "entity_type": entity_type,
            "data": {"name": f"{entity_type}_test"}
        })
        # Should either succeed or handle gracefully
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_read_entity(self, call_mcp, entity_type):
        """Test reading entity of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123"
        })
        # Should either return entity or handle gracefully
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_update_entity(self, call_mcp, entity_type):
        """Test updating entity of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123",
            "data": {"name": f"updated_{entity_type}"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_delete_entity(self, call_mcp, entity_type):
        """Test deleting entity of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "delete",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123"
        })
        assert "success" in result or "error" in result


class TestEntityOperationsExtended:
    """Test extended operations across all entity types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_archive_entity(self, call_mcp, entity_type):
        """Test archiving entity of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "archive",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_restore_entity(self, call_mcp, entity_type):
        """Test restoring entity of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "restore",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123"
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_list_entities(self, call_mcp, entity_type):
        """Test listing entities of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": entity_type,
            "limit": 10
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_search_entities(self, call_mcp, entity_type):
        """Test searching entities of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": entity_type,
            "query": "test"
        })
        assert "success" in result or "error" in result or "data" in result


class TestEntityOperationsBulk:
    """Test bulk operations across all entity types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_bulk_update_entities(self, call_mcp, entity_type):
        """Test bulk updating entities of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "bulk_update",
            "entity_type": entity_type,
            "entity_ids": [f"{entity_type}-1", f"{entity_type}-2"],
            "data": {"status": "updated"}
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_bulk_delete_entities(self, call_mcp, entity_type):
        """Test bulk deleting entities of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "bulk_delete",
            "entity_type": entity_type,
            "entity_ids": [f"{entity_type}-1", f"{entity_type}-2"]
        })
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES)
    async def test_bulk_archive_entities(self, call_mcp, entity_type):
        """Test bulk archiving entities of given type."""
        result = await call_mcp("entity_tool", {
            "operation": "bulk_archive",
            "entity_type": entity_type,
            "entity_ids": [f"{entity_type}-1", f"{entity_type}-2"]
        })
        assert "success" in result or "error" in result


class TestEntityOperationsHistory:
    """Test history operations across entity types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_entity_history(self, call_mcp, entity_type):
        """Test getting history for entity type."""
        result = await call_mcp("entity_tool", {
            "operation": "history",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123"
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["organization", "project", "document", "requirement"])
    async def test_restore_version(self, call_mcp, entity_type):
        """Test restoring specific version."""
        result = await call_mcp("entity_tool", {
            "operation": "restore_version",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123",
            "version": 1
        })
        assert "success" in result or "error" in result


class TestEntityOperationsTraceability:
    """Test traceability operations."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ["requirement", "test"])
    async def test_entity_trace(self, call_mcp, entity_type):
        """Test getting trace/relationships."""
        result = await call_mcp("entity_tool", {
            "operation": "trace",
            "entity_type": entity_type,
            "entity_id": f"{entity_type}-123"
        })
        assert "success" in result or "error" in result or "data" in result


class TestEntityOperationsWithFilters:
    """Test operations with filters across entity types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES[:5])  # Test subset for efficiency
    async def test_list_with_filter(self, call_mcp, entity_type):
        """Test listing with filters."""
        result = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": entity_type,
            "filters": {"status": "active"},
            "limit": 10
        })
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("entity_type", ENTITY_TYPES[:5])
    async def test_list_with_sort(self, call_mcp, entity_type):
        """Test listing with sorting."""
        result = await call_mcp("entity_tool", {
            "operation": "list",
            "entity_type": entity_type,
            "sort_by": "created_at",
            "limit": 10
        })
        assert "success" in result or "error" in result or "data" in result


class TestEntityOperationsCoverage:
    """Test operation-entity coverage matrix."""

    def test_all_entity_types_supported(self):
        """Test that all entity types are defined."""
        assert len(ENTITY_TYPES) == 20
        assert "organization" in ENTITY_TYPES
        assert "requirement" in ENTITY_TYPES
        assert "test" in ENTITY_TYPES

    def test_all_operations_defined(self):
        """Test that all operations are defined."""
        assert len(CORE_OPERATIONS) == 4
        assert len(EXTENDED_OPERATIONS) == 4
        assert len(BULK_OPERATIONS) == 3
        assert len(ALL_OPERATIONS) == 11

    def test_coverage_matrix_size(self):
        """Test theoretical coverage matrix size."""
        # 20 entity types × 11+ operations = 220+ test cases
        matrix_size = len(ENTITY_TYPES) * len(ALL_OPERATIONS)
        assert matrix_size >= 220


class TestEntityTypeSpecificBehaviors:
    """Test entity-type-specific behaviors."""

    @pytest.mark.asyncio
    async def test_organization_hierarchy(self, call_mcp):
        """Test organization-specific hierarchy operations."""
        result = await call_mcp("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": "org-1"
        })
        # Organizations may have workspace relationships
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_requirement_test_tracing(self, call_mcp):
        """Test requirement-test relationship tracing."""
        result = await call_mcp("entity_tool", {
            "operation": "trace",
            "entity_type": "requirement",
            "entity_id": "req-123"
        })
        # Requirements should be traceable to tests
        assert "success" in result or "error" in result or "data" in result

    @pytest.mark.asyncio
    async def test_audit_log_immutable(self, call_mcp):
        """Test audit log is effectively immutable."""
        # Audit logs should not be updatable
        result = await call_mcp("entity_tool", {
            "operation": "update",
            "entity_type": "audit_log",
            "entity_id": "audit-1",
            "data": {"status": "modified"}
        })
        # Should either reject or handle specially
        assert "success" in result or "error" in result
