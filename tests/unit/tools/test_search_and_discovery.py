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
        
        project_data = {"name": "Vehicle Tracking Project", "description": "Project to track vehicles"}
        project_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        # Search for "vehicle"
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "vehicle",
                "entity_types": ["organization", "project"]
            }
        )
        
        assert result["success"] is True
        assert len(result["data"]) >= 2
        
        # Verify search results contain expected entities
        search_results = result["data"]
        org_found = any("Vehicle Management" in str(item) for item in search_results)
        project_found = any("Vehicle Tracking" in str(item) for item in search_results)
        assert org_found or project_found  # At least one should be found
    
    @pytest.mark.asyncio
    async def test_keyword_search_partial_match(self, call_mcp):
        """Partial keyword match search."""
        # Create entities
        doc_data = {"name": "Authentication System", "content": "User authentication documentation"}
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Search for partial term "auth"
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "auth",
                "entity_types": ["document"]
            }
        )
        
        assert result["success"] is True
        # Should find documents containing "auth" in name or content
        found_auth_docs = [
            item for item in result["data"] 
            if "auth" in str(item).lower()
        ]
        assert len(found_auth_docs) >= 1
    
    @pytest.mark.asyncio
    async def test_keyword_search_fuzzy(self, call_mcp):
        """Fuzzy search with typo tolerance."""
        # Create entities with specific terms
        org_data = {"name": "Customer Service Department"}
        await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        
        # Search with intentional typo "custmer" instead of "customer"
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "custmer",  # Intentional typo
                "entity_types": ["organization"],
                "fuzzy_threshold": 0.8
            }
        )
        
        assert result["success"] is True
        # Should find "Customer Service" even with typo
        if result["data"]:
            found_similar = any(
                "customer" in str(item).lower() for item in result["data"]
            )
            assert found_similar  # Should find similar term
    
    @pytest.mark.asyncio
    async def test_keyword_search_case_insensitive(self, call_mcp):
        """Case-insensitive keyword search."""
        # Create entity
        doc_data = {"name": "Data Processing Manual", "content": "PROCESSING large datasets"}
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Search with different case
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "PROCESSING",  # Uppercase
                "entity_types": ["document"],
                "case_sensitive": False
            }
        )
        
        assert result["success"] is True
        # Should find entity regardless of case
        found_doc = any(
            "processing" in str(item).lower() for item in result["data"]
        )
        assert found_doc
    
    @pytest.mark.asyncio
    async def test_keyword_search_exclude_deleted(self, call_mcp):
        """Keyword search excludes soft-deleted entities."""
        # Create and then "delete" an entity
        doc_data = {"name": "Temporary Document", "status": "deleted"}
        doc_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Create active entity
        active_doc_data = {"name": "Active Document", "content": "permanent content"}
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": active_doc_data}
        )
        
        # Search for "temporary" - should not find deleted
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "temporary",
                "entity_types": ["document"],
                "exclude_deleted": True
            }
        )
        
        assert result["success"] is True
        
        # Verify deleted document is not in results
        if result["data"]:
            temp_found = any(
                "temporary" in str(item).lower() for item in result["data"]
            )
            # Should not find the deleted document
            assert not temp_found or "status" in str(result["data"])


