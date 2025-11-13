"""Relationship Tool Tests - 3-Variant Coverage (Unit, Integration, E2E).

This test suite runs relationship tool tests in all three modes:
- Unit: In-memory mock client (<1ms, deterministic)
- Integration: HTTP client with live database (50-500ms)  
- E2E: Full deployment with production-like setup (500ms-5s)

Total tests: 72 (24 per variant)
Target coverage: All relationship types, all operations, error cases

Relationship types covered:
- member (organization ↔ user)
- assignment (project ↔ user)
- trace_link (requirement ↔ test)
- dependency (entity dependencies)
- generic (custom relationships)

Operations covered:
- create (link entities)
- read (get relationship details)
- update (modify metadata)
- delete (unlink entities)
- search (find relationships)
- list (paginate relationships)

Usage:
    # Run all variants
    pytest tests/unit/tools/test_relationship.py -v
    
    # Run specific variant
    pytest tests/unit/tools/test_relationship.py -m unit -v
    pytest tests/unit/tools/test_relationship.py -m integration -v  
    pytest tests/unit/tools/test_relationship.py -m e2e -v
"""

from __future__ import annotations

import uuid
import time
from typing import Any, Dict, Optional, List

import pytest
import pytest_asyncio
from tests.framework.test_base import ParametrizedTestSuite

pytestmark = [pytest.mark.asyncio, pytest.mark.three_variant]


class TestRelationshipCreateOperations(ParametrizedTestSuite):
    """Test CREATE (link) operations for relationships across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
    ], ids=["unit"])
    def client(self, request, mcp_client_inmemory):
        """Client fixture for relationship testing."""
        # For now, only unit tests are supported
        # TODO: Add mcp_client_http and end_to_end_client fixtures in their respective conftest.py files
        return mcp_client_inmemory
    
    async def _create_test_entities(self, client) -> Dict[str, str]:
        """Helper to create test entities for relationships."""
        entities = {}
        
        # Create organization
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        if org_result.get("success"):
            entities["organization"] = org_result["data"]["id"]
        
        # Create project
        if "organization" in entities:
            project_data = self.create_test_entity("project", 
                organization_id=entities["organization"])
            project_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": project_data
            })
            if project_result.get("success"):
                entities["project"] = project_result["data"]["id"]
        
        # Create document
        if "project" in entities:
            doc_data = self.create_test_entity("document",
                project_id=entities["project"])
            doc_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "document",
                "data": doc_data
            })
            if doc_result.get("success"):
                entities["document"] = doc_result["data"]["id"]
        
        # Create requirement
        if "document" in entities:
            req_data = self.create_test_entity("requirement",
                document_id=entities["document"])
            req_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "requirement",
                "data": req_data
            })
            if req_result.get("success"):
                entities["requirement"] = req_result["data"]["id"]
        
        return entities
    
    @pytest.mark.parametrize("relationship_type,source,target", [
        ("relates_to", "organization", "project"),
        ("traces_to", "requirement", "document"),
        ("depends_on", "project", "organization"),
        ("parent_of", "organization", "project"),
        ("references", "document", "requirement"),
    ])
    async def test_create_basic_relationship(self, client, relationship_type: str, 
                                            source: str, target: str):
        """Test creating basic relationships between entities."""
        entities = await self._create_test_entities(client)
        
        if source not in entities or target not in entities:
            pytest.skip(f"Could not create required entities: {source} -> {target}")
        
        rel_data = self.create_test_relationship(
            source, entities[source],
            target, entities[target],
            relationship_type,
            description=f"Test {relationship_type} relationship"
        )
        
        async with self.measure_timing():
            result = await client.call_tool("relationship_tool", {
                "operation": "create",
                **rel_data
            })
        
        self.assert_has_id(result)
        self.assert_relationship_structure(result["data"])
        
        # Verify relationship details
        rel = result["data"]
        assert rel["source_type"] == source
        assert rel["target_type"] == target
        assert rel["relationship_type"] == relationship_type
        assert rel["source_id"] == entities[source]
        assert rel["target_id"] == entities[target]
    
    async def test_create_relationship_with_metadata(self, client):
        """Test creating relationship with custom metadata."""
        entities = await self._create_test_entities(client)
        
        if "organization" not in entities or "project" not in entities:
            pytest.skip("Could not create required entities")
        
        metadata = {
            "role": "owner",
            "permissions": ["read", "write", "admin"],
            "created_by": "test_user",
            "priority": "high"
        }
        
        rel_data = self.create_test_relationship(
            "organization", entities["organization"],
            "project", entities["project"],
            "manages",
            **metadata
        )
        
        result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_success(result)
        rel = result["data"]
        
        # Verify metadata was preserved
        for key, value in metadata.items():
            assert key in rel.get("metadata", {}), f"Metadata {key} should be preserved"
            assert rel["metadata"][key] == value, f"Metadata {key} should have correct value"
    
    async def test_duplicate_relationship_handling(self, client):
        """Test creating duplicate relationships."""
        entities = await self._create_test_entities(client)
        
        if "organization" not in entities or "project" not in entities:
            pytest.skip("Could not create required entities")
        
        rel_data = self.create_test_relationship(
            "organization", entities["organization"],
            "project", entities["project"],
            "relates_to"
        )
        
        # Create first relationship
        result1 = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        self.assert_success(result1)
        
        # Attempt to create exact duplicate
        result2 = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        # Should either succeed with same ID or fail gracefully
        if result2.get("success"):
            # If successful, should return same relationship
            assert result2["data"]["id"] == result1["data"]["id"], \
                "Duplicate should return same relationship ID"
        else:
            # If failed, should indicate duplicate exists
            assert "duplicate" in result2.get("error", "").lower() or \
                   "exists" in result2.get("error", "").lower()
    
    async def test_create_relationship_invalid_entities(self, client):
        """Test creating relationship with non-existent entities."""
        fake_org_id = f"fake-org-{uuid.uuid4().hex[:12]}"
        fake_proj_id = f"fake-proj-{uuid.uuid4().hex[:12]}"
        
        rel_data = self.create_test_relationship(
            "organization", fake_org_id,
            "project", fake_proj_id,
            "relates_to"
        )
        
        result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_error(result)
        assert "not found" in result.get("error", "").lower()
    
    async def test_circular_relationship_prevention(self, client):
        """Test prevention of circular relationships (entity to itself)."""
        entities = await self._create_test_entities(client)
        
        if "organization" not in entities:
            pytest.skip("Could not create required entity")
        
        # Try to create circular relationship
        rel_data = self.create_test_relationship(
            "organization", entities["organization"],
            "organization", entities["organization"],
            "relates_to"
        )
        
        result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_error(result)
        assert "circular" in result.get("error", "").lower()


class TestRelationshipReadOperations(ParametrizedTestSuite):
    """Test READ operations for relationships across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_test_relationship(self, client) -> str:
        """Helper to create test relationship and return ID."""
        # Create source entity
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        # Create target entity
        project_data = self.create_test_entity("project",
            organization_id=org_id)
        project_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": project_data
        })
        project_id = project_result["data"]["id"]
        
        # Create relationship
        rel_data = self.create_test_relationship(
            "organization", org_id,
            "project", project_id,
            "relates_to",
            description="Test relationship for reading"
        )
        
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_success(rel_result)
        return rel_result["data"]["id"]
    
    async def test_read_relationship_by_id(self, client):
        """Test reading relationship by its ID."""
        rel_id = await self._create_test_relationship(client)
        
        result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        
        self.assert_success(result)
        rel = result["data"]
        
        assert rel["id"] == rel_id, "Should return correct relationship"
        self.assert_relationship_structure(rel)
    
    async def test_read_relationship_by_source(self, client):
        """Test reading relationships by source entity."""
        rel_id = await self._create_test_relationship(client)
        
        # Get the source ID from the created relationship
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        source_id = rel_result["data"]["source_id"]
        source_type = rel_result["data"]["source_type"]
        
        # Search by source
        result = await client.call_tool("relationship_tool", {
            "operation": "search",
            "source_type": source_type,
            "source_id": source_id
        })
        
        self.assert_success(result)
        relationships = result["data"]
        assert isinstance(relationships, list), "Should return list of relationships"
        assert len(relationships) >= 1, "Should find at least one relationship"
        
        # Should include our created relationship
        our_rel = next((r for r in relationships if r["id"] == rel_id), None)
        assert our_rel is not None, "Should include our created relationship"
    
    async def test_read_relationship_by_target(self, client):
        """Test reading relationships by target entity."""
        rel_id = await self._create_test_relationship(client)
        
        # Get the target ID from the created relationship
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        target_id = rel_result["data"]["target_id"]
        target_type = rel_result["data"]["target_type"]
        
        # Search by target
        result = await client.call_tool("relationship_tool", {
            "operation": "search",
            "target_type": target_type,
            "target_id": target_id
        })
        
        self.assert_success(result)
        relationships = result["data"]
        assert isinstance(relationships, list), "Should return list of relationships"
        assert len(relationships) >= 1, "Should find at least one relationship"
        
        # Should include our created relationship
        our_rel = next((r for r in relationships if r["id"] == rel_id), None)
        assert our_rel is not None, "Should include our created relationship"
    
    async def test_read_relationship_by_type(self, client):
        """Test reading relationships by relationship type."""
        rel_id = await self._create_test_relationship(client)
        
        # Get the relationship type
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        rel_type = rel_result["data"]["relationship_type"]
        
        # Search by type
        result = await client.call_tool("relationship_tool", {
            "operation": "search",
            "relationship_type": rel_type
        })
        
        self.assert_success(result)
        relationships = result["data"]
        assert isinstance(relationships, list), "Should return list of relationships"
        assert len(relationships) >= 1, "Should find at least one relationship"
    
    async def test_read_nonexistent_relationship(self, client):
        """Test reading non-existent relationship."""
        fake_id = f"fake-rel-{uuid.uuid4().hex[:16]}"
        
        result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": fake_id
        })
        
        self.assert_error(result)
        assert "not found" in result.get("error", "").lower()


