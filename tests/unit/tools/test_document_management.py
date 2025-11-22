"""Simplified document management tests.

Tests core document CRUD operations without non-existent fields.
"""

import pytest
import uuid


class TestDocumentManagement:
    """Test document management scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_document_minimal(self, call_mcp):
        """Create document with minimal required data."""
        # Create organization and project
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]
        
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        project_id = project_result["data"]["id"]
        
        # Create document
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": project_id}}
        )
        
        assert result["success"] is True
        assert result["data"]["name"]
        assert result["data"]["project_id"] == project_id
    
    @pytest.mark.asyncio
    async def test_create_document_with_content(self, call_mcp):
        """Create document with content."""
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]
        
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        project_id = project_result["data"]["id"]
        
        content = "# Test Document\n\nThis is test content."
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "content": content, "project_id": project_id}}
        )
        
        assert result["success"] is True
        assert result["data"]["content"] == content
    
    @pytest.mark.asyncio
    async def test_get_document(self, call_mcp):
        """Retrieve document by ID."""
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]
        
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        project_id = project_result["data"]["id"]
        
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": project_id}}
        )
        doc_id = create_result["data"]["id"]
        
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "read", "entity_id": doc_id}
        )
        
        assert result["success"] is True
        assert result["data"]["id"] == doc_id
    
    @pytest.mark.asyncio
    async def test_update_document(self, call_mcp):
        """Update document."""
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {uuid.uuid4().hex[:8]}"}}
        )
        org_id = org_result["data"]["id"]
        
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": {"name": f"Proj {uuid.uuid4().hex[:8]}", "organization_id": org_id}}
        )
        project_id = project_result["data"]["id"]
        
        create_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": {"name": f"Doc {uuid.uuid4().hex[:8]}", "project_id": project_id}}
        )
        doc_id = create_result["data"]["id"]
        
        new_name = f"Updated {uuid.uuid4().hex[:8]}"
        result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "update", "entity_id": doc_id, "data": {"name": new_name}}
        )
        
        assert result["success"] is True
        assert result["data"]["name"] == new_name

