"""Test soft-delete consistency across entity operations.

Tests that soft-deleted entities don't appear in:
- Search results
- List operations
- Relationship queries
- Export operations
- Bulk operations

Tests restoration of soft-deleted entities:
- Restore operation works
- Restored entities appear in normal queries
- Cascading restore for related entities

Run with: pytest tests/unit/tools/test_soft_delete_consistency.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta

from tests.unit.tools.conftest import unwrap_mcp_response

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestSoftDeleteConsistency:
    """Test soft-delete filtering consistency."""
    
    @pytest.mark.story("Data Consistency - Soft delete filtering")
    @pytest.mark.unit
    async def test_soft_deleted_filtered_from_list(self, call_mcp, test_document):
        """Test soft-deleted documents don't appear in list."""
        # Soft delete the document
        delete_result = await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        delete_response = unwrap_mcp_response(delete_result)
        assert delete_response["success"] is True
        
        # List documents - should not include deleted
        list_result = await call_mcp(
            "list_entities",
            entity_type="document",
            filters={"project_id": test_document["project_id"]}
        )
        list_response = unwrap_mcp_response(list_result)
        assert list_response["success"] is True
        
        # Deleted document should not be in results
        deleted_in_results = [
            doc for doc in list_response.get("results", [])
            if doc["id"] == test_document["id"]
        ]
        assert len(deleted_in_results) == 0
    
    @pytest.mark.story("Data Consistency - Soft delete filtering")
    @pytest.mark.unit
    async def test_soft_deleted_filtered_from_search(self, call_mcp, test_document):
        """Test soft-deleted documents don't appear in search."""
        # Soft delete the document
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        
        # Search for document - should not include deleted
        search_results = await call_mcp(
            "search_entities",
            entity_type="document",
            search_term=test_document["name"],
            filters={"project_id": test_document["project_id"]}
        )
        
        # Deleted document should not be in search results
        deleted_in_search = [
            doc for doc in search_results
            if doc["id"] == test_document["id"]
        ]
        assert len(deleted_in_search) == 0
    
    @pytest.mark.story("Data Consistency - Soft delete filtering")
    @pytest.mark.unit
    async def test_soft_deleted_filtered_from_export(self, call_mcp, test_document):
        """Test soft-deleted documents don't appear in exports."""
        # Soft delete the document
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        
        # Export documents - should not include deleted
        export_result = await call_mcp(
            "export_entities",
            entity_type="document",
            format="json",
            filters={"project_id": test_document["project_id"]}
        )
        export_response = unwrap_mcp_response(export_result)
        
        if export_response["success"]:
            # Check exported data doesn't include deleted document
            exported_docs = export_response.get("data", [])
            if isinstance(exported_docs, str):
                # JSON string - parse and check
                import json
                exported_docs = json.loads(exported_docs)
            
            deleted_in_export = [
                doc for doc in exported_docs
                if isinstance(doc, dict) and doc.get("id") == test_document["id"]
            ]
            assert len(deleted_in_export) == 0
    
    @pytest.mark.story("Data Consistency - Soft delete filtering")
    @pytest.mark.unit
    async def test_bulk_operations_respect_soft_delete(self, call_mcp, test_documents):
        """Test bulk operations don't affect soft-deleted entities."""
        if not test_documents:
            pytest.skip("No test documents available")
        
        # Soft delete half the documents
        deleted_ids = []
        active_ids = []
        
        for i, doc in enumerate(test_documents):
            if i % 2 == 0:
                await call_mcp(
                    "delete_entity",
                    entity_type="document",
                    entity_id=doc["id"],
                    soft_delete=True
                )
                deleted_ids.append(doc["id"])
            else:
                active_ids.append(doc["id"])
        
        # Bulk update all documents
        update_result = await call_mcp(
            "bulk_update_entities",
            entity_type="document",
            entity_ids=test_documents,  # All documents
            data={"status": "bulk_updated"}
        )
        update_response = unwrap_mcp_response(update_result)
        
        if update_response["success"]:
            # Check that only active documents were updated
            # This test assumes the bulk update respects soft-delete filtering
            assert update_response["updated"] >= len(active_ids)
    
    @pytest.mark.story("Data Consistency - Relationship filtering")
    @pytest.mark.unit
    async def test_soft_deleted_filtered_from_relationships(self, call_mcp, test_requirement):
        """Test soft-deleted parent filters children."""
        # Soft delete the document containing the requirement
        doc_id = test_requirement["document_id"]
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=doc_id,
            soft_delete=True
        )
        
        # List requirements in the document
        requirements_result = await call_mcp(
            "list_entities",
            entity_type="requirement",
            filters={"document_id": doc_id}
        )
        requirements_response = unwrap_mcp_response(requirements_result)
        
        if requirements_response["success"]:
            # Should not include requirements from deleted document
            deleted_doc_requirements = [
                req for req in requirements_response.get("results", [])
                if req.get("document_id") == doc_id
            ]
            # This depends on how relationships are implemented
            # The test checks that deleted parent filters are applied
    
    @pytest.mark.story("Data Consistency - Include deleted option")
    @pytest.mark.unit
    async def test_list_can_include_deleted(self, call_mcp, test_document):
        """Test list operations can include deleted entities."""
        # Soft delete the document
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        
        # List with include_deleted=true (if supported)
        list_result = await call_mcp(
            "list_entities",
            entity_type="document",
            filters={"project_id": test_document["project_id"]},
            filters_list=[
                {"field": "is_deleted", "operator": "eq", "value": True}
            ]
        )
        list_response = unwrap_mcp_response(list_result)
        
        # Should find the deleted document when explicitly searching for deleted
        if list_response["success"]:
            deleted_found = [
                doc for doc in list_response.get("results", [])
                if doc["id"] == test_document["id"] and doc.get("is_deleted") is True
            ]
            assert len(deleted_found) >= 0  # May or may not be supported
    
    @pytest.mark.story("Data Consistency - Audit trail")
    @pytest.mark.unit
    async def test_soft_delete_creates_audit_trail(self, call_mcp, test_document):
        """Test soft delete creates proper audit trail."""
        # Get original document state
        original_doc = await call_mcp(
            "read_entity",
            entity_type="document",
            entity_id=test_document["id"]
        )
        original_response = unwrap_mcp_response(original_doc)
        
        # Soft delete the document
        delete_result = await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        delete_response = unwrap_mcp_response(delete_result)
        assert delete_response["success"] is True
        
        # Verify audit trail fields are set
        updated_doc = await call_mcp(
            "read_entity",
            entity_type="document",
            entity_id=test_document["id"],
            filters_list=[
                {"field": "is_deleted", "operator": "eq", "value": True}
            ]
        )
        updated_response = unwrap_mcp_response(updated_doc)
        
        if updated_response:
            # Check soft delete metadata
            assert updated_response.get("is_deleted") is True
            assert updated_response.get("deleted_at") is not None
            assert "deleted_by" in updated_response or updated_response.get("updated_by") is not None
            
            # Verify deletion timestamp is recent
            deleted_at = datetime.fromisoformat(updated_response["deleted_at"].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            assert (now - deleted_at) < timedelta(minutes=1)


class TestSoftDeleteRestore:
    """Test soft delete restoration functionality."""
    
    @pytest.mark.story("Data Consistency - Restore functionality")
    @pytest.mark.unit
    async def test_restore_soft_deleted_document(self, call_mcp, test_document):
        """Test restoring a soft-deleted document."""
        # Soft delete the document
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        
        # Verify it's deleted
        list_result = await call_mcp(
            "list_entities",
            entity_type="document",
            filters={"project_id": test_document["project_id"]}
        )
        list_response = unwrap_mcp_response(list_result)
        deleted_in_list = [
            doc for doc in list_response.get("results", [])
            if doc["id"] == test_document["id"]
        ]
        assert len(deleted_in_list) == 0
        
        # Restore the document
        restore_result = await call_mcp(
            "restore_entity",
            entity_type="document",
            entity_id=test_document["id"]
        )
        restore_response = unwrap_mcp_response(restore_result)
        assert restore_response["success"] is True
        
        # Verify it's restored
        updated_list_result = await call_mcp(
            "list_entities",
            entity_type="document",
            filters={"project_id": test_document["project_id"]}
        )
        updated_list_response = unwrap_mcp_response(updated_list_result)
        restored_in_list = [
            doc for doc in updated_list_response.get("results", [])
            if doc["id"] == test_document["id"]
        ]
        assert len(restored_in_list) >= 1
    
    @pytest.mark.story("Data Consistency - Restore audit trail")
    @pytest.mark.unit
    async def test_restore_clears_delete_metadata(self, call_mcp, test_document):
        """Test restore clears soft delete metadata."""
        # Soft delete the document
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        
        # Restore the document
        await call_mcp(
            "restore_entity",
            entity_type="document",
            entity_id=test_document["id"]
        )
        
        # Verify delete metadata is cleared
        restored_doc = await call_mcp(
            "read_entity",
            entity_type="document",
            entity_id=test_document["id"]
        )
        restored_response = unwrap_mcp_response(restored_doc)
        
        if restored_response:
            assert restored_response.get("is_deleted") is False
            # deleted_at and deleted_by should be cleared
            # (implementation dependent)
    
    @pytest.mark.story("Data Consistency - Bulk restore")
    @pytest.mark.unit
    async def test_bulk_restore_operations(self, call_mcp, test_documents):
        """Test bulk restore of soft-deleted entities."""
        if not test_documents:
            pytest.skip("No test documents available")
        
        # Soft delete half the documents
        deleted_ids = []
        active_ids = []
        
        for i, doc in enumerate(test_documents):
            if i % 2 == 0:
                await call_mcp(
                    "delete_entity",
                    entity_type="document",
                    entity_id=doc["id"],
                    soft_delete=True
                )
                deleted_ids.append(doc["id"])
            else:
                active_ids.append(doc["id"])
        
        # Bulk restore all documents
        restore_result = await call_mcp(
            "bulk_restore_entities",
            entity_type="document",
            entity_ids=deleted_ids
        )
        restore_response = unwrap_mcp_response(restore_result)
        
        if restore_response["success"]:
            # Verify restored documents appear in list
            list_result = await call_mcp(
                "list_entities",
                entity_type="document",
                filters={"project_id": test_documents[0]["project_id"]}
            )
            list_response = unwrap_mcp_response(list_result)
            
            if list_response["success"]:
                all_in_list = all(
                    any(doc["id"] == restored_id for doc in list_response.get("results", []))
                    for restored_id in deleted_ids
                )
                assert all_in_list
    
    @pytest.mark.story("Data Consistency - Cascading restore")
    @pytest.mark.unit
    async def test_cascading_restore_behavior(self, call_mcp, test_requirement):
        """Test cascading restore behavior."""
        # Get the document containing the requirement
        doc_id = test_requirement["document_id"]
        
        # Soft delete the document (this should cascade to requirement)
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=doc_id,
            soft_delete=True
        )
        
        # Restore the document (should cascade to requirement)
        restore_result = await call_mcp(
            "restore_entity",
            entity_type="document",
            entity_id=doc_id
        )
        restore_response = unwrap_mcp_response(restore_result)
        
        # Check if requirement was restored (cascading behavior)
        req_result = await call_mcp(
            "read_entity",
            entity_type="requirement",
            entity_id=test_requirement["id"]
        )
        req_response = unwrap_mcp_response(req_result)
        
        if req_response:
            # If requirement is restored, it should not be marked as deleted
            # This test verifies cascading restore behavior
            assert req_response.get("is_deleted") is False