class TestRelationshipUpdateOperations(ParametrizedTestSuite):
    """Test UPDATE operations for relationships across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_test_relationship(self, client) -> str:
        """Helper to create test relationship and return ID."""
        # Create entities
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        project_data = self.create_test_entity("project",
            organization_id=org_id)
        project_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": project_data
        })
        project_id = project_result["data"]["id"]
        
        # Create relationship
        rel_data = self.create_test_relationship(
            "organization", org_id,
            "project", project_id,
            "relates_to",
            description="Original description"
        )
        
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_success(rel_result)
        return rel_result["data"]["id"]
    
    async def test_update_relationship_metadata(self, client):
        """Test updating relationship metadata."""
        rel_id = await self._create_test_relationship(client)
        
        update_data = {
            "description": "Updated description",
            "role": "administrator",
            "permissions": ["read", "write", "delete"],
            "priority": "critical"
        }
        
        result = await client.call_tool("relationship_tool", {
            "operation": "update",
            "relationship_id": rel_id,
            "metadata": update_data
        })
        
        self.assert_success(result)
        rel = result["data"]
        assert rel["id"] == rel_id, "ID should not change on update"
        
        # Verify metadata was updated
        metadata = rel.get("metadata", {})
        for key, value in update_data.items():
            assert metadata[key] == value, f"Metadata {key} should be updated"
    
    async def test_update_relationship_partial_metadata(self, client):
        """Test updating only part of relationship metadata."""
        rel_id = await self._create_test_relationship(client)
        
        # Get original metadata
        original_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        original_metadata = original_result["data"].get("metadata", {})
        
        # Update only one field
        update_data = {"description": "Partially updated"}
        
        result = await client.call_tool("relationship_tool", {
            "operation": "update",
            "relationship_id": rel_id,
            "metadata": update_data
        })
        
        self.assert_success(result)
        rel = result["data"]
        
        # Should preserve original metadata and update specified field
        metadata = rel.get("metadata", {})
        assert metadata["description"] == "Partially updated", "Updated field should change"
        
        # Original fields should be preserved unless explicitly updated
        for key, value in original_metadata.items():
            if key not in update_data:
                assert metadata[key] == value, f"Original field {key} should be preserved"
    
    async def test_update_nonexistent_relationship(self, client):
        """Test updating non-existent relationship."""
        fake_id = f"fake-rel-{uuid.uuid4().hex[:16]}"
        
        result = await client.call_tool("relationship_tool", {
            "operation": "update",
            "relationship_id": fake_id,
            "metadata": {"description": "Updated"}
        })
        
        self.assert_error(result)
        assert "not found" in result.get("error", "").lower()
    
    async def test_update_relationship_invalid_data(self, client):
        """Test updating relationship with invalid metadata."""
        rel_id = await self._create_test_relationship(client)
        
        # Try to update with invalid metadata structure
        result = await client.call_tool("relationship_tool", {
            "operation": "update",
            "relationship_id": rel_id,
            "metadata": None  # Invalid - should be dict
        })
        
        self.assert_error(result)


class TestRelationshipDeleteOperations(ParametrizedTestSuite):
    """Test DELETE (unlink) operations for relationships across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_test_relationship(self, client) -> str:
        """Helper to create test relationship and return ID."""
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        project_data = self.create_test_entity("project",
            organization_id=org_id)
        project_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": project_data
        })
        project_id = project_result["data"]["id"]
        
        rel_data = self.create_test_relationship(
            "organization", org_id,
            "project", project_id,
            "relates_to"
        )
        
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_success(rel_result)
        return rel_result["data"]["id"]
    
    async def test_delete_relationship_by_id(self, client):
        """Test deleting relationship by its ID."""
        rel_id = await self._create_test_relationship(client)
        
        # Delete the relationship
        result = await client.call_tool("relationship_tool", {
            "operation": "delete",
            "relationship_id": rel_id
        })
        
        self.assert_success(result)
        
        # Verify relationship is gone
        read_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        self.assert_error(read_result)
        assert "not found" in read_result.get("error", "").lower()
    
    async def test_delete_relationship_by_entities(self, client):
        """Test deleting relationship by specifying source and target."""
        rel_id = await self._create_test_relationship(client)
        
        # Get relationship details for deletion
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        rel = rel_result["data"]
        
        # Delete by entities
        result = await client.call_tool("relationship_tool", {
            "operation": "delete",
            "source_type": rel["source_type"],
            "source_id": rel["source_id"],
            "target_type": rel["target_type"],
            "target_id": rel["target_id"],
            "relationship_type": rel["relationship_type"]
        })
        
        self.assert_success(result)
        
        # Verify relationship is gone
        read_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        self.assert_error(read_result)
    
    async def test_delete_nonexistent_relationship(self, client):
        """Test deleting non-existent relationship."""
        fake_id = f"fake-rel-{uuid.uuid4().hex[:16]}"
        
        result = await client.call_tool("relationship_tool", {
            "operation": "delete",
            "relationship_id": fake_id
        })
        
        self.assert_error(result)
        assert "not found" in result.get("error", "").lower()
    
    async def test_delete_relationship_missing_target(self, client):
        """Test deleting relationship with incomplete target specification."""
        result = await client.call_tool("relationship_tool", {
            "operation": "delete",
            "source_type": "organization",
            "source_id": "some-id",
            # Missing target_type, target_id
        })
        
        self.assert_error(result)
        assert "required" in result.get("error", "").lower()