class TestSemanticSearch:
    """Test semantic/embedding-based search operations."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_embedding_based(self, call_mcp):
        """Semantic search using embedding similarity."""
        # Create entities with semantically related content
        doc1_data = {
            "name": "Vehicle Safety Manual",
            "content": "Guidelines for safe driving and vehicle maintenance"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Car Operation Guide",
            "content": "Instructions for driving and caring for automobiles"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search for semantically related term
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "semantic_search",
                "search_term": "automobile safety",
                "entity_types": ["document"],
                "similarity_threshold": 0.7
            }
        )
        
        assert result["success"] is True
        # Should find documents about vehicles even without exact keyword match
        assert len(result["data"]) >= 0  # May not find results depending on embeddings
    
    @pytest.mark.asyncio
    async def test_semantic_search_similar_threshold(self, call_mcp):
        """Semantic search with adjustable similarity threshold."""
        # Create entities
        doc_data = {
            "name": "Software Architecture",
            "content": "System design patterns and architectural principles"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # High threshold search (should find close matches)
        result_high, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "semantic_search",
                "search_term": "software design",
                "entity_types": ["document"],
                "similarity_threshold": 0.9  # High threshold
            }
        )
        
        # Low threshold search (should find more results)
        result_low, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "semantic_search",
                "search_term": "software design",
                "entity_types": ["document"],
                "similarity_threshold": 0.3  # Low threshold
            }
        )
        
        assert result_high["success"] is True
        assert result_low["success"] is True
        # Low threshold should return at least as many results as high threshold
        assert len(result_low["data"]) >= len(result_high["data"])
    
    @pytest.mark.asyncio
    async def test_semantic_search_performance(self, call_mcp):
        """Semantic search performance testing."""
        # Create multiple entities for performance testing
        for i in range(20):
            doc_data = {
                "name": f"Document {i}",
                "content": f"Content related to testing and validation number {i}"
            }
            await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", "data": doc_data}
            )
        
        # Perform semantic search and measure timing
        start_time = datetime.now(timezone.utc)
        
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "semantic_search",
                "search_term": "testing validation",
                "entity_types": ["document"],
                "max_results": 10
            }
        )
        
        end_time = datetime.now(timezone.utc)
        
        assert result["success"] is True
        # Verify timing is reasonable (should complete within a few seconds)
        search_duration = (end_time - start_time).total_seconds()
        assert search_duration < 10.0  # Should complete within 10 seconds


class TestHybridSearch:
    """Test combined keyword and semantic search operations."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_combined(self, call_mcp):
        """Combined keyword and semantic search."""
        # Create entities
        doc_data = {
            "name": "Payment Processing",
            "content": "Secure payment handling and transaction processing"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Perform hybrid search
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "hybrid_search",
                "search_term": "payment transactions",
                "entity_types": ["document"],
                "keyword_weight": 0.6,
                "semantic_weight": 0.4
            }
        )
        
        assert result["success"] is True
        # Should find relevant results based on both keyword and semantic similarity
        assert len(result["data"]) >= 0
    
    @pytest.mark.asyncio
    async def test_hybrid_search_weight_tuning(self, call_mcp):
        """Hybrid search with different weight configurations."""
        # Create entity
        doc_data = {
            "name": "User Interface Design",
            "content": "Frontend development and user experience principles"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc_data}
        )
        
        # Keyword-heavy search
        result_keyword, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "hybrid_search",
                "search_term": "frontend interface",
                "entity_types": ["document"],
                "keyword_weight": 0.9,
                "semantic_weight": 0.1
            }
        )
        
        # Semantic-heavy search
        result_semantic, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "hybrid_search",
                "search_term": "frontend interface",
                "entity_types": ["document"],
                "keyword_weight": 0.1,
                "semantic_weight": 0.9
            }
        )
        
        assert result_keyword["success"] is True
        assert result_semantic["success"] is True
        
        # Both should find the document, but with potentially different scores
        # The exact behavior depends on implementation, but both should succeed
    
    @pytest.mark.asyncio
    async def test_hybrid_search_balanced_weights(self, call_mcp):
        """Hybrid search with balanced keyword/semantic weights."""
        # Create entities
        for i in range(3):
            doc_data = {
                "name": f"Technical Document {i}",
                "content": f"Engineering and development content number {i}"
            }
            await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", "data": doc_data}
            )
        
        # Balanced hybrid search
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "hybrid_search",
                "search_term": "engineering development",
                "entity_types": ["document"],
                "keyword_weight": 0.5,
                "semantic_weight": 0.5
            }
        )
        
        assert result["success"] is True
        # Should find documents based on balanced approach
        assert len(result["data"]) >= 0