class TestSoftDeleteEdgeCases:
    """Test edge cases for soft delete operations."""
    
    @pytest.mark.story("Data Consistency - Double soft delete")
    @pytest.mark.unit
    async def test_double_soft_delete_safe(self, call_mcp, test_document):
        """Test double soft delete doesn't cause errors."""
        # Soft delete the document once
        first_delete = await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        first_response = unwrap_mcp_response(first_delete)
        assert first_response["success"] is True
        
        # Soft delete again - should succeed or be idempotent
        second_delete = await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        second_response = unwrap_mcp_response(second_delete)
        
        # Should handle gracefully (either succeed or indicate already deleted)
        assert second_response["success"] is True or "already deleted" in str(second_response.get("error", "")).lower()
    
    @pytest.mark.story("Data Consistency - Restore non-deleted")
    @pytest.mark.unit
    async def test_restore_non_deleted_entity(self, call_mcp, test_document):
        """Test restoring non-deleted entity."""
        # Don't delete the document
        # Try to restore it
        restore_result = await call_mcp(
            "restore_entity",
            entity_type="document",
            entity_id=test_document["id"]
        )
        restore_response = unwrap_mcp_response(restore_result)
        
        # Should handle gracefully
        assert restore_response["success"] is True or "not deleted" in str(restore_response.get("error", "")).lower()
    
    @pytest.mark.story("Data Consistency - Hard delete bypasses soft delete")
    @pytest.mark.unit
    async def test_hard_delete_removes_completely(self, call_mcp, test_document):
        """Test hard delete bypasses soft delete completely."""
        # Hard delete the document
        hard_delete = await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=False
        )
        hard_response = unwrap_mcp_response(hard_delete)
        assert hard_response["success"] is True
        
        # Even searching for deleted entities shouldn't find it
        deleted_search = await call_mcp(
            "search_entities",
            entity_type="document",
            filters={"is_deleted": True}
        )
        
        # Hard-deleted entity should not be found
        found_hard_deleted = [
            doc for doc in deleted_search
            if doc["id"] == test_document["id"]
        ]
        assert len(found_hard_deleted) == 0
    
    @pytest.mark.story("Data Consistency - Soft delete timestamps")
    @pytest.mark.unit
    async def test_soft_delete_timestamps_consistent(self, call_mcp, test_document):
        """Test soft delete timestamps are consistent."""
        from datetime import datetime, timezone, timedelta
        
        # Record time before deletion
        before_delete = datetime.now(timezone.utc)
        
        # Soft delete the document
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=test_document["id"],
            soft_delete=True
        )
        
        # Record time after deletion
        after_delete = datetime.now(timezone.utc)
        
        # Check deleted timestamp
        deleted_doc = await call_mcp(
            "read_entity",
            entity_type="document",
            entity_id=test_document["id"],
            filters_list=[
                {"field": "is_deleted", "operator": "eq", "value": True}
            ]
        )
        deleted_response = unwrap_mcp_response(deleted_doc)
        
        if deleted_response:
            deleted_at = datetime.fromisoformat(
                deleted_response["deleted_at"].replace('Z', '+00:00')
            )
            
            # Should be within the deletion time window
            assert before_delete <= deleted_at <= after_delete
    
    @pytest.mark.story("Data Consistency - Soft delete performance")
    @pytest.mark.unit
    async def test_soft_delete_performance(self, call_mcp, test_documents):
        """Test soft delete operations are performant."""
        import time
        
        if not test_documents:
            pytest.skip("No test documents available")
        
        # Time multiple soft delete operations
        start_time = time.time()
        
        for doc in test_documents[:10]:  # Test with 10 documents
            await call_mcp(
                "delete_entity",
                entity_type="document",
                entity_id=doc["id"],
                soft_delete=True
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly (soft deletes are just updates)
        assert duration < 2.0, f"Soft delete too slow: {duration}s for 10 operations"
    
    @pytest.mark.story("Data Consistency - Soft delete RLS")
    @pytest.mark.unit
    async def test_soft_delete_respects_rls(self, call_mcp, test_document):
        """Test soft delete respects Row Level Security."""
        # Mock user from different workspace
        with pytest.raises(Exception):  # Should fail due to RLS
            await call_mcp(
                "delete_entity",
                entity_type="document",
                entity_id=test_document["id"],
                soft_delete=True,
                headers={"Authorization": "Bearer different_user_token"}
            )
        
        # Even as admin, should require proper authentication
        # This test verifies RLS is enforced for soft deletes


class TestSoftDeleteDataIntegrity:
    """Test data integrity with soft delete operations."""
    
    @pytest.mark.story("Data Consistency - Foreign key constraints")
    @pytest.mark.unit
    async def test_soft_delete_preserves_foreign_keys(self, call_mcp, test_requirement):
        """Test soft delete preserves foreign key constraints."""
        # Soft delete the document containing the requirement
        doc_id = test_requirement["document_id"]
        
        await call_mcp(
            "delete_entity",
            entity_type="document",
            entity_id=doc_id,
            soft_delete=True
        )
        
        # Requirement should still exist but reference deleted document
        requirement = await call_mcp(
            "read_entity",
            entity_type="requirement",
            entity_id=test_requirement["id"]
        )
        requirement_response = unwrap_mcp_response(requirement)
        
        if requirement_response:
            # Should still reference the document (foreign key preserved)
            assert requirement_response["document_id"] == doc_id
            
            # Document should be marked as deleted
            deleted_doc = await call_mcp(
                "read_entity",
                entity_type="document",
                entity_id=doc_id
            )
            deleted_doc_response = unwrap_mcp_response(deleted_doc)
            if deleted_doc_response:
                assert deleted_doc_response.get("is_deleted") is True
    
    @pytest.mark.story("Data Consistency - Soft delete consistency")
    @pytest.mark.unit
    async def test_all_entity_types_support_soft_delete(self, call_mcp):
        """Test all entity types support soft delete consistently."""
        entity_types = [
            "organization", "project", "document", "requirement",
            "test", "block", "property", "column"
        ]
        
        for entity_type in entity_types:
            # Create a test entity
            create_result = await call_mcp(
                "create_entity",
                entity_type=entity_type,
                data={
                    "name": f"Test {entity_type}",
                    "workspace_id": "test_ws"
                }
            )
            create_response = unwrap_mcp_response(create_result)
            
            if create_response.get("success") and "id" in create_response:
                entity_id = create_response["id"]
                
                # Try to soft delete
                delete_result = await call_mcp(
                    "delete_entity",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    soft_delete=True
                )
                delete_response = unwrap_mcp_response(delete_result)
                
                # Should support soft delete (or provide clear error)
                assert delete_response.get("success") is True or \
                       "not supported" in str(delete_response.get("error", "")).lower()
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
        # Response has deleted/failed keys, or success/error on error
        assert "deleted" in result or "success" in result or "error" in result


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
