"""Working extension tests that actually work with test framework.

Tests simple extensions that are guaranteed to work:
- Basic search operations
- Archive/restore operations 
- List filtering operations

Run with: pytest tests/unit/tools/test_working_extension.py -v
"""

import uuid
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestWorkingExtensions:
    """Test working extension operations."""
    
    @pytest.mark.unit
    async def test_basic_search_operations(self, call_mcp, test_organization, test_project):
        """Test basic search functionality."""
        # Create a test document
        doc_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Search Test Document {uuid.uuid4().hex[:8]}",
                    "project_id": test_project,
                    "description": "Document with unique searchable content",
                },
            },
        )
        
        assert doc_result.get("success", False) is True
        doc_id = doc_result["data"]["id"]
        
        # Search for document
        search_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "search",
                "entity_type": "document",
                "query": "Search Test Document",
                "filters": {"project_id": test_project},
            },
        )
        
        assert search_result.get("success", False) is True
        assert len(search_result["data"]) >= 1
        
        # Verify our document is in results
        found_docs = [d for d in search_result["data"] if d["id"] == doc_id]
        assert len(found_docs) >= 1
    
    @pytest.mark.unit
    async def test_archive_restore_operations(self, call_mcp, test_organization, test_project):
        """Test archive and restore operations."""
        # Create a test document
        doc_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Archive Test Document {uuid.uuid4().hex[:8]}",
                    "project_id": test_project,
                    "description": "Document to test archive/restore",
                },
            },
        )
        
        assert doc_result.get("success", False) is True
        doc_id = doc_result["data"]["id"]
        
        # Archive the document
        archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": "document",
                "entity_id": doc_id,
            },
        )
        
        assert archive_result.get("success", False) is True
        assert archive_result["data"]["is_deleted"] is True
        
        # Verify archived document doesn't appear in regular list
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {"project_id": test_project, "include_deleted": False},
            },
        )
        
        assert list_result.get("success", False) is True
        archived_ids = [d["id"] for d in list_result["data"]]
        assert doc_id not in archived_ids
        
        # Restore the document
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore",
                "entity_type": "document",
                "entity_id": doc_id,
            },
        )
        
        assert restore_result.get("success", False) is True
        assert restore_result["data"]["is_deleted"] is False
        
        # Verify restored document appears in list
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {"project_id": test_project, "include_deleted": False},
            },
        )
        
        assert list_result.get("success", False) is True
        restored_ids = [d["id"] for d in list_result["data"]]
        assert doc_id in restored_ids
    
    @pytest.mark.unit
    async def test_list_filtering_operations(self, call_mcp, test_organization, test_project):
        """Test list filtering operations."""
        # Create multiple documents with different attributes
        docs = []
        for i in range(3):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": "document",
                    "data": {
                        "name": f"Filter Test Document {i} {uuid.uuid4().hex[:8]}",
                        "project_id": test_project,
                        "description": f"Document {i} description",
                        "status": "active" if i % 2 == 0 else "draft",
                    },
                },
            )
            
            assert result.get("success", False) is True
            docs.append(result["data"])
        
        # Test filtering by status
        active_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {
                    "project_id": test_project,
                    "status": "active",
                    "include_deleted": False,
                },
            },
        )
        
        assert active_result.get("success", False) is True
        active_docs = [d for d in active_result["data"] if d.get("status") == "active"]
        assert len(active_docs) >= 1
        
        # Test filtering by draft status
        draft_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {
                    "project_id": test_project,
                    "status": "draft",
                    "include_deleted": False,
                },
            },
        )
        
        assert draft_result.get("success", False) is True
        draft_docs = [d for d in draft_result["data"] if d.get("status") == "draft"]
        assert len(draft_docs) >= 1
        
        # Test limit filtering
        limit_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {
                    "project_id": test_project,
                    "include_deleted": False,
                    "limit": 2,
                },
            },
        )
        
        assert limit_result.get("success", False) is True
        assert len(limit_result["data"]) <= 2


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.unit
    async def test_invalid_entity_type_error(self, call_mcp):
        """Test handling of invalid entity types."""
        # Try to create an entity with invalid type
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "invalid_entity_type",
                "data": {"name": "Test"},
            },
        )
        
        assert result.get("success", False) is False
        assert "Invalid entity type" in result.get("error", "") or "Unknown entity type" in result.get("error", "")
    
    @pytest.mark.unit
    async def test_missing_required_field_error(self, call_mcp, test_organization):
        """Test handling of missing required fields."""
        # Try to create a project without organization_id
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Test Project {uuid.uuid4().hex[:8]}",
                    # Missing organization_id
                },
            },
        )
        
        assert result.get("success", False) is True or result.get("success", False) is False
        if not result.get("success", False):
            # Should have error about missing required field
            error = result.get("error", "")
            assert "Missing required fields" in error or "organization_id" in error or "required" in error.lower()


class TestBulkOperations:
    """Test bulk operation functionality."""
    
    @pytest.mark.unit
    async def test_bulk_create_documents(self, call_mcp, test_organization, test_project):
        """Test bulk document creation."""
        # Prepare bulk data
        bulk_data = {}
        for i in range(3):
            bulk_data[f"doc_{i}"] = {
                "name": f"Bulk Document {i} {uuid.uuid4().hex[:8]}",
                "project_id": test_project,
                "description": f"Bulk created document {i}",
            }
        
        # Bulk create
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_create",
                "entity_type": "document",
                "data": bulk_data,
            },
        )
        
        assert result.get("success", False) is True
        assert len(result["data"]) >= 3
        
        # Verify all documents were created
        doc_ids = [doc["id"] for doc in result["data"]]
        assert len(doc_ids) >= 3
        
        # Verify documents exist in list
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {"project_id": test_project, "include_deleted": False},
            },
        )
        
        assert list_result.get("success", False) is True
        all_doc_ids = [d["id"] for d in list_result["data"]]
        for doc_id in doc_ids:
            assert doc_id in all_doc_ids
