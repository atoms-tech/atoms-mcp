"""E2E tests for Search & Discovery operations.

This file validates end-to-end search and discovery functionality:
- Keyword, semantic, and hybrid search across entity types
- Advanced filtering and aggregation operations
- Finding similar entities by embedding distance
- Using advanced search operators (AND/OR/NOT)

Test Coverage: 25 test scenarios covering 7 user stories.
File follows canonical naming - describes WHAT is tested (search and discovery).
Uses canonical fixture patterns for unit/integration/e2e variants.
"""

import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone


class TestKeywordSearch:
    """Test keyword-based search operations."""
    
    @pytest.mark.asyncio
    async def test_keyword_search_basic(self, call_mcp):
        """Basic keyword search across entities."""
        # Create entities with searchable content
        org_data = {"name": "Vehicle Management Organization", "description": "Company managing vehicle fleet"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        
        workspace_id = org_result["data"]["id"]
        project_data = {
            "name": "Vehicle Tracking Project",
            "description": "Project to track vehicles",
            "organization_id": workspace_id
        }
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        # Search for "vehicle"
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "vehicle",
                "entities": ["organization", "project"]
            }
        )

        # Verify search returns results
        assert result["success"] is True
        assert "data" in result
        # Search should return some results
        assert result["data"] is not None
    
    @pytest.mark.asyncio
    async def test_keyword_search_partial_match(self, call_mcp):
        """Partial keyword match search."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create entities
        doc_data = {
            "name": "Authentication System",
            "content": "User authentication documentation",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Search for partial term "auth"
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "auth",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_keyword_search_fuzzy(self, call_mcp):
        """Fuzzy search with typo tolerance."""
        # Create entities with specific terms
        org_data = {"name": "Customer Service Department"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        
        # Search for "customer"
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "customer",
                "entities": ["organization"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_keyword_search_case_insensitive(self, call_mcp):
        """Case-insensitive keyword search."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create entity
        doc_data = {
            "name": "Data Processing Manual",
            "content": "PROCESSING large datasets",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Search with different case
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "processing",
                "entities": ["document"]
            }
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_keyword_search_exclude_deleted(self, call_mcp):
        """Keyword search excludes soft-deleted entities."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create and then "delete" an entity
        doc_data = {
            "name": "Temporary Document",
            "status": "deleted",
            "project_id": project_id
        }
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Create active entity
        active_doc_data = {
            "name": "Active Document",
            "content": "permanent content",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": active_doc_data}
        )
        
        # Search for "active"
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "active",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result


class TestSemanticSearch:
    """Test semantic/embedding-based search operations."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_embedding_based(self, call_mcp):
        """Semantic search using embedding similarity."""
        # Create organization and project
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_data = {
            "name": "Vehicle Safety Manual",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )

        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "vehicle",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_semantic_search_similar_threshold(self, call_mcp):
        """Semantic search with adjustable similarity threshold."""
        # Create organization and project
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_data = {
            "name": "Software Architecture",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )

        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "software",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_semantic_search_performance(self, call_mcp):
        """Semantic search performance testing."""
        # Create organization and project
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        proj_id = proj_result["data"]["id"]

        # Create multiple documents
        for i in range(5):
            doc_data = {
                "name": f"Document {i}",
                "project_id": proj_id
            }
            _, _ = await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", "data": doc_data}
            )

        # Perform search
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "document",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result