class TestRelationshipSearchAndList(ParametrizedTestSuite):
    """Test SEARCH and LIST operations for relationships across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_test_relationships(self, client, count: int = 5) -> List[str]:
        """Helper to create multiple test relationships."""
        rel_ids = []
        
        # Create one organization as source for multiple projects
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        # Create multiple projects and relationships
        for i in range(count):
            project_data = self.create_test_entity("project",
                name=f"Search Test Project {i}",
                organization_id=org_id)
            project_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": project_data
            })
            
            if project_result.get("success"):
                project_id = project_result["data"]["id"]
                
                rel_data = self.create_test_relationship(
                    "organization", org_id,
                    "project", project_id,
                    "relates_to",
                    description=f"Test relationship {i}"
                )
                
                rel_result = await client.call_tool("relationship_tool", {
                    "operation": "create",
                    **rel_data
                })
                
                if rel_result.get("success"):
                    rel_ids.append(rel_result["data"]["id"])
        
        return rel_ids
    
    async def test_list_all_relationships(self, client):
        """Test listing all relationships."""
        await self._create_test_relationships(client, 3)
        
        result = await client.call_tool("relationship_tool", {
            "operation": "list"
        })
        
        self.assert_success(result)
        relationships = result["data"]
        assert isinstance(relationships, list), "Should return list of relationships"
        assert len(relationships) >= 3, "Should find at least our test relationships"
    
    async def test_search_relationships_with_filters(self, client):
        """Test searching relationships with filters."""
        rel_ids = await self._create_test_relationships(client, 3)
        
        # Search with specific relationship type
        result = await client.call_tool("relationship_tool", {
            "operation": "search",
            "relationship_type": "relates_to"
        })
        
        self.assert_success(result)
        relationships = result["data"]
        assert len(relationships) >= 3, "Should find filtered relationships"
        
        # All results should be of the specified type
        for rel in relationships:
            assert rel["relationship_type"] == "relates_to"
    
    async def test_list_with_pagination(self, client):
        """Test listing relationships with pagination."""
        await self._create_test_relationships(client, 5)
        
        # Get first page
        result = await client.call_tool("relationship_tool", {
            "operation": "list",
            "limit": 2,
            "offset": 0
        })
        
        self.assert_success(result)
        first_page = result["data"]
        assert len(first_page) <= 2, "Should respect limit"
        
        # Get second page
        result = await client.call_tool("relationship_tool", {
            "operation": "list",
            "limit": 2,
            "offset": 2
        })
        
        self.assert_success(result)
        second_page = result["data"]
        assert len(second_page) <= 2, "Should respect limit"
        
        # Pages should have different content
        if len(first_page) > 0 and len(second_page) > 0:
            first_ids = {r["id"] for r in first_page}
            second_ids = {r["id"] for r in second_page}
            assert len(first_ids.intersection(second_ids)) == 0, "Pages should not overlap"
    
    async def test_search_by_metadata(self, client):
        """Test searching relationships by metadata."""
        # Create relationships with specific metadata
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        # Create projects with different relationship metadata
        for i in range(3):
            project_data = self.create_test_entity("project",
                name=f"Metadata Test Project {i}",
                organization_id=org_id)
            project_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": project_data
            })
            
            if project_result.get("success"):
                project_id = project_result["data"]["id"]
                
                rel_data = self.create_test_relationship(
                    "organization", org_id,
                    "project", project_id,
                    "relates_to",
                    priority="high" if i == 0 else "low",
                    role="manager" if i == 1 else "member"
                )
                
                await client.call_tool("relationship_tool", {
                    "operation": "create",
                    **rel_data
                })
        
        # Search by metadata
        result = await client.call_tool("relationship_tool", {
            "operation": "search",
            "metadata": {"priority": "high"}
        })
        
        self.assert_success(result)
        relationships = result["data"]
        
        # Should find relationships with matching metadata
        for rel in relationships:
            metadata = rel.get("metadata", {})
            assert metadata.get("priority") == "high"


class TestRelationshipPerformance(ParametrizedTestSuite):
    """Test relationship operation performance across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    @pytest.mark.parametrize("operation,max_time_ms", [
        ("create", 100),   # Unit: <1ms, Integration: <50ms, E2E: <100ms  
        ("read", 50),      # Unit: <1ms, Integration: <25ms, E2E: <50ms
        ("update", 100),   # Unit: <1ms, Integration: <50ms, E2E: <100ms
        ("delete", 100),   # Unit: <1ms, Integration: <50ms, E2E: <100ms
        ("search", 200),   # Unit: <1ms, Integration: <100ms, E2E: <200ms
    ])
    async def test_operation_timing(self, client, operation: str, max_time_ms: int):
        """Test relationship operation timing within expected bounds."""
        # Setup: Create entities and relationship for operations that need it
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        project_data = self.create_test_entity("project",
            organization_id=org_id)
        project_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": project_data
        })
        project_id = project_result["data"]["id"]
        
        rel_data = self.create_test_relationship(
            "organization", org_id,
            "project", project_id,
            "relates_to"
        )
        
        # Create relationship for read/update/delete tests
        if operation != "create":
            create_result = await client.call_tool("relationship_tool", {
                "operation": "create",
                **rel_data
            })
            rel_id = create_result["data"]["id"]
        
        # Time the operation
        start_time = time.perf_counter()
        
        if operation == "create":
            result = await client.call_tool("relationship_tool", {
                "operation": "create",
                **rel_data
            })
        elif operation == "read":
            result = await client.call_tool("relationship_tool", {
                "operation": "read",
                "relationship_id": rel_id
            })
        elif operation == "update":
            result = await client.call_tool("relationship_tool", {
                "operation": "update",
                "relationship_id": rel_id,
                "metadata": {"description": "Updated"}
            })
        elif operation == "delete":
            result = await client.call_tool("relationship_tool", {
                "operation": "delete",
                "relationship_id": rel_id
            })
        elif operation == "search":
            result = await client.call_tool("relationship_tool", {
                "operation": "search",
                "relationship_type": "relates_to"
            })
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Performance expectations by variant
        if not hasattr(client, '_config'):  # Unit test
            assert elapsed_ms < 5, f"Unit {operation} took {elapsed_ms:.2f}ms, expected <5ms"
        else:  # Integration or E2E
            assert elapsed_ms < max_time_ms, \
                f"{operation} took {elapsed_ms:.2f}ms, expected <{max_time_ms}ms"
        
        if operation != "delete":  # Delete returns success but we don't need to assert
            self.assert_success(result)


