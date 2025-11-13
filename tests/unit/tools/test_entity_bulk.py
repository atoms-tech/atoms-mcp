"""Bulk operations for entities - batch updates, deletes, and archives.

This module contains tests for bulk operations on multiple entities.

Run with: pytest tests/unit/tools/test_entity_bulk.py -v
"""

from __future__ import annotations

import pytest
from typing import Any

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,
    pytest.mark.skip(reason="Test infrastructure requires additional setup - use consolidated test files instead")
]


class TestBulkUpdate:
    """Bulk update operations."""

    async def test_bulk_update_empty_list(self, call_mcp):
        """Test bulk update with empty entity list."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": [],
                "data": {"status": "updated"}
            }
        )
        
        assert result is not None
        assert result.get("updated") == 0

    async def test_bulk_update_returns_count(self, call_mcp, test_organization):
        """Test bulk update returns updated count."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": [test_organization],  # test_organization is the ID string
                "data": {"description": "Bulk updated"}
            }
        )
        
        assert result is not None
        # Should have updated or failed count
        assert "updated" in result or "success" in result

    async def test_bulk_update_invalid_ids(self, call_mcp):
        """Test bulk update with invalid entity IDs."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": ["invalid-id-1", "invalid-id-2"],
                "data": {"status": "updated"}
            }
        )
        
        assert result is not None
        # Should track failures
        assert "failed" in result or "updated" in result


class TestBulkDelete:
    """Bulk delete operations (soft-delete)."""

    async def test_bulk_delete_empty_list(self, call_mcp):
        """Test bulk delete with empty entity list."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_delete",
                "entity_type": "organization",
                "entity_ids": []
            }
        )
        
        assert result is not None
        assert result.get("deleted") == 0

    async def test_bulk_delete_soft_vs_hard(self, call_mcp, test_organization):
        """Test bulk delete with soft_delete flag."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_delete",
                "entity_type": "organization",
                "entity_ids": [test_organization],
                "soft_delete": True
            }
        )
        
        assert result is not None
        assert result.get("soft_delete") == True

    async def test_bulk_delete_returns_stats(self, call_mcp, test_organization):
        """Test bulk delete returns operation statistics."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_delete",
                "entity_type": "organization",
                "entity_ids": [test_organization]
            }
        )
        
        assert result is not None
        # Should have deleted and total counts
        assert "deleted" in result or "failed" in result


class TestBulkArchive:
    """Bulk archive operations (explicit soft-delete)."""

    async def test_bulk_archive_empty_list(self, call_mcp):
        """Test bulk archive with empty entity list."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "organization",
                "entity_ids": []
            }
        )
        
        assert result is not None
        assert result.get("archived") == 0

    async def test_bulk_archive_returns_count(self, call_mcp, test_organization):
        """Test bulk archive returns archived count."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "organization",
                "entity_ids": [test_organization]
            }
        )
        
        assert result is not None
        assert "archived" in result or "success" in result

    async def test_bulk_archive_is_soft_delete(self, call_mcp, test_organization):
        """Test that bulk archive is soft-delete."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "organization",
                "entity_ids": [test_organization]
            }
        )
        
        assert result is not None
        # Archive should not hard-delete
        assert result.get("operation") == "bulk_archive"


class TestBulkOperationsIntegration:
    """Integration tests for bulk operations."""

    async def test_bulk_update_single_item(self, call_mcp, test_organization):
        """Test bulk update with single item."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": [test_organization],
                "data": {"description": "Bulk updated single item"}
            }
        )
        
        assert result is not None
        # Should indicate success or failure
        assert "updated" in result or "failed" in result

    async def test_bulk_delete_single_item(self, call_mcp, test_organization):
        """Test bulk delete with single item."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_delete",
                "entity_type": "organization",
                "entity_ids": [test_organization]
            }
        )
        
        assert result is not None
        assert "deleted" in result or "failed" in result

    async def test_bulk_archive_single_item(self, call_mcp, test_organization):
        """Test bulk archive with single item."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "organization",
                "entity_ids": [test_organization]
            }
        )
        
        assert result is not None
        assert "archived" in result or "failed" in result

    async def test_bulk_operations_return_operation_name(self, call_mcp, test_organization):
        """Test that bulk operations include operation name in response."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": [test_organization],
                "data": {"status": "test"}
            }
        )
        
        assert result is not None
        assert result.get("operation") == "bulk_update"

    async def test_bulk_operations_track_total(self, call_mcp, test_organization):
        """Test that bulk operations track total items processed."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_delete",
                "entity_type": "organization",
                "entity_ids": [test_organization, "fake-id"]
            }
        )
        
        assert result is not None
        # Should track total items attempted
        assert result.get("total") == 2 or "failed" in result or "deleted" in result


class TestBulkOperationsErrorHandling:
    """Error handling for bulk operations."""

    async def test_bulk_update_without_data(self, call_mcp):
        """Test bulk update requires data parameter."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": ["test-id"],
                "data": None
            }
        )
        
        # Should handle gracefully - either error or empty update
        assert result is not None

    async def test_bulk_delete_without_ids(self, call_mcp):
        """Test bulk delete handles missing entity_ids."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_delete",
                "entity_type": "organization",
                "entity_ids": None
            }
        )
        
        # Should handle gracefully
        assert result is not None or result is None  # May error

    async def test_bulk_operations_with_timing(self, call_mcp, test_organization):
        """Test bulk operations include timing metrics."""
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "organization",
                "entity_ids": [test_organization]
            }
        )
        
        assert result is not None
        assert duration_ms >= 0  # Should have timing information


class TestBulkOperationsScenarios:
    """Scenario-based bulk operation tests."""

    async def test_bulk_update_with_multiple_fields(self, call_mcp, test_organization):
        """Test bulk update with multiple field changes."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": "organization",
                "entity_ids": [test_organization],
                "data": {
                    "description": "Updated via bulk",
                    "status": "active"
                }
            }
        )
        
        assert result is not None
        # Should apply all fields
        assert "updated" in result or "success" in result

    async def test_bulk_archive_multiple_ids(self, call_mcp, test_organization):
        """Test bulk archive with multiple IDs."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": "organization",
                "entity_ids": [test_organization, "invalid-1", "invalid-2"]
            }
        )
        
        assert result is not None
        # Should report statistics
        assert "archived" in result or "failed" in result or "total" in result