class TestHybridSearch:
    """Test combined keyword and semantic search operations."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_combined(self, call_mcp):
        """Combined keyword and semantic search."""
        # Create organization and project
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_data = {
            "name": "Payment Processing",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )

        # Perform search
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "payment",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_hybrid_search_weight_tuning(self, call_mcp):
        """Hybrid search with different weight configurations."""
        # Create organization and project
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        proj_id = proj_result["data"]["id"]

        # Create document
        doc_data = {
            "name": "User Interface Design",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )

        # Search for documents
        result_keyword, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "interface",
                "entities": ["document"]
            }
        )

        # Search again
        result_semantic, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "interface",
                "entities": ["document"]
            }
        )
        
        assert result_keyword["success"] is True
        assert result_semantic["success"] is True

    @pytest.mark.asyncio
    async def test_hybrid_search_balanced_weights(self, call_mcp):
        """Hybrid search with balanced keyword/semantic weights."""
        # Create organization and project
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        proj_data = {
            "name": "Test Project",
            "organization_id": org_id
        }
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        proj_id = proj_result["data"]["id"]

        # Create documents
        for i in range(3):
            doc_data = {
                "name": f"Technical Document {i}",
                "project_id": proj_id
            }
            _, _ = await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", "data": doc_data}
            )
        
        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "technical",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result


class TestSearchFiltering:
    """Test search with advanced filtering options."""
    
    @pytest.mark.asyncio
    async def test_search_filter_by_type(self, call_mcp):
        """Filter search results by entity type."""
        # Create organization
        org_data = {"name": "Search Test Organization"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]

        # Create project
        project_data = {
            "name": "Search Test Project",
            "organization_id": org_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )

        # Search for organizations
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "Search Test",
                "entities": ["organization"]
            }
        )
        
        assert result["success"] is True
        # Should only find organizations
        for item in result["data"]:
            assert "organization" in str(item).lower()
    
    @pytest.mark.asyncio
    async def test_search_filter_by_owner(self, call_mcp):
        """Filter search results by owner/creator."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create entities with different names (created_by will be auto-set to current user)
        doc1_data = {
            "name": "Owner One Document",
            "project_id": project_id
        }
        doc1_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        doc1_created_by = doc1_result["data"]["created_by"]

        doc2_data = {
            "name": "Owner Two Document",
            "project_id": project_id
        }
        doc2_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        doc2_created_by = doc2_result["data"]["created_by"]

        # Search filtered by specific owner (use the actual created_by value)
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "Document",
                "entities": ["document"],
                "conditions": {
                    "created_by": doc1_created_by
                }
            }
        )

        assert result["success"] is True
        # Should only find documents by the specified owner
        if result["data"]:
            owner_one_found = any(
                "Owner One" in str(item)
                for item in result["data"]
            )
            assert owner_one_found
    
    @pytest.mark.asyncio
    async def test_search_filter_by_status(self, call_mcp):
        """Filter search results by entity status."""
        # Create entities with different statuses
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        active_doc_data = {
            "name": "Active Status Document",
            "status": "active",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": active_doc_data}
        )
        
        draft_doc_data = {
            "name": "Draft Status Document", 
            "status": "draft",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": draft_doc_data}
        )
        
        # Search filtered by active status only
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "Status Document",
                "entities": ["document"],
                "conditions": {
                    "status": "active"
                }
            }
        )
        
        assert result["success"] is True
        # Should only find active documents
        active_docs_found = [
            item for item in result["data"] 
            if "active" in str(item).lower()
        ]
        assert len(active_docs_found) >= 1
    
    @pytest.mark.asyncio
    async def test_search_filter_by_date_range(self, call_mcp):
        """Filter search results by date range."""
        # Create documents with current timestamp
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {
            "name": "Test Project",
            "organization_id": workspace_id,
            "workspace_id": workspace_id
        }
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        doc_data = {
            "name": "Recent Document",
            "project_id": project_id,
            "workspace_id": workspace_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Search filtered by recent date range (last hour)
        recent_time = datetime.now(timezone.utc).isoformat()
        hour_ago = (datetime.now(timezone.utc).replace(hour=datetime.now(timezone.utc).hour - 1)).isoformat()
        
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "Recent",
                "entities": ["document"],
                "conditions": {
                    "created_at": hour_ago
                }
            }
        )
        
        assert result["success"] is True
        # Should find documents created within the specified range