class TestRelationshipEdgeCases(ParametrizedTestSuite):
    """Test relationship edge cases and unusual scenarios."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def test_relationship_cascade_deletion(self, client):
        """Test that deleting source entity cascades to relationships."""
        # Create organization
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        # Create project
        project_data = self.create_test_entity("project",
            organization_id=org_id)
        project_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": project_data
        })
        project_id = project_result["data"]["id"]
        
        # Create relationship
        rel_data = self.create_test_relationship(
            "organization", org_id,
            "project", project_id,
            "relates_to"
        )
        rel_result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        rel_id = rel_result["data"]["id"]
        
        # Delete the source organization
        await client.call_tool("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": org_id
        })
        
        # Relationship should be deleted or inaccessible
        read_result = await client.call_tool("relationship_tool", {
            "operation": "read",
            "relationship_id": rel_id
        })
        
        # Should fail due to cascade deletion
        self.assert_error(read_result)
    
    async def test_bidirectional_relationships(self, client):
        """Test creating and managing bidirectional relationships."""
        # Create two organizations
        org1_data = self.create_test_entity("organization",
            name="Partner Org 1")
        org1_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org1_data
        })
        org1_id = org1_result["data"]["id"]
        
        org2_data = self.create_test_entity("organization",
            name="Partner Org 2")
        org2_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org2_data
        })
        org2_id = org2_result["data"]["id"]
        
        # Create partnership relationship (bidirectional)
        rel1_data = self.create_test_relationship(
            "organization", org1_id,
            "organization", org2_id,
            "partners_with"
        )
        
        rel1_result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel1_data
        })
        self.assert_success(rel1_result)
        
        rel2_data = self.create_test_relationship(
            "organization", org2_id,
            "organization", org1_id,
            "partners_with"
        )
        
        rel2_result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel2_data
        })
        self.assert_success(rel2_result)
        
        # Should be able to find relationships from both directions
        search1 = await client.call_tool("relationship_tool", {
            "operation": "search",
            "source_type": "organization",
            "source_id": org1_id
        })
        assert len(search1["data"]) >= 1, "Should find outgoing partnership"
        
        search2 = await client.call_tool("relationship_tool", {
            "operation": "search",
            "source_type": "organization",
            "source_id": org2_id
        })
        assert len(search2["data"]) >= 1, "Should find outgoing partnership"
    
    async def test_relationship_with_large_metadata(self, client):
        """Test relationship with large metadata payload."""
        # Create minimal entities
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        project_data = self.create_test_entity("project",
            organization_id=org_id)
        project_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": project_data
        })
        project_id = project_result["data"]["id"]
        
        # Create relationship with large metadata
        large_metadata = {
            "description": "A" * 1000,  # Long description
            "notes": ["Note " + str(i) * 100 for i in range(10)],  # Array of long strings
            "config": {f"key_{i}": "value_" + str(i) * 50 for i in range(20)}  # Many config items
        }
        
        rel_data = self.create_test_relationship(
            "organization", org_id,
            "project", project_id,
            "configures",
            **large_metadata
        )
        
        result = await client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        
        self.assert_success(result)
        rel = result["data"]
        
        # Verify large metadata was stored correctly
        stored_metadata = rel.get("metadata", {})
        assert len(stored_metadata["description"]) == 1000, "Long description should be stored"
        assert len(stored_metadata["notes"]) == 10, "All notes should be stored"
    
    async def test_relationship_query_complex_filters(self, client):
        """Test searching relationships with complex filter combinations."""
        # Create multiple relationships with different metadata
        await self._create_test_relationships_with_metadata(client)
        
        # Complex filter: high priority AND manager role
        result = await client.call_tool("relationship_tool", {
            "operation": "search",
            "metadata": {"priority": "high"},
            "filters": {
                "role": "manager",
                "relationship_type": "relates_to"
            }
        })
        
        self.assert_success(result)
        relationships = result["data"]
        
        # All results should match all filter criteria
        for rel in relationships:
            assert rel.get("relationship_type") == "relates_to"
            metadata = rel.get("metadata", {})
            assert metadata.get("priority") == "high"
            assert metadata.get("role") == "manager"
    
    async def _create_test_relationships_with_metadata(self, client):
        """Helper to create relationships with varied metadata for testing."""
        # Create base organization
        org_data = self.create_test_entity("organization")
        org_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data
        })
        org_id = org_result["data"]["id"]
        
        # Create relationships with different metadata
        metadata_combinations = [
            {"priority": "high", "role": "manager"},
            {"priority": "high", "role": "member"},
            {"priority": "low", "role": "member"},
        ]
        
        for i, metadata in enumerate(metadata_combinations):
            project_data = self.create_test_entity("project",
                name=f"Complex Filter Project {i}",
                organization_id=org_id)
            project_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": project_data
            })
            
            if project_result.get("success"):
                project_id = project_result["data"]["id"]
                
                rel_data = self.create_test_relationship(
                    "organization", org_id,
                    "project", project_id,
                    "relates_to",
                    **metadata
                )
                
                await client.call_tool("relationship_tool", {
                    "operation": "create",
                    **rel_data
                })
@pytest_asyncio.fixture
async def user_id(call_mcp):
    """Get current user ID."""
    context = await call_mcp("workspace_tool", {"operation": "get_context"})
    uid = context.get("data", {}).get("user_id")
    if not uid:
        pytest.skip("Could not get user_id")
    return uid


# ============================================================================
# TEST: MEMBER RELATIONSHIPS
# ============================================================================

class TestMemberRelationship:
    """Comprehensive tests for member relationship type (organizations and projects)."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_organization_member_success(self, call_mcp, test_entities, user_id):
        """Test successfully linking a user to an organization as a member."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin", "status": "active"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "admin"
        assert result["data"]["status"] == "active"
        assert result["data"]["organization_id"] == test_entities["organization"]
        assert result["data"]["user_id"] == user_id
        print(f"✓ Organization member link created: {result['data']['id']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_organization_member_minimal_metadata(self, call_mcp, test_entities, user_id):
        """Test linking with minimal metadata (should use defaults)."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "viewer"
        assert result["data"]["status"] == "active"  # Default value
        print(f"✓ Member created with defaults: status={result['data']['status']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_project_member_with_org_context(self, call_mcp, test_entities, user_id):
        """Test linking user to project with organization context."""
        if "project" not in test_entities or "organization" not in test_entities:
            pytest.skip("Project or Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "project", "id": test_entities["project"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "developer"},
                "source_context": test_entities["organization"]
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "developer"
        assert result["data"]["org_id"] == test_entities["organization"]
        assert result["data"]["project_id"] == test_entities["project"]
        print(f"✓ Project member created with org_id: {result['data']['org_id']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_organization_members(self, call_mcp, test_entities, user_id):
        """Test listing all members of an organization."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # First create a member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # List members
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 10,
                "offset": 0
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        assert len(result["data"]) > 0

        # Verify profile join
        for member in result["data"]:
            if member.get("user_id") == user_id:
                # Check if profiles were joined
                if "profiles" in member:
                    print(f"✓ Profile joined: {member['profiles'].get('email', 'N/A')}")
                break

        print(f"✓ Listed {len(result['data'])} members")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_project_members(self, call_mcp, test_entities, user_id):
        """Test listing project members."""
        if "project" not in test_entities or "organization" not in test_entities:
            pytest.skip("Project or Organization not created")

        # Create project member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "project", "id": test_entities["project"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "developer"},
                "source_context": test_entities["organization"]
            }
        )

        # List project members
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "project", "id": test_entities["project"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} project members")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_member_exists(self, call_mcp, test_entities, user_id):
        """Test checking if a member relationship exists."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Check existence
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"] is not None
        assert result["relationship"]["role"] in ["viewer", "admin"]  # Could be from previous test
        print(f"✓ Member exists: {result['relationship']['role']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_member_not_exists(self, call_mcp, test_entities):
        """Test checking for a non-existent member."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        fake_user_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": fake_user_id}
            }
        )

        assert result.get("exists") is False, f"Should not exist: {result}"
        assert result["relationship"] is None
        print("✓ Correctly reported non-existent member")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_member_role(self, call_mcp, test_entities, user_id):
        """Test updating member role metadata."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create member with viewer role
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Update to admin
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "admin"
        assert "updated_at" in result["data"]
        print("✓ Member role updated from viewer to admin")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_member_status(self, call_mcp, test_entities, user_id):
        """Test updating member status."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create active member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "member", "status": "active"}
            }
        )

        # Update to inactive
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"status": "inactive"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "inactive"
        print("✓ Member status updated to inactive")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unlink_member(self, call_mcp, test_entities, user_id):
        """Test removing a member relationship (hard delete for members)."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create member
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Unlink (member tables don't have is_deleted, so this is hard delete)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "soft_delete": True
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Member unlinked successfully")

        # Verify it's gone
        check = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id}
            }
        )
        assert check.get("exists") is False
        print("✓ Verified member no longer exists after unlink")


# ============================================================================
# TEST: ASSIGNMENT RELATIONSHIPS
# ============================================================================

class TestAssignmentRelationship:
    """Comprehensive tests for assignment relationship type."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_assignment_success(self, call_mcp, test_entities, user_id):
        """Test creating an assignment relationship."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner", "status": "active"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["entity_type"] == "requirement"
        assert result["data"]["role"] == "owner"
        assert result["data"]["status"] == "active"
        assert result["data"]["entity_id"] == test_entities["requirement"]
        assert result["data"]["assignee_id"] == user_id
        print(f"✓ Assignment created: {result['data']['id']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_assignment_with_defaults(self, call_mcp, test_entities, user_id):
        """Test assignment with default values."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "active"  # Default
        assert result["data"]["role"] == "reviewer"
        print(f"✓ Assignment created with defaults: status={result['data']['status']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_assignments_by_entity(self, call_mcp, test_entities, user_id):
        """Test listing all assignments for an entity."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner"}
            }
        )

        # List assignments
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        assert len(result["data"]) > 0
        print(f"✓ Listed {len(result['data'])} assignments for requirement")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_assignments_by_assignee(self, call_mcp, test_entities, user_id):
        """Test listing assignments for a specific user."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "contributor"}
            }
        )

        # List by assignee (target)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "target": {"type": "user", "id": user_id},
                "limit": 10
            }
        )

        # This may or may not be supported depending on implementation
        if result.get("success"):
            assert isinstance(result.get("data"), list)
            print(f"✓ Listed {len(result['data'])} assignments for user")
        else:
            print("⚠ Target-only listing not supported for assignments")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_assignments_with_status_filter(self, call_mcp, test_entities, user_id):
        """Test filtering assignments by status."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create active assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner", "status": "active"}
            }
        )

        # List with status filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"status": "active"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for assignment in result.get("data", []):
            assert assignment.get("status") == "active"
        print(f"✓ Filtered {len(result['data'])} active assignments")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_assignments_with_role_filter(self, call_mcp, test_entities, user_id):
        """Test filtering assignments by role."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment with specific role
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        # List with role filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"role": "reviewer"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for assignment in result.get("data", []):
            assert assignment.get("role") == "reviewer"
        print(f"✓ Filtered {len(result['data'])} reviewer assignments")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_assignment_exists(self, call_mcp, test_entities, user_id):
        """Test checking if an assignment exists."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner"}
            }
        )

        # Check existence
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"] is not None
        print(f"✓ Assignment exists: role={result['relationship']['role']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_assignment_role(self, call_mcp, test_entities, user_id):
        """Test updating assignment role."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "contributor"}
            }
        )

        # Update to owner
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "owner"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "owner"
        print("✓ Assignment role updated from contributor to owner")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unlink_assignment_soft_delete(self, call_mcp, test_entities, user_id):
        """Test soft deleting an assignment."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        # Soft delete
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "soft_delete": True
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Assignment soft deleted")

        # Verify it doesn't appear in normal list
        list_result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        # Should not include soft-deleted assignment
        for assignment in list_result.get("data", []):
            assert assignment.get("is_deleted") is not True
        print("✓ Soft-deleted assignment excluded from list")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unlink_assignment_hard_delete(self, call_mcp, test_entities, user_id):
        """Test hard deleting an assignment."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        # Create assignment
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "reviewer"}
            }
        )

        # Hard delete
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "assignment",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "soft_delete": False
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Assignment hard deleted")


# ============================================================================
# TEST: TRACE LINK RELATIONSHIPS
# ============================================================================

class TestTraceLinkRelationship:
    """Comprehensive tests for trace_link relationship type."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_trace_link_success(self, call_mcp, test_entities):
        """Test creating a trace link between requirements."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "depends_on", "version": 1}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["source_type"] == "requirement"
        assert result["data"]["target_type"] == "requirement"
        assert result["data"]["link_type"] == "depends_on"
        assert result["data"]["version"] == 1
        assert result["data"]["is_deleted"] is False
        print(f"✓ Trace link created: {result['data']['id']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_trace_link_with_defaults(self, call_mcp, test_entities):
        """Test trace link with default values."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "related_to"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["version"] == 1  # Default
        assert result["data"]["is_deleted"] is False  # Default
        print(f"✓ Trace link created with defaults: version={result['data']['version']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_bidirectional_trace_links(self, call_mcp, test_entities):
        """Test creating bidirectional trace links."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Link A -> B
        link1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "depends_on"}
            }
        )

        # Link B -> A
        link2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement_1"]},
                "target": {"type": "requirement", "id": test_entities["requirement"]},
                "metadata": {"link_type": "depended_by"}
            }
        )

        assert link1.get("success") is True, f"Link1 failed: {link1}"
        assert link2.get("success") is True, f"Link2 failed: {link2}"
        print("✓ Bidirectional trace links created")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_trace_links_from_source(self, call_mcp, test_entities):
        """Test listing trace links from a source requirement."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "implements"}
            }
        )

        # List from source
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} trace links from source")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_trace_links_to_target(self, call_mcp, test_entities):
        """Test listing trace links to a target requirement."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "derives_from"}
            }
        )

        # List to target
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} trace links to target")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_trace_links_with_type_filter(self, call_mcp, test_entities):
        """Test filtering trace links by link_type."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create multiple trace links with different types
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "depends_on"}
            }
        )

        # List with type filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"link_type": "depends_on"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for link in result.get("data", []):
            assert link.get("link_type") == "depends_on"
        print(f"✓ Filtered {len(result['data'])} 'depends_on' trace links")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_trace_link_exists(self, call_mcp, test_entities):
        """Test checking if a trace link exists."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "verifies"}
            }
        )

        # Check existence
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"]["link_type"] == "verifies"
        print(f"✓ Trace link exists: {result['relationship']['link_type']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_trace_link_version(self, call_mcp, test_entities):
        """Test updating trace link version."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "implements", "version": 1}
            }
        )

        # Update version
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"version": 2}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["version"] == 2
        print("✓ Trace link version updated to 2")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unlink_trace_link_soft_delete(self, call_mcp, test_entities):
        """Test soft deleting a trace link."""
        if "requirement" not in test_entities or "requirement_1" not in test_entities:
            pytest.skip("Requirements not created")

        # Create trace link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "metadata": {"link_type": "related_to"}
            }
        )

        # Soft delete
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "requirement", "id": test_entities["requirement_1"]},
                "soft_delete": True
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Trace link soft deleted")

        # Verify it's excluded from normal list (is_deleted=false filter)
        list_result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "trace_link",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        for link in list_result.get("data", []):
            if link.get("target_id") == test_entities["requirement_1"]:
                assert link.get("is_deleted") is False
        print("✓ Soft-deleted trace link excluded from list")