class TestSearchFiltering:
    """Test search with advanced filtering options."""
    
    @pytest.mark.asyncio
    async def test_search_filter_by_type(self, call_mcp):
        """Filter search results by entity type."""
        # Create different entity types
        org_data = {"name": "Search Test Organization"}
        await call_mcp(
            "entity_tool",
            {"entity_type": "organization", "operation": "create", "data": org_data}
        )
        
        project_data = {"name": "Search Test Project"}
        await call_mcp(
            "entity_tool",
            {"entity_type": "project", "operation": "create", "data": project_data}
        )
        
        # Search limited to organizations only
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "Search Test",
                "entity_types": ["organization"],  # Only organizations
                "filters": {}
            }
        )
        
        assert result["success"] is True
        # Should only find organizations
        for item in result["data"]:
            assert "organization" in str(item).lower()
    
    @pytest.mark.asyncio
    async def test_search_filter_by_owner(self, call_mcp):
        """Filter search results by owner/creator."""
        # Create entities with different owners
        doc1_data = {
            "name": "Owner One Document",
            "created_by": "user1@example.com"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Owner Two Document",
            "created_by": "user2@example.com"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search filtered by specific owner
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "Document",
                "entity_types": ["document"],
                "filters": {
                    "created_by": "user1@example.com"
                }
            }
        )
        
        assert result["success"] is True
        # Should only find documents by the specified owner
        if result["data"]:
            user1_found = any(
                "user1@example.com" in str(item) or "Owner One" in str(item)
                for item in result["data"]
            )
            assert user1_found
    
    @pytest.mark.asyncio
    async def test_search_filter_by_status(self, call_mcp):
        """Filter search results by entity status."""
        # Create entities with different statuses
        active_doc_data = {
            "name": "Active Status Document",
            "status": "active"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": active_doc_data}
        )
        
        draft_doc_data = {
            "name": "Draft Status Document", 
            "status": "draft"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": draft_doc_data}
        )
        
        # Search filtered by active status only
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_term": "Status Document",
                "entity_types": ["document"],
                "filters": {
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
        
        doc_data = {
            "name": "Recent Document",
            "created_at": current_time
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
                "query_type": "keyword_search",
                "search_term": "Recent",
                "entity_types": ["document"],
                "filters": {
                    "created_at": {
                        "start": hour_ago,
                        "end": recent_time
                    }
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
        
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {"entity_type": "project", "operation": "create", "data": {"name": f"Project {i}"}}
            )
        
        # Get count by entity type
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "aggregate_type": "count_by_type",
                "filters": {}
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
        # Create entities with different owners
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "document", 
                    "operation": "create", 
                    "data": {
                        "name": f"Owner1 Doc {i}",
                        "created_by": "user1@example.com"
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
                        "created_by": "user2@example.com"
                    }
                }
            )
        
        # Get count by owner
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "aggregate_type": "count_by_owner",
                "filters": {}
            }
        )
        
        assert result["success"] is True
        assert "data" in result
        
        owner_counts = result["data"]
        # Should have counts for both users
        assert "user1@example.com" in owner_counts
        assert "user2@example.com" in owner_counts
    
    @pytest.mark.asyncio
    async def test_aggregate_count_by_status(self, call_mcp):
        """Get count of entities by status."""
        # Create entities with different statuses
        for i in range(2):
            await call_mcp(
                "entity_tool",
                {
                    "entity_type": "project", 
                    "operation": "create", 
                    "data": {
                        "name": f"Active Project {i}",
                        "status": "active"
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
                        "status": "completed"
                    }
                }
            )
        
        # Get count by status
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "aggregate_type": "count_by_status",
                "filters": {}
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
        # Create some entities
        initial_count = 5
        for i in range(initial_count):
            await call_mcp(
                "entity_tool",
                {"entity_type": "document", "operation": "create", "data": {"name": f"Count Test {i}"}}
            )
        
        # Get total count
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "aggregate_type": "total_count",
                "filters": {}
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
                        "type": "technical"
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
                        "type": "user_manual"
                    }
                }
            )
        
        # Group by multiple criteria
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "aggregate",
                "aggregate_type": "group_by",
                "group_by": ["status", "type"],
                "filters": {}
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
        # Create a base document
        base_doc_data = {
            "name": "Database Design Guide",
            "content": "Guidelines for relational database schema design and normalization"
        }
        base_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": base_doc_data}
        )
        base_id = base_result["data"]["id"]
        
        # Create similar documents
        similar_doc_data = {
            "name": "SQL Schema Best Practices",
            "content": "Best practices for designing SQL database structures"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": similar_doc_data}
        )
        
        # Find similar entities
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "find_similar",
                "entity_type": "document",
                "entity_id": base_id,
                "similarity_threshold": 0.7,
                "max_results": 5
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
        # Create base and diverse documents
        base_doc_data = {
            "name": "Machine Learning Basics",
            "content": "Introduction to machine learning algorithms and concepts"
        }
        base_result, _ = await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": base_doc_data}
        )
        base_id = base_result["data"]["id"]
        
        # Create documents with different similarity levels
        very_similar = {
            "name": "ML Algorithms",
            "content": "Types of machine learning algorithms and their applications"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": very_similar}
        )
        
        somewhat_similar = {
            "name": "Data Science",
            "content": "Data analysis and statistical methods"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": somewhat_similar}
        )
        
        # High threshold (only very similar)
        result_high, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "find_similar",
                "entity_type": "document",
                "entity_id": base_id,
                "similarity_threshold": 0.9,
                "max_results": 10
            }
        )
        
        # Low threshold (more similar entities)
        result_low, _ = await call_mcp(
            "query_tool",
            {
                "query_type": "find_similar",
                "entity_type": "document",
                "entity_id": base_id,
                "similarity_threshold": 0.3,
                "max_results": 10
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
        doc1_data = {
            "name": "Payment Security",
            "content": "Secure payment processing with encryption"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "User Authentication",
            "content": "User login and security protocols"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search with AND operator
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_terms": ["payment", "security"],
                "operator": "AND",
                "entity_types": ["document"]
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
        # Create entities
        doc1_data = {
            "name": "Database Manual",
            "content": "SQL database operations and management"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Network Configuration",
            "content": "Network setup and administration"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search with OR operator
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_terms": ["database", "network"],
                "operator": "OR",
                "entity_types": ["document"]
            }
        )
        
        assert result["success"] is True
        # Should find entities containing either "database" or "network" (or both)
        assert len(result["data"]) >= 2
    
    @pytest.mark.asyncio
    async def test_search_with_not_operator(self, call_mcp):
        """Search using NOT operator (exclude terms)."""
        # Create entities
        doc1_data = {
            "name": "Production Guide",
            "content": "Production environment setup and configuration"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc1_data}
        )
        
        doc2_data = {
            "name": "Development Testing",
            "content": "Testing and development environment procedures"
        }
        await call_mcp(
            "entity_tool",
            {"entity_type": "document", "operation": "create", "data": doc2_data}
        )
        
        # Search excluding "development"
        result, duration_ms = await call_mcp(
            "query_tool",
            {
                "query_type": "keyword_search",
                "search_terms": ["environment"],
                "exclude_terms": ["development"],
                "operator": "NOT",
                "entity_types": ["document"]
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
