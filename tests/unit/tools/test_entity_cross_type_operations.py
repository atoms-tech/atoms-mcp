"""Cross-entity type relationship and cascade operations.

Tests operations across multiple entity types and their relationships.
"""

import uuid
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestEntityCrossTypeOperations:
    """Test operations across entity types and hierarchies."""
    
    @pytest.mark.unit
    async def test_cross_entity_relationships(self, call_mcp):
        """Test operations across entity relationships."""
        # Create hierarchy
        org_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": f"Cross Org {uuid.uuid4().hex[:8]}", "type": "team"},
            },
        )
        
        assert org_result.get("success", False) is True
        org_id = org_result["data"]["id"]
        
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {"name": f"Cross Project {uuid.uuid4().hex[:8]}", "organization_id": org_id},
            },
        )
        
        assert project_result.get("success", False) is True
        project_id = project_result["data"]["id"]
        
        document_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {"name": f"Cross Document {uuid.uuid4().hex[:8]}", "project_id": project_id},
            },
        )
        
        assert document_result.get("success", False) is True
        document_id = document_result["data"]["id"]
        
        requirement_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "requirement",
                "data": {"name": f"Cross Requirement {uuid.uuid4().hex[:8]}", "document_id": document_id},
            },
        )
        
        assert requirement_result.get("success", False) is True
        
        test_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "test",
                "data": {"title": f"Cross Test {uuid.uuid4().hex[:8]}", "project_id": project_id},
            },
        )
        
        assert test_result.get("success", False) is True
        
        # List related entities
        projects_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "project",
                "filters": {"organization_id": org_id},
            },
        )
        
        assert projects_result.get("success", False) is True
        assert len(projects_result.get("data", [])) >= 1
        assert projects_result["data"][0]["id"] == project_id
        
        documents_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {"project_id": project_id},
            },
        )
        
        assert documents_result.get("success", False) is True
        assert len(documents_result.get("data", [])) >= 1
        assert documents_result["data"][0]["id"] == document_id
        
        requirements_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "requirement",
                "filters": {"document_id": document_id},
            },
        )
        
        assert requirements_result.get("success", False) is True
        assert len(requirements_result.get("data", [])) >= 1
        assert requirements_result["data"][0]["id"] == requirement_result["data"]["id"]
        
        tests_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "test",
                "filters": {"project_id": project_id},
            },
        )
        
        assert tests_result.get("success", False) is True
        assert len(tests_result.get("data", [])) >= 1
        assert tests_result["data"][0]["id"] == test_result["data"]["id"]
    
    @pytest.mark.unit
    async def test_cascade_operations_across_hierarchy(self, call_mcp):
        """Test archive/restore cascading through entity hierarchy."""
        # Create hierarchy
        org_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "organization",
                "data": {"name": f"Cascade Org {uuid.uuid4().hex[:8]}", "type": "team"},
            },
        )
        
        assert org_result.get("success", False) is True
        org_id = org_result["data"]["id"]
        
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {"name": f"Cascade Project {uuid.uuid4().hex[:8]}", "organization_id": org_id},
            },
        )
        
        assert project_result.get("success", False) is True
        project_id = project_result["data"]["id"]
        
        document_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {"name": f"Cascade Document {uuid.uuid4().hex[:8]}", "project_id": project_id},
            },
        )
        
        assert document_result.get("success", False) is True
        
        # Archive parent
        archive_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "archive",
                "entity_type": "organization",
                "entity_id": org_id,
            },
        )
        
        assert archive_result.get("success", False) is True
        
        # Restore parent
        restore_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "restore",
                "entity_type": "organization",
                "entity_id": org_id,
            },
        )
        
        assert restore_result.get("success", False) is True
        
        # Verify children are still accessible
        projects_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "project",
                "filters": {"organization_id": org_id},
            },
        )
        
        assert projects_result.get("success", False) is True
        assert len(projects_result.get("data", [])) >= 1
        assert projects_result["data"][0]["id"] == project_id