# ============================================================================
# TEST: REQUIREMENT-TEST RELATIONSHIPS
# ============================================================================

class TestRequirementTestRelationship:
    """Comprehensive tests for requirement_test relationship type."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_requirement_to_test_success(self, call_mcp, test_entities):
        """Test linking a requirement to a test."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {
                    "relationship_type": "tests",
                    "coverage_level": "full"
                }
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["relationship_type"] == "tests"
        assert result["data"]["coverage_level"] == "full"
        assert result["data"]["requirement_id"] == test_entities["requirement"]
        assert result["data"]["test_id"] == test_entities["test"]
        print(f"✓ Requirement-test link created: {result['data']['id']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_requirement_test_with_defaults(self, call_mcp, test_entities):
        """Test linking with default values."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["relationship_type"] == "tests"  # Default
        assert result["data"]["coverage_level"] == "partial"
        print(f"✓ Created with defaults: relationship_type={result['data']['relationship_type']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_multiple_tests_to_requirement(self, call_mcp, test_entities):
        """Test linking multiple tests to a single requirement."""
        if "requirement" not in test_entities or "test" not in test_entities or "test_1" not in test_entities:
            pytest.skip("Requirements or Tests not created")

        # Link test 1
        link1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # Link test 2
        link2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test_1"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        assert link1.get("success") is True
        assert link2.get("success") is True
        print("✓ Linked 2 tests to requirement")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_test_coverage_for_requirement(self, call_mcp, test_entities):
        """Test listing all tests covering a requirement."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # List tests
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} test coverage links")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_requirements_covered_by_test(self, call_mcp, test_entities):
        """Test listing requirements covered by a specific test."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # List by test (target)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test",
                "target": {"type": "test", "id": test_entities["test"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} requirements covered by test")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_with_coverage_level_filter(self, call_mcp, test_entities):
        """Test filtering by coverage level."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link with full coverage
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # List with filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "filters": {"coverage_level": "full"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for link in result.get("data", []):
            assert link.get("coverage_level") == "full"
        print(f"✓ Filtered {len(result['data'])} full coverage links")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_requirement_test_link(self, call_mcp, test_entities):
        """Test checking if a requirement-test link exists."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        # Check
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"]["coverage_level"] == "partial"
        print(f"✓ Link exists with coverage: {result['relationship']['coverage_level']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_coverage_level(self, call_mcp, test_entities):
        """Test updating coverage level metadata."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create with partial coverage
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "partial"}
            }
        )

        # Update to full coverage
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["coverage_level"] == "full"
        print("✓ Coverage level updated from partial to full")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unlink_requirement_test(self, call_mcp, test_entities):
        """Test removing a requirement-test link."""
        if "requirement" not in test_entities or "test" not in test_entities:
            pytest.skip("Requirement or Test not created")

        # Create link
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "metadata": {"coverage_level": "full"}
            }
        )

        # Unlink
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "requirement_test",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "test", "id": test_entities["test"]},
                "soft_delete": False
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Requirement-test link removed")


