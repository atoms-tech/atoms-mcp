"""Entity tool tests - Document management.

Tests document-specific operations:
- Create document
- Read document content
- List documents in project

User stories covered:
- User can create a document
- User can view document content
- User can list documents in project

Run with: pytest tests/unit/tools/test_entity_document.py -v
"""

import uuid
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestDocumentCRUD:
    """Test document CRUD operations."""

    @pytest.mark.unit
    async def test_create_document(self, call_mcp, test_organization):
        """User can create a document."""
        # First create a project
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Doc Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        # Create document
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Test Document {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "content": "# Test Document\n\nThis is a test.",
                    "document_type": "markdown",
                },
            },
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Document creation failed"
        assert "id" in data
        assert data.get("project_id") == project_id

    @pytest.mark.unit
    async def test_read_document(self, call_mcp, test_organization):
        """User can view document content."""
        # Create project and document first
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Doc Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        doc_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "document",
                "data": {
                    "name": f"Doc to Read {uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "content": "Test content",
                },
            },
        )

        if hasattr(doc_result, "data"):
            doc_id = doc_result.data.get("data", {}).get("id")
        else:
            doc_id = doc_result.get("data", {}).get("id")

        # Read document
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "read",
                "entity_type": "document",
                "entity_id": doc_id,
            }
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
            data = result.data.get("data", {})
        else:
            success = result.get("success", False)
            data = result.get("data", {})

        assert success, "Document read failed"
        assert data.get("id") == doc_id


class TestDocumentList:
    """Test document listing."""

    @pytest.mark.unit
    async def test_list_documents_by_project(self, call_mcp, test_organization):
        """User can list documents in project."""
        # Create project
        project_result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": f"Doc List Project {uuid.uuid4().hex[:8]}",
                    "organization_id": test_organization,
                },
            },
        )

        if hasattr(project_result, "data"):
            project_id = project_result.data.get("data", {}).get("id")
        else:
            project_id = project_result.get("data", {}).get("id")

        # List documents
        result, _ = await call_mcp(
            "entity_tool",
            {
                "operation": "list",
                "entity_type": "document",
                "filters": {"project_id": project_id}
            }
        )

        # Parse response
        if hasattr(result, "data"):
            success = result.data.get("success", False)
        else:
            success = result.get("success", False)

        assert success, "List documents by project failed"
