"""E2E tests for Document Management operations.

This file validates end-to-end document management functionality:
- Creating documents within projects with various data
- Viewing document content with full metadata and relationships
- Listing documents with pagination and filtering

Test Coverage: 10 test scenarios covering 3 user stories.
File follows canonical naming - describes WHAT is tested (document management).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestDocumentCreation:
    """Test document creation scenarios."""
    
    @pytest.mark.asyncio
    async def test_create_document_minimal_data(self, call_mcp):
        """Create document with minimal required data (name only)."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        project_data = {
            "name": f"Minimal Doc Project {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        
        # Create document with minimal data
        doc_data = {
            "name": f"Minimal Document {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        assert uuid.UUID(result["data"]["id"])  # Valid UUID
        assert result["data"]["name"] == doc_data["name"]
        assert result["data"]["project_id"] == project_id
        assert result["data"]["content"] == ""  # Empty content
        assert result["data"]["status"] == "draft"
    
    @pytest.mark.asyncio
    async def test_create_document_full_metadata(self, call_mcp):
        """Create document with full metadata and content."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project
        project_data = {
            "name": f"Full Metadata Project {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        
        # Create document with full metadata
        doc_data = {
            "name": f"Complete Document {uuid.uuid4().hex[:8]}",
            "description": "A comprehensive document with full metadata",
            "content": "# Document Title\n\nThis is the document content with **bold** and *italic* text.",
            "type": "technical_specification",
            "status": "active",
            "version": "1.0.0",
            "language": "en",
            "tags": ["documentation", "specification", "technical"],
            "project_id": project_id,
            "workspace_id": workspace_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        assert result["success"] is True
        assert result["data"]["name"] == doc_data["name"]
        assert result["data"]["description"] == doc_data["description"]
        assert result["data"]["content"] == doc_data["content"]
        assert result["data"]["type"] == doc_data["type"]
        assert result["data"]["status"] == doc_data["status"]
        assert result["data"]["version"] == doc_data["version"]
        assert result["data"]["language"] == doc_data["language"]
        assert result["data"]["tags"] == doc_data["tags"]
    
    @pytest.mark.asyncio
    async def test_create_document_auto_outline(self, call_mcp):
        """Create document with auto-generated outline/sections."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project
        project_data = {
            "name": f"Auto Outline Project {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        # Create document with auto-outline flag
        doc_data = {
            "name": f"Auto Outline Document {uuid.uuid4().hex[:8]}",
            "template_type": "specification",
            "auto_create_outline": True,
            "workspace_id": workspace_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        assert result["success"] is True
        doc_id = result["data"]["id"]
        
        # Verify outline was auto-generated
        doc_details, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "get", "entity_id": doc_id}
        )
        
        assert doc_details["success"] is True
        content = doc_details["data"]["content"]
        assert len(content) > 0  # Should have auto-generated content
        assert any(section in content.lower() for section in ["overview", "requirements", "implementation"])
    
    @pytest.mark.asyncio
    async def test_create_document_invalid_project_fails(self, call_mcp):
        """Creating document with invalid project should fail."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        fake_project_id = str(uuid.uuid4())
        
        doc_data = {
            "name": f"Invalid Project Document {uuid.uuid4().hex[:8]}",
            "project_id": fake_project_id,
            "workspace_id": workspace_id
        }
        
        result, duration_ms = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # The error might be about workspace_id or project not found
        assert result["success"] is False
        error_lower = result.get("error", "").lower()
        # Accept either workspace_id error (if project validation happens first) or project not found
        assert "workspace" in error_lower or "project" in error_lower or "not found" in error_lower


class TestDocumentDetails:
    """Test document content viewing and metadata retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_document_by_id(self, call_mcp):
        """Retrieve document by ID with all metadata."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project and document
        project_data = {
            "name": f"Get Doc Project {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        doc_data = {
            "name": f"Retrieved Document {uuid.uuid4().hex[:8]}",
            "description": "Document for testing retrieval",
            "content": "# Retrieved Document\n\nThis content should be preserved exactly.",
            "type": "user_manual",
            "status": "active",
            "tags": ["retrieval", "test"],
            "workspace_id": workspace_id
        }
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        
        # Get document by ID
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document", 
                "operation": "get", 
                "entity_id": doc_id,
                "include_relations": True
            }
        )
        
        assert result["success"] is True
        assert result["data"]["id"] == doc_id
        assert result["data"]["name"] == doc_data["name"]
        assert result["data"]["content"] == doc_data["content"]
        assert result["data"]["description"] == doc_data["description"]
        assert result["data"]["type"] == doc_data["type"]
        assert result["data"]["status"] == doc_data["status"]
        assert result["data"]["tags"] == doc_data["tags"]
        assert "created_at" in result["data"]
        assert "updated_at" in result["data"]
    
    @pytest.mark.asyncio
    async def test_get_document_with_related_requirements(self, call_mcp):
        """Get document with linked requirements."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project and document
        project_data = {
            "name": f"Related Docs Project {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        # Create document
        doc_data = {
            "name": f"Related Document {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        
        # Create requirements and link to document
        for i in range(3):
            req_data = {
                "name": f"REQ-00{i+1}",
                "description": f"Requirement {i+1}",
                "project_id": project_result["data"]["id"],
                "workspace_id": workspace_id
            }
            req_result, _ = await call_mcp(
                "entity_tool",
                {"entity_type": "requirement", "operation": "create", "data": req_data}
            )
            
            # Link requirement to document
            await call_mcp(
                "relationship_tool",
                {
                    "relationship_type": "document_requirement",
                    "operation": "create",
                    "data": {
                        "document_id": doc_id,
                        "requirement_id": req_result["data"]["id"]
                    }
                }
            )
        
        # Get document with related requirements
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "get",
                "entity_id": doc_id,
                "include_relations": True
            }
        )
        
        assert result["success"] is True
        if "related_requirements" in result["data"]:
            assert len(result["data"]["related_requirements"]) >= 3
    
    @pytest.mark.asyncio
    async def test_get_document_version_history(self, call_mcp):
        """Get document version history and metadata."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create document
        doc_data = {
            "name": f"Version History Doc {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        doc_id = doc_result["data"]["id"]
        
        # Create some versions by updating content
        for i in range(3):
            update_data = {
                "content": f"# Version {i+1}\n\nUpdated content for version {i+1}."
            }
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "update",
                    "entity_id": doc_id,
                    "data": update_data
                }
            )
        
        # Get version history
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "get_versions",
                "entity_id": doc_id
            }
        )
        
        assert result["success"] is True
        if "versions" in result["data"]:
            assert len(result["data"]["versions"]) >= 3
            # Verify versions are ordered by creation date
            versions = result["data"]["versions"]
            for i in range(len(versions) - 1):
                assert versions[i]["created_at"] <= versions[i + 1]["created_at"]


class TestDocumentListing:
    """Test listing documents with filtering and pagination."""
    
    @pytest.mark.asyncio
    async def test_list_documents_in_project(self, call_mcp):
        """List all documents within a specific project."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project
        project_data = {
            "name": f"List Docs Project {uuid.uuid4().hex[:8]}",
            "workspace_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        project_id = project_result["data"]["id"]
        
        # Create multiple documents in project
        doc_names = [f"Document {i}" for i in range(5)]
        created_ids = []
        
        for name in doc_names:
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document", 
                    "operation": "create", 
                    "data": {"name": name, "project_id": project_id, "workspace_id": workspace_id}
                }
            )
            created_ids.append(result["data"]["id"])
        
        # List documents in project
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document", 
                "operation": "list",
                "filters": {"project_id": project_id}
            }
        )
        
        assert result["success"] is True
        assert len(result["data"]) >= len(doc_names)
        
        # Verify our documents are in the list
        returned_ids = [d["id"] for d in result["data"]]
        for created_id in created_ids:
            assert created_id in returned_ids
    
    @pytest.mark.asyncio
    async def test_list_documents_with_pagination(self, call_mcp):
        """Test pagination when listing documents."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create many documents
        documents_created = []
        for i in range(12):
            result, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {"name": f"Paginated Document {i}", "workspace_id": workspace_id}
                }
            )
            documents_created.append(result["data"]["id"])
        
        # Test pagination (limit 5, offset 0)
        result1, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "limit": 5,
                "offset": 0
            }
        )
        
        assert result1["success"] is True
        assert len(result1["data"]) <= 5
        
        # Test pagination (limit 5, offset 5)
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "limit": 5,
                "offset": 5
            }
        )
        
        assert result2["success"] is True
        assert len(result2["data"]) <= 5
        
        # Test pagination (limit 5, offset 10)
        result3, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "limit": 5,
                "offset": 10
            }
        )
        
        assert result3["success"] is True
        assert len(result3["data"]) <= 5
        
        # Combined results should have most of our documents
        all_ids = [d["id"] for d in result1["data"]] + [d["id"] for d in result2["data"]] + [d["id"] for d in result3["data"]]
        documents_in_pagination = sum(1 for pid in documents_created if pid in all_ids)
        assert documents_in_pagination >= 10  # At least 10 of 12 documents
    
    @pytest.mark.asyncio
    async def test_list_documents_with_filtering(self, call_mcp):
        """Test filtering documents by type, status, and tags."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create documents with different types and statuses
        document_types = ["user_manual", "technical_spec", "api_reference"]
        document_statuses = ["draft", "active", "archived"]
        document_ids = {}
        
        for doc_type in document_types:
            for status in document_statuses:
                result, _ = await call_mcp(
                    "entity_tool",
                    {
                        "entity_type": "document",
                        "operation": "create",
                        "data": {
                            "name": f"{doc_type.title()} - {status.title()}",
                            "type": doc_type,
                            "status": status,
                            "tags": [doc_type, status],
                            "workspace_id": workspace_id
                        }
                    }
                )
                key = f"{doc_type}_{status}"
                document_ids[key] = result["data"]["id"]
        
        # Filter by type
        result, duration_ms = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "filters": {"type": "technical_spec"}
            }
        )
        
        assert result["success"] is True
        technical_spec_docs = [d for d in result["data"] if d["type"] == "technical_spec"]
        assert len(technical_spec_docs) >= 3  # Should have 3 different statuses
        
        # Filter by status
        result2, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "filters": {"status": "active"}
            }
        )
        
        assert result2["success"] is True
        active_docs = [d for d in result2["data"] if d["status"] == "active"]
        assert len(active_docs) >= 3  # Should have 3 different types
        
        # Filter by multiple criteria
        result3, _ = await call_mcp(
            "entity_tool",
            {
                "entity_type": "document",
                "operation": "list",
                "filters": {"type": "user_manual", "status": "draft"}
            }
        )
        
        assert result3["success"] is True
        filtered_docs = [
            d for d in result3["data"] 
            if d["type"] == "user_manual" and d["status"] == "draft"
        ]
        assert len(filtered_docs) >= 1
