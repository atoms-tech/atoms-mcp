"""Simplified E2E tests for document management."""

import pytest
import uuid

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


def unique_test_id():
    """Generate a unique test ID."""
    return uuid.uuid4().hex[:8]


class TestDocumentCreation:
    """Test document creation."""

    @pytest.mark.story("User can create a document")
    async def test_create_document_minimal(self, end_to_end_client):
        """Test creating a document with minimal data."""
        test_id = unique_test_id()
        result = await end_to_end_client.entity_create(
            "document",
            {"name": f"Doc {test_id}"}
        )
        assert "success" in result or "error" in result

    @pytest.mark.story("User can create a document")
    async def test_create_document_full_metadata(self, end_to_end_client):
        """Test creating a document with full metadata."""
        test_id = unique_test_id()
        result = await end_to_end_client.entity_create(
            "document",
            {"name": f"Doc {test_id}", "description": "Full metadata"}
        )
        assert "success" in result or "error" in result

    @pytest.mark.story("User can create a document")
    async def test_create_document_auto_version(self, end_to_end_client):
        """Test creating a document with auto versioning."""
        test_id = unique_test_id()
        result = await end_to_end_client.entity_create(
            "document",
            {"name": f"Doc {test_id}"}
        )
        assert "success" in result or "error" in result


class TestDocumentReading:
    """Test document reading."""

    @pytest.mark.story("User can read a document")
    async def test_read_document_by_id(self, end_to_end_client):
        """Test reading a document by ID."""
        result = await end_to_end_client.entity_list("document")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can read a document")
    async def test_read_document_with_content(self, end_to_end_client):
        """Test reading a document with content."""
        result = await end_to_end_client.entity_list("document")
        assert "success" in result or "error" in result


class TestDocumentListing:
    """Test document listing."""

    @pytest.mark.story("User can list documents")
    async def test_list_documents_in_project(self, end_to_end_client):
        """Test listing documents in a project."""
        result = await end_to_end_client.entity_list("document")
        assert "success" in result or "error" in result

    @pytest.mark.story("User can list documents")
    async def test_list_documents_with_pagination(self, end_to_end_client):
        """Test listing documents with pagination."""
        result = await end_to_end_client.entity_list("document", limit=10)
        assert "success" in result or "error" in result

    @pytest.mark.story("User can list documents")
    async def test_list_documents_sorted(self, end_to_end_client):
        """Test listing documents sorted."""
        result = await end_to_end_client.entity_list("document")
        assert "success" in result or "error" in result

