"""Parametrized entity tests across all entity types.

Tests archive/restore, bulk operations, search, history, and filtering
for all entity types using parametrization to avoid duplication.
"""

import uuid
import asyncio
import pytest
from datetime import datetime, timezone, timedelta

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestEntityParametrizedOperations:
    """Parametrized operations across all entity types."""
    
    @pytest.fixture(params=[
        "project", "document", "requirement", "test", "user", "profile"
    ])
    def entity_type(self, request):
        """Parametrized entity types for comprehensive testing."""
        return request.param
    
    @pytest.mark.unit
    async def test_archive_restore_operations(self, call_mcp, test_organization, entity_type):
        """Archive and restore operations for all entity types."""
        org_id = test_organization
        project_id = await self._create_test_project(call_mcp, org_id)
        document_id = await self._create_test_document(call_mcp, project_id)
        
        parent_id, test_data = await self._get_test_data_for_entity(
            entity_type, org_id, project_id, document_id
        )
        
        # Create entity
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": entity_type,
                "data": test_data,
            },
        )
        
        assert create_result.get("success", False) is True
        entity_id = create_result["data"]["id"]
        
        # Archive
        archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": entity_type,
                "entity_id": entity_id,
            },
        )
        
        assert archive_result.get("success", False) is True
        assert archive_result["data"]["is_deleted"] is True
        
        # List should not include archived
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": entity_type,
                "filters": {"include_deleted": False},
            },
        )
        
        archived_ids = [e["id"] for e in list_result.get("data", [])]
        assert entity_id not in archived_ids
        
        # Restore
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore",
                "entity_type": entity_type,
                "entity_id": entity_id,
            },
        )
        
        assert restore_result.get("success", False) is True
        assert restore_result["data"]["is_deleted"] is False
    
    @pytest.mark.unit
    async def test_bulk_operations(self, call_mcp, test_organization, entity_type):
        """Bulk create, update, archive operations."""
        org_id = test_organization
        project_id = await self._create_test_project(call_mcp, org_id)
        document_id = await self._create_test_document(call_mcp, project_id)
        
        bulk_data = await self._prepare_bulk_data_for_entity(
            entity_type, org_id, project_id, document_id, count=3
        )
        
        # Bulk create
        bulk_create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_create",
                "entity_type": entity_type,
                "data": bulk_data,
            },
        )
        
        assert bulk_create_result.get("success", False) is True
        assert len(bulk_create_result.get("data", [])) == 3
        
        created_ids = [e["id"] for e in bulk_create_result.get("data", [])]
        
        # Bulk update
        update_data = {
            entity_id: {"updated_field": f"bulk_updated_{uuid.uuid4().hex[:8]}"}
            for entity_id in created_ids[:2]
        }
        
        bulk_update_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_update",
                "entity_type": entity_type,
                "data": update_data,
            },
        )
        
        assert bulk_update_result.get("success", False) is True
        assert len(bulk_update_result.get("data", [])) == 2
        
        # Bulk archive
        bulk_archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "bulk_archive",
                "entity_type": entity_type,
                "entity_ids": created_ids[:2],
            },
        )
        
        assert bulk_archive_result.get("success", False) is True
        assert len(bulk_archive_result.get("data", [])) == 2
    
    @pytest.mark.unit
    async def test_search_operations(self, call_mcp, test_organization, entity_type):
        """Search operations for all entity types."""
        org_id = test_organization
        project_id = await self._create_test_project(call_mcp, org_id)
        document_id = await self._create_test_document(call_mcp, project_id)
        
        parent_id, test_data = await self._get_test_data_for_entity(
            entity_type, org_id, project_id, document_id
        )
        
        search_terms = ["unique_term_alpha", "unique_term_beta", "unique_term_gamma"]
        
        for term in search_terms:
            data = test_data.copy()
            self._add_search_term_to_data(data, entity_type, term)
            
            create_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": entity_type,
                    "data": data,
                },
            )
            
            assert create_result.get("success", False) is True
        
        # Search for each term
        for term in search_terms:
            search_result, _ = await call_mcp(
                "entity_tool",
                {
                    "operation": "search",
                    "entity_type": entity_type,
                    "query": term,
                },
            )
            
            assert search_result.get("success", False) is True
            assert len(search_result.get("data", [])) >= 1
    
    @pytest.mark.unit
    async def test_history_operations(self, call_mcp, test_organization, entity_type):
        """History and version operations for all entity types."""
        org_id = test_organization
        project_id = await self._create_test_project(call_mcp, org_id)
        document_id = await self._create_test_document(call_mcp, project_id)
        
        parent_id, test_data = await self._get_test_data_for_entity(
            entity_type, org_id, project_id, document_id
        )
        
        create_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": entity_type,
                "data": test_data,
            },
        )
        
        assert create_result.get("success", False) is True
        entity_id = create_result["data"]["id"]
        
        # Create updates
        for i in range(3):
            update_data = {"description": f"Update {i} - {datetime.now().isoformat()}"}
            await call_mcp(
                "entity_tool",
                {
                    "operation": "update",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "data": update_data,
                },
            )
            await asyncio.sleep(0.01)
        
        # Get history
        history_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "history",
                "entity_type": entity_type,
                "entity_id": entity_id,
            },
        )
        
        assert history_result.get("success", False) is True
        assert len(history_result.get("data", [])) >= 4
    
    @pytest.mark.unit
    async def test_filter_operations(self, call_mcp, test_organization, entity_type):
        """Filter operations for all entity types."""
        org_id = test_organization
        project_id = await self._create_test_project(call_mcp, org_id)
        document_id = await self._create_test_document(call_mcp, project_id)
        
        # Create entities with different properties
        for i in range(5):
            parent_id, test_data = await self._get_test_data_for_entity(
                entity_type, org_id, project_id, document_id
            )
            self._add_filter_properties(test_data, entity_type, i)
            
            await call_mcp(
                "entity_tool",
                {
                    "operation": "create",
                    "entity_type": entity_type,
                    "data": test_data,
                },
            )
        
        # Test basic filtering
        list_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": entity_type,
                "filters": {"limit": 3},
            },
        )
        
        assert list_result.get("success", False) is True
        assert len(list_result.get("data", [])) <= 3
    
    # Helper methods
    
    async def _create_test_project(self, call_mcp, org_id):
        """Create a test project."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Test Project {uuid.uuid4().hex[:8]}",
                    "organization_id": org_id,
                },
            },
        )
        assert result.get("success", False) is True
        return result["data"]["id"]
    
    async def _create_test_document(self, call_mcp, project_id):
        """Create a test document."""
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Test Document {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                },
            },
        )
        assert result.get("success", False) is True
        return result["data"]["id"]
    
    async def _get_test_data_for_entity(self, entity_type, org_id, project_id, document_id):
        """Get test data for entity type."""
        if entity_type == "organization":
            return None, {"name": f"Test Org {uuid.uuid4().hex[:8]}", "type": "team"}
        elif entity_type == "project":
            return org_id, {"name": f"Test Project {uuid.uuid4().hex[:8]}", "organization_id": org_id}
        elif entity_type == "document":
            return project_id, {"name": f"Test Document {uuid.uuid4().hex[:8]}", "project_id": project_id}
        elif entity_type == "requirement":
            return document_id, {"name": f"Test Requirement {uuid.uuid4().hex[:8]}", "document_id": document_id}
        elif entity_type == "test":
            return project_id, {"title": f"Test Case {uuid.uuid4().hex[:8]}", "project_id": project_id}
        elif entity_type == "user":
            return None, {"email": f"test_{uuid.uuid4().hex[:8]}@example.com"}
        elif entity_type == "profile":
            return None, {"display_name": f"Profile {uuid.uuid4().hex[:8]}"}
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
    
    async def _prepare_bulk_data_for_entity(self, entity_type, org_id, project_id, document_id, count):
        """Prepare bulk data."""
        bulk_data = {}
        for i in range(count):
            parent_id, test_data = await self._get_test_data_for_entity(
                entity_type, org_id, project_id, document_id
            )
            bulk_data[f"bulk_{i}"] = test_data
        return bulk_data
    
    def _add_search_term_to_data(self, data, entity_type, term):
        """Add searchable term to entity data."""
        if entity_type in ["organization", "project", "document", "requirement"]:
            data["name"] = f"{data.get('name', 'Entity')} {term}"
        elif entity_type == "test":
            data["title"] = f"{data.get('title', 'Test')} {term}"
        elif entity_type == "user":
            data["display_name"] = f"User {term}"
        elif entity_type == "profile":
            data["display_name"] = f"Profile {term}"
    
    def _add_filter_properties(self, data, entity_type, index):
        """Add filterable properties."""
        if entity_type == "organization":
            data["type"] = "team" if index % 2 == 0 else "company"
            data["is_active"] = index % 2 == 0
        elif entity_type == "project":
            data["status"] = "active" if index % 2 == 0 else "archived"
        elif entity_type == "document":
            data["type"] = "spec" if index % 2 == 0 else "design"
        elif entity_type == "requirement":
            data["priority"] = "high" if index % 2 == 0 else "medium"
        elif entity_type == "test":
            data["status"] = "pending" if index % 2 == 0 else "completed"
        elif entity_type == "user":
            data["is_active"] = index % 2 == 0
        elif entity_type == "profile":
            data["visibility"] = "public" if index % 3 == 0 else "private"
