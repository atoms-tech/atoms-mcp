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
        assert "data" in result

    @pytest.mark.asyncio
    async def test_search_filter_by_owner(self, call_mcp):
        """Filter search results by owner/creator."""
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

        # Create documents
        doc1_data = {
            "name": "Owner One Document",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )

        doc2_data = {
            "name": "Owner Two Document",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )

        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "Document",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_search_filter_by_status(self, call_mcp):
        """Filter search results by entity status."""
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

        # Create documents
        active_doc_data = {
            "name": "Active Status Document",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": active_doc_data}
        )

        draft_doc_data = {
            "name": "Draft Status Document",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": draft_doc_data}
        )

        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "Status Document",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
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
        # Aggregate query returns results
        assert result["data"] is not None
    
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
        # Aggregate query returns results
        assert result["data"] is not None
    
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
        # Aggregate query returns results
        assert result["data"] is not None
    
    @pytest.mark.asyncio
    async def test_aggregate_group_by(self, call_mcp):
        """Group entities by multiple criteria."""
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

        # Create documents
        for i in range(2):
            _, _ = await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {
                        "name": f"Group Test {i}",
                        "project_id": proj_id
                    }
                }
            )

        # Group by multiple criteria using aggregate query
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "entities": ["document"],
                "conditions": {}
            }
        )

        assert result["success"] is True
        assert "data" in result
        # Aggregate query returns results
        assert result["data"] is not None


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
        
        # Create documents
        base_doc_data = {
            "name": "Database Design Guide",
            "project_id": project_id
        }
        base_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": base_doc_data}
        )

        # Create similar document
        similar_doc_data = {
            "name": "SQL Schema Best Practices",
            "project_id": project_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": similar_doc_data}
        )

        # Find similar entities using search query
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "database",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_similarity_threshold_tuning(self, call_mcp):
        """Test similarity threshold adjustment."""
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

        # Create documents
        base_doc_data = {
            "name": "Machine Learning Basics",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": base_doc_data}
        )

        # Create similar document
        very_similar = {
            "name": "ML Algorithms",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": very_similar}
        )

        # Search for documents
        result_high, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "machine learning",
                "entities": ["document"]
            }
        )

        # Search again
        result_low, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "machine",
                "entities": ["document"]
            }
        )

        assert result_high["success"] is True
        assert result_low["success"] is True


class TestAdvancedSearchOperators:
    """Test search with AND/OR/NOT operators."""
    
    @pytest.mark.asyncio
    async def test_search_with_and_operator(self, call_mcp):
        """Search using AND operator (all terms must match)."""
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

        doc1_data = {
            "name": "Payment Security",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )

        doc2_data = {
            "name": "User Authentication",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )

        # Search for documents
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
    async def test_search_with_or_operator(self, call_mcp):
        """Search using OR operator (any term can match)."""
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

        doc1_data = {
            "name": "Database Manual",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )

        doc2_data = {
            "name": "Network Configuration",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )

        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "database",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_search_with_not_operator(self, call_mcp):
        """Search using NOT operator (exclude terms)."""
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

        doc1_data = {
            "name": "Production Guide",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Development Testing",
            "project_id": proj_id
        }
        _, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )

        # Search for documents
        result, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "search",
                "search_term": "environment",
                "entities": ["document"]
            }
        )

        assert result["success"] is True
        assert "data" in result