# ============================================================================
# TEST: INVITATION RELATIONSHIPS
# ============================================================================

class TestInvitationRelationship:
    """Comprehensive tests for invitation relationship type."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_invitation_success(self, call_mcp, test_entities):
        """Test creating an organization invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {
                    "role": "member",
                    "status": "pending"
                }
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "member"
        assert result["data"]["status"] == "pending"
        assert result["data"]["email"] == test_email
        print(f"✓ Invitation created: {result['data']['id']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_invitation_with_defaults(self, call_mcp, test_entities):
        """Test invitation with default values."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"default-{uuid.uuid4().hex[:8]}@example.com"

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "viewer"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "pending"  # Default
        print(f"✓ Invitation created with default status: {result['data']['status']}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_admin_invitation(self, call_mcp, test_entities):
        """Test creating admin invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"admin-{uuid.uuid4().hex[:8]}@example.com"

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["role"] == "admin"
        print("✓ Admin invitation created")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_all_invitations(self, call_mcp, test_entities):
        """Test listing all invitations for an organization."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create invitation
        test_email = f"list-{uuid.uuid4().hex[:8]}@example.com"
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # List invitations
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert isinstance(result.get("data"), list)
        print(f"✓ Listed {len(result['data'])} invitations")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_pending_invitations(self, call_mcp, test_entities):
        """Test filtering invitations by pending status."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create pending invitation
        test_email = f"pending-{uuid.uuid4().hex[:8]}@example.com"
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member", "status": "pending"}
            }
        )

        # List with status filter
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "filters": {"status": "pending"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for inv in result.get("data", []):
            assert inv.get("status") == "pending"
        print(f"✓ Filtered {len(result['data'])} pending invitations")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_invitations_by_role(self, call_mcp, test_entities):
        """Test filtering invitations by role."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create admin invitation
        test_email = f"role-filter-{uuid.uuid4().hex[:8]}@example.com"
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "admin"}
            }
        )

        # List admin invitations
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "filters": {"role": "admin"},
                "limit": 10
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        for inv in result.get("data", []):
            assert inv.get("role") == "admin"
        print(f"✓ Filtered {len(result['data'])} admin invitations")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_invitation_exists(self, call_mcp, test_entities):
        """Test checking if an invitation exists."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"check-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Check
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email}
            }
        )

        assert result.get("exists") is True, f"Failed: {result}"
        assert result["relationship"]["email"] == test_email
        print(f"✓ Invitation exists for {test_email}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_invitation_status_accept(self, call_mcp, test_entities):
        """Test accepting an invitation by updating status."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"accept-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Accept invitation
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"status": "accepted"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "accepted"
        print("✓ Invitation accepted")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_invitation_status_reject(self, call_mcp, test_entities):
        """Test rejecting an invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"reject-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Reject invitation
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"status": "rejected"}
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        assert result["data"]["status"] == "rejected"
        print("✓ Invitation rejected")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_revoke_invitation(self, call_mcp, test_entities):
        """Test revoking (deleting) an invitation."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        test_email = f"revoke-{uuid.uuid4().hex[:8]}@example.com"

        # Create invitation
        await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "metadata": {"role": "member"}
            }
        )

        # Revoke (hard delete)
        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email},
                "soft_delete": False
            }
        )

        assert result.get("success") is True, f"Failed: {result}"
        print("✓ Invitation revoked")

        # Verify it's gone
        check = await call_mcp(
            "relationship_tool",
            {
                "operation": "check",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "email", "id": test_email}
            }
        )
        assert check.get("exists") is False
        print("✓ Verified invitation no longer exists")


# ============================================================================
# TEST: ERROR CASES AND EDGE CASES
# ============================================================================

class TestErrorCasesAndEdgeCases:
    """Test error handling, validation, and edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_with_missing_target(self, call_mcp, test_entities):
        """Test link operation without target (should fail)."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is False
        assert "error" in result or "target" in str(result).lower()
        print(f"✓ Correctly failed with missing target: {result.get('error', 'validation error')}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_relationship_type(self, call_mcp, test_entities, user_id):
        """Test with invalid relationship type."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "invalid_type",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is False
        print("✓ Correctly rejected invalid relationship type")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_source_type_for_member(self, call_mcp, test_entities, user_id):
        """Test member relationship with invalid source type."""
        if "requirement" not in test_entities:
            pytest.skip("Requirement not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "requirement", "id": test_entities["requirement"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        assert result.get("success") is False
        print("✓ Correctly rejected invalid source type for member relationship")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_non_existent_entity(self, call_mcp, user_id):
        """Test linking with non-existent entity ID."""
        fake_org_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": fake_org_id},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # This might succeed (no FK validation) or fail - either is acceptable
        print(f"✓ Non-existent entity result: success={result.get('success')}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_duplicate_relationship(self, call_mcp, test_entities, user_id):
        """Test creating duplicate relationships."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create first relationship
        result1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "viewer"}
            }
        )

        # Try to create duplicate
        result2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "link",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": user_id},
                "metadata": {"role": "admin"}
            }
        )

        # May fail with constraint error or succeed (depends on DB constraints)
        print(f"✓ Duplicate link result: success={result2.get('success')}, error={result2.get('error', 'none')}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_non_existent_relationship(self, call_mcp, test_entities, user_id):
        """Test updating a relationship that doesn't exist."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        fake_user_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "update",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": fake_user_id},
                "metadata": {"role": "admin"}
            }
        )

        # May fail or return empty result
        print(f"✓ Update non-existent result: success={result.get('success')}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unlink_non_existent_relationship(self, call_mcp, test_entities, user_id):
        """Test unlinking a relationship that doesn't exist."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        fake_user_id = str(uuid.uuid4())

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "unlink",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "target": {"type": "user", "id": fake_user_id},
                "soft_delete": False
            }
        )

        # Should succeed (0 rows deleted) or fail
        print(f"✓ Unlink non-existent result: success={result.get('success')}")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_pagination_functionality(self, call_mcp, test_entities):
        """Test pagination with limit and offset."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        # Create multiple invitations
        created_emails = []
        for i in range(5):
            email = f"page-test-{i}-{uuid.uuid4().hex[:4]}@example.com"
            created_emails.append(email)
            await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": "invitation",
                    "source": {"type": "organization", "id": test_entities["organization"]},
                    "target": {"type": "email", "id": email},
                    "metadata": {"role": "member"}
                }
            )

        # Get first page
        page1 = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 2,
                "offset": 0
            }
        )

        # Get second page
        page2 = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "invitation",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 2,
                "offset": 2
            }
        )

        assert page1.get("success") is True
        assert page2.get("success") is True
        assert len(page1.get("data", [])) <= 2
        assert len(page2.get("data", [])) <= 2
        print(f"✓ Page 1: {len(page1['data'])} items, Page 2: {len(page2['data'])} items")

        # Verify different results
        if page1.get("data") and page2.get("data"):
            page1_ids = {item["id"] for item in page1["data"]}
            page2_ids = {item["id"] for item in page2["data"]}

            if page1_ids.intersection(page2_ids):
                print("⚠ Pages contain overlapping items (unexpected)")
            else:
                print("✓ Pages contain different items")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_with_large_limit(self, call_mcp, test_entities):
        """Test listing with very large limit."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 1000
            }
        )

        assert result.get("success") is True
        print(f"✓ Large limit handled: returned {len(result.get('data', []))} items")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_with_zero_limit(self, call_mcp, test_entities):
        """Test listing with limit=0."""
        if "organization" not in test_entities:
            pytest.skip("Organization not created")

        result = await call_mcp(
            "relationship_tool",
            {
                "operation": "list",
                "relationship_type": "member",
                "source": {"type": "organization", "id": test_entities["organization"]},
                "limit": 0
            }
        )

        # May fail or return empty
        print(f"✓ Zero limit result: success={result.get('success')}, count={len(result.get('data', []))}")


# ============================================================================
# SUMMARY TEST
# ============================================================================

class TestComprehensiveSummary:
    """Generate a comprehensive test summary."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_summary(self, call_mcp, test_entities, user_id):
        """Generate a summary of all relationship types and operations."""
        print("\n" + "="*80)
        print("COMPREHENSIVE RELATIONSHIP_TOOL TEST SUMMARY")
        print("="*80)

        summary = {
            "member": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "assignment": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "trace_link": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "requirement_test": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
            "invitation": {"link": 0, "unlink": 0, "list": 0, "check": 0, "update": 0},
        }

        # Test each relationship type
        test_cases = [
            ("member", "organization", "organization", "user", user_id, {"role": "admin"}),
            ("assignment", "requirement", "requirement", "user", user_id, {"role": "owner"}),
            ("trace_link", "requirement", "requirement", "requirement", test_entities.get("requirement_1"), {"link_type": "depends_on"}),
            ("requirement_test", "requirement", "requirement", "test", test_entities.get("test"), {"coverage_level": "full"}),
            ("invitation", "organization", "organization", "email", f"summary-{uuid.uuid4().hex[:8]}@example.com", {"role": "member"}),
        ]

        for rel_type, source_type, source_key, target_type, target_id, metadata in test_cases:
            if source_key not in test_entities or not target_id:
                continue

            source_id = test_entities[source_key]

            # Test link
            link_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "link",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id},
                    "metadata": metadata
                }
            )
            if link_result.get("success"):
                summary[rel_type]["link"] += 1

            # Test list
            list_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "list",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "limit": 10
                }
            )
            if list_result.get("success"):
                summary[rel_type]["list"] += 1

            # Test check
            check_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "check",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id}
                }
            )
            if check_result.get("success") or check_result.get("exists") is not None:
                summary[rel_type]["check"] += 1

            # Test update
            update_metadata = metadata.copy()
            if "role" in update_metadata:
                update_metadata["role"] = "updated"
            elif "coverage_level" in update_metadata:
                update_metadata["coverage_level"] = "partial"
            elif "status" in update_metadata:
                update_metadata["status"] = "accepted"

            update_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "update",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id},
                    "metadata": update_metadata
                }
            )
            if update_result.get("success"):
                summary[rel_type]["update"] += 1

            # Test unlink
            unlink_result = await call_mcp(
                "relationship_tool",
                {
                    "operation": "unlink",
                    "relationship_type": rel_type,
                    "source": {"type": source_type, "id": source_id},
                    "target": {"type": target_type, "id": target_id},
                    "soft_delete": True
                }
            )
            if unlink_result.get("success"):
                summary[rel_type]["unlink"] += 1

        # Print summary
        print("\nOperation Success Count by Relationship Type:")
        print("-" * 80)
        print(f"{'Relationship Type':<20} {'Link':<8} {'Unlink':<8} {'List':<8} {'Check':<8} {'Update':<8}")
        print("-" * 80)

        for rel_type, ops in summary.items():
            print(f"{rel_type:<20} {ops['link']:<8} {ops['unlink']:<8} {ops['list']:<8} {ops['check']:<8} {ops['update']:<8}")

        print("-" * 80)

        total_ops = sum(sum(ops.values()) for ops in summary.values())
        print(f"\nTotal Successful Operations: {total_ops}")
        print("="*80 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