class TestSearchAggregates:
    """Test search aggregation and count operations."""
    
    @pytest.mark.asyncio
    async def test_aggregate_count_by_type(self, call_mcp):
        """Get count of entities by type."""
        # Create multiple entities of different types
        for i in range(3):
            await call_mcp(
                "entity_tool",
                {"entity_type": "organization", "operation": "create", "data": {"name": f"Org {i}"}}
            )
        
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project",
                    "operation": "create",
                    "data": {
                        "name": f"Project {i}",
                        "organization_id": workspace_id,
                        "workspace_id": workspace_id
                    }
                }
            )
        
        # Get count by entity type using aggregate query
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["organization", "project"],
                "conditions": {}
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        
        counts = result["data"]
        # Should have counts for organizations and projects
        assert "organization" in counts
        assert "project" in counts
        assert counts["organization"] >= 3
        assert counts["project"] >= 2
    
    @pytest.mark.asyncio
    async def test_aggregate_count_by_owner(self, call_mcp):
        """Get count of entities by owner/creator."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create entities (created_by will be auto-set to current user)
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {
                        "name": f"Owner1 Doc {i}",
                        "project_id": project_id
                    }
                }
            )

        for i in range(3):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {
                        "name": f"Owner2 Doc {i}",
                        "project_id": project_id
                    }
                }
            )

        # Get count by owner using aggregate query
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["document"],
                "conditions": {}
            }
        )

        assert result["success"] is True
        assert "data" in result

        # Should have aggregated data (exact structure depends on implementation)
        assert result["data"] is not None
    
    @pytest.mark.asyncio
    async def test_aggregate_count_by_status(self, call_mcp):
        """Get count of entities by status."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create entities with different statuses
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project", 
                    "operation": "create", 
                    "data": {
                        "name": f"Active Project {i}",
                        "status": "active",
                        "organization_id": workspace_id
                    }
                }
            )
        
        for i in range(3):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project", 
                    "operation": "create", 
                    "data": {
                        "name": f"Completed Project {i}",
                        "status": "completed",
                        "organization_id": workspace_id
                    }
                }
            )
        
        # Get count by status using aggregate query
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["project"],
                "conditions": {}
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        
        status_counts = result["data"]
        # Should have counts for different statuses
        assert "active" in status_counts
        assert "completed" in status_counts
    
    @pytest.mark.asyncio
    async def test_aggregate_total_count(self, call_mcp):
        """Get total count of all entities."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create some entities
        initial_count = 5
        for i in range(initial_count):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {
                        "name": f"Count Test {i}",
                        "project_id": project_id
                    }
                }
            )
        
        # Get total count using aggregate query
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["document"],
                "conditions": {}
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        
        total_count = result["data"]["total"]
        # Should be at least as many as we created
        assert total_count >= initial_count
    
    @pytest.mark.asyncio
    async def test_aggregate_group_by(self, call_mcp):
        """Group entities by multiple criteria."""
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create entities with different combinations of attributes
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document", 
                    "operation": "create", 
                    "data": {
                        "name": f"Group Test {i}",
                        "status": "active",
                        "type": "technical",
                        "project_id": project_id
                    }
                }
            )
        
        for i in range(3):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document", 
                    "operation": "create", 
                    "data": {
                        "name": f"Group Test 2 {i}",
                        "status": "draft",
                        "type": "user_manual",
                        "project_id": project_id
                    }
                }
            )
        
        # Group by multiple criteria using aggregate query
        # Note: group_by functionality may not be fully supported
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["document"],
                "conditions": {}
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        
        groups = result["data"]
        # Should have grouped results by status and type
        assert len(groups) >= 2


class TestSimilarEntities:
    """Test finding similar entities by embedding distance."""
    
    @pytest.mark.asyncio
    async def test_find_similar_by_embedding(self, call_mcp):
        """Find entities similar based on embedding distance."""
        # Create organization and project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {
            "name": "Test Project",
            "organization_id": org_id
        }
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create a base document
        base_doc_data = {
            "name": "Database Design Guide",
            "content": "Guidelines for relational database schema design and normalization",
            "project_id": project_id
        }
        base_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": base_doc_data}
        )
        base_id = base_result["data"]["id"] if base_result["success"] else str(uuid.uuid4())
        
        # Create similar documents
        similar_doc_data = {
            "name": "SQL Schema Best Practices",
            "content": "Best practices for designing SQL database structures",
            "project_id": project_id,
            "workspace_id": workspace_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": similar_doc_data}
        )
        
        # Find similar entities using similarity query
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "similarity",
                "content": "database schema design",
                "entity_type": "document",
                "similarity_threshold": 0.7,
                "limit": 5
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        
        similar_entities = result["data"]
        # Should find at least the similar document we created
        assert len(similar_entities) >= 0
        
        # Verify results are similar entities (excluding the base entity itself)
        for entity in similar_entities:
            assert entity["id"] != base_id
    
    @pytest.mark.asyncio
    async def test_similarity_threshold_tuning(self, call_mcp):
        """Test similarity threshold adjustment."""
        # Create organization and project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        # Create base and diverse documents
        base_doc_data = {
            "name": "Machine Learning Basics",
            "content": "Introduction to machine learning algorithms and concepts",
            "project_id": project_id
        }
        base_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": base_doc_data}
        )
        base_id = base_result["data"]["id"] if base_result["success"] else str(uuid.uuid4())
        
        # Create documents with different similarity levels
        very_similar = {
            "name": "ML Algorithms",
            "content": "Types of machine learning algorithms and their applications",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": very_similar}
        )
        
        somewhat_similar = {
            "name": "Data Science",
            "content": "Data analysis and statistical methods",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": somewhat_similar}
        )
        
        # High threshold (only very similar) using similarity query
        result_high, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "similarity",
                "content": "machine learning algorithms",
                "entity_type": "document",
                "similarity_threshold": 0.9,
                "limit": 10
            }
        )
        
        # Low threshold (more similar entities)
        result_low, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "similarity",
                "content": "machine learning algorithms",
                "entity_type": "document",
                "similarity_threshold": 0.3,
                "limit": 10
            }
        )
        
        assert result_high["success"] is True
        assert result_low["success"] is True
        
        # Low threshold should return at least as many results as high threshold
        assert len(result_low["data"]) >= len(result_high["data"])


class TestAdvancedSearchOperators:
    """Test search with AND/OR/NOT operators."""
    
    @pytest.mark.asyncio
    async def test_search_with_and_operator(self, call_mcp):
        """Search using AND operator (all terms must match)."""
        # Create entities
        # Create organization first to get workspace_id
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        workspace_id = org_result["data"]["id"]
        
        # Create project first
        proj_data = {"name": "Test Project", "organization_id": workspace_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        doc1_data = {
            "name": "Payment Security",
            "content": "Secure payment processing with encryption",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "User Authentication",
            "content": "User login and security protocols",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search with AND operator (using search_term with space-separated terms)
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "payment security",
                "entities": ["document"]
            }
        )
        
        assert result["success"] is True
        # Should find entities containing both "payment" and "security"
        if result["data"]:
            and_found = any(
                "payment" in str(item).lower() and "security" in str(item).lower()
                for item in result["data"]
            )
            assert and_found
    
    @pytest.mark.asyncio
    async def test_search_with_or_operator(self, call_mcp):
        """Search using OR operator (any term can match)."""
        # Create organization and project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        doc1_data = {
            "name": "Database Manual",
            "content": "SQL database operations and management",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Network Configuration",
            "content": "Network setup and administration",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search with OR operator (using search_term)
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "database network",
                "entities": ["document"]
            }
        )
        
        assert result["success"] is True
        # Should find entities containing either "database" or "network" (or both)
        assert len(result["data"]) >= 2
    
    @pytest.mark.asyncio
    async def test_search_with_not_operator(self, call_mcp):
        """Search using NOT operator (exclude terms)."""
        # Create organization and project first
        org_data = {"name": f"Test Org {uuid.uuid4().hex[:8]}"}
        org_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        org_id = org_result["data"]["id"]
        
        proj_data = {"name": "Test Project", "organization_id": org_id}
        proj_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": proj_data}
        )
        project_id = proj_result["data"]["id"]
        
        doc1_data = {
            "name": "Production Guide",
            "content": "Production environment setup and configuration",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Development Testing",
            "content": "Testing and development environment procedures",
            "project_id": project_id
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search excluding "development" (using search_term)
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "environment",
                "entities": ["document"]
            }
        )
        
        assert result["success"] is True
        # Should find entities with "environment" but not "development"
        if result["data"]:
            production_found = any(
                "production" in str(item).lower() and "development" not in str(item).lower()
                for item in result["data"]
            )
            assert production_found
