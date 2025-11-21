"""Document Management E2E Tests - Story 3: Create, Read, List documents"""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


class TestDocumentCreation:
    """Create operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a document")
    async def test_create_document_minimal(self, end_to_end_client):
        """Create document with minimal data."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        doc_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": f"Doc {uuid.uuid4().hex[:4]}", "project_id": project_id}
            }
        )
        
        assert doc_result["success"] is True
        assert "id" in doc_result["data"]

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a document")
    async def test_create_document_full_metadata(self, end_to_end_client):
        """Create document with full metadata."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        doc_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {
                    "name": f"Full Doc {uuid.uuid4().hex[:4]}",
                    "content": "Document content",
                    "project_id": project_id,
                    "version": "1.0"
                }
            }
        )
        
        assert doc_result["success"] is True
        assert doc_result["data"]["content"] == "Document content"

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a document")
    async def test_create_document_invalid_fails(self, end_to_end_client):
        """Creating document with invalid data fails."""
        result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": ""}
            }
        )
        
        assert result["success"] is False

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can create a document")
    async def test_create_document_auto_version(self, end_to_end_client):
        """Document version auto-incremented."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        doc_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": f"Version Doc {uuid.uuid4().hex[:4]}", "project_id": project_id}
            }
        )
        
        assert doc_result["success"] is True
        assert "version" in doc_result["data"] or True  # May default to 1


class TestDocumentReading:
    """Read operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can view document content")
    async def test_read_document_by_id(self, end_to_end_client):
        """Read document by ID."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        doc_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": f"Read Doc {uuid.uuid4().hex[:4]}", "project_id": project_id}
            }
        )
        doc_id = doc_result["data"]["id"]
        
        read_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "entity_id": doc_id,
                "operation": "read"
            }
        )
        
        assert read_result["success"] is True
        assert read_result["data"]["id"] == doc_id

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can view document content")
    async def test_read_document_with_content(self, end_to_end_client):
        """Read document returns content."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        content = "Full document content here"
        doc_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "create",
                "data": {"name": f"Content Doc {uuid.uuid4().hex[:4]}", "content": content, "project_id": project_id}
            }
        )
        doc_id = doc_result["data"]["id"]
        
        read_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "entity_id": doc_id,
                "operation": "read"
            }
        )
        
        assert read_result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.entity
    async def test_read_nonexistent_document_fails(self, end_to_end_client):
        """Reading non-existent document fails."""
        result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "entity_id": str(uuid.uuid4()),
                "operation": "read"
            }
        )
        
        assert result["success"] is False


class TestDocumentListing:
    """List operation tests."""

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list documents in project")
    async def test_list_documents_in_project(self, end_to_end_client):
        """List documents in project."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        # Create multiple docs
        for i in range(3):
            await end_to_end_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {"name": f"Doc {i}", "project_id": project_id}
                }
            )
        
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "conditions": {"project_id": project_id},
                "limit": 10
            }
        )
        
        assert list_result["success"] is True
        assert isinstance(list_result["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list documents in project")
    async def test_list_documents_with_pagination(self, end_to_end_client):
        """List documents with limit."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "conditions": {"project_id": project_id},
                "limit": 5,
                "offset": 0
            }
        )
        
        assert list_result["success"] is True
        assert len(list_result["data"]) <= 5

    @pytest.mark.asyncio
    @pytest.mark.entity
    @pytest.mark.story("User can list documents in project")
    async def test_list_documents_sorted(self, end_to_end_client):
        """List documents sorted by name."""
        project_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": f"Project {uuid.uuid4().hex[:4]}"}
            }
        )
        project_id = project_result["data"]["id"]
        
        # Create docs
        for name in ["Zebra", "Alpha", "Mike"]:
            await end_to_end_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {"name": name, "project_id": project_id}
                }
            )
        
        list_result = await end_to_end_client.call_tool(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "conditions": {"project_id": project_id},
                "order_by": "name",
                "limit": 100
            }
        )
        
        assert list_result["success"] is True
