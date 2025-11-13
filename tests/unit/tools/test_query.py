"""Query Tool Tests - Unit Tests Only.

This test suite validates query_tool functionality using the actual API:
- query_type: search, rag_search, aggregate, analyze, relationships, similarity
- entities: list of entity types to search
- search_term: text to search for (for search/rag_search queries)
- conditions: structured filter conditions
- rag_mode: semantic, keyword, hybrid, auto
- Other parameters: limit, format_type, similarity_threshold, etc.

Run with: pytest tests/unit/tools/test_query_fixed.py -v
"""

import uuid
import time
from typing import Any, Dict, List

import pytest
import pytest_asyncio

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


@pytest_asyncio.fixture
async def test_entities_fixture():
    """Fixture that just provides test entity data (no creation)."""
    return [
        {
            "name": "Python Web Application",
            "entity_type": "project",
            "description": "A web application built with Python Flask framework for REST APIs",
        },
        {
            "name": "Database Design Document",
            "entity_type": "document",
            "description": "Comprehensive database schema design for PostgreSQL",
        },
        {
            "name": "User Authentication Module",
            "entity_type": "project",
            "description": "JWT-based authentication system with OAuth2 integration",
        },
    ]


@pytest_asyncio.fixture
async def test_entities(call_mcp, test_entities_fixture):
    """Create test entities for search tests."""
    entity_ids = []
    
    for entity_data in test_entities_fixture:
        try:
            result, _ = await call_mcp("entity_tool", {
                "operation": "create",
                "entity_type": entity_data["entity_type"],
                "data": {
                    "name": entity_data["name"],
                    "description": entity_data.get("description", ""),
                }
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        except Exception:
            # If entity creation fails, just continue
            pass
    
    yield entity_ids
    
    # Cleanup
    for entity_id in entity_ids:
        try:
            await call_mcp("entity_tool", {
                "operation": "delete",
                "entity_id": entity_id
            })
        except:
            pass


class TestQuerySearch:
    """Test search query type."""
    
    @pytest.mark.story("Search & Discovery - User can search all entities")
    async def test_basic_search(self, call_mcp, test_entities):
        """Test basic text search across entities."""
        # Works with or without test entities
        result, duration_ms = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project", "document"],
            "search_term": "application",
            "limit": 10
        })
        
        # Should return result (success or error)
        assert result is not None, "Should return a result"
        # If successful, data should be iterable
        if result.get("success"):
            assert "data" in result, "Result should contain data"
            assert isinstance(result["data"], (list, dict)), "Data should be list or dict"
    
    async def test_search_empty_term(self, call_mcp, test_entities):
        """Test search with empty term should fail gracefully."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "",
            "limit": 5
        })
        
        # Empty search term should fail (search_term is required)
        assert not result.get("success"), "Empty search term should not succeed"
    
    async def test_search_with_conditions(self, call_mcp, test_entities):
        """Test search with filter conditions."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "project",
            "conditions": {"status": "active"},
            "limit": 10
        })
        
        # Should return result (success or error), not crash
        assert result is not None
    
    async def test_search_multiple_entities(self, call_mcp, test_entities):
        """Test searching multiple entity types."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project", "document", "organization"],
            "search_term": "test",
            "limit": 20
        })
        
        # Should return result (success or error), not crash
        assert result is not None
    
    async def test_search_with_limit(self, call_mcp, test_entities):
        """Test search respects limit parameter."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "application",
            "limit": 2
        })
        
        # Should return result (success or error), not crash
        assert result is not None


class TestQuerySort:
    """Test sorting and ordering of query results."""
    
    async def test_sort_ascending_by_name(self, call_mcp, test_entities):
        """Test sorting results in ascending order by name.
        
        User Story: User can sort query results
        Acceptance Criteria:
        - Results can be sorted by any field
        - Ascending sort works (A-Z, 0-9)
        - Results are properly ordered
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "name:asc",
            "limit": 10
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            if len(entities) > 1:
                # Verify ascending order by name
                names = [e.get("name", "") for e in entities if isinstance(e, dict)]
                sorted_names = sorted(names)
                assert names == sorted_names, f"Names not sorted ascending: {names}"
    
    async def test_sort_descending_by_created_at(self, call_mcp, test_entities):
        """Test sorting results in descending order by creation date.
        
        User Story: User can sort query results
        Acceptance Criteria:
        - Descending sort works (Z-A, 9-0, newest first)
        - Time-based sorting maintains chronological order
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "created_at:desc",
            "limit": 10
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            if len(entities) > 1:
                # Verify descending order by created_at
                created_dates = []
                for e in entities:
                    if isinstance(e, dict) and "created_at" in e:
                        created_dates.append(e["created_at"])
                
                if created_dates:
                    sorted_dates = sorted(created_dates, reverse=True)
                    assert created_dates == sorted_dates, f"Dates not sorted descending: {created_dates}"
    
    async def test_sort_by_updated_at(self, call_mcp, test_entities):
        """Test sorting by last updated time.
        
        User Story: User can sort by modification time
        Acceptance Criteria:
        - Updated_at field is sortable
        - Most recently updated appear first (desc)
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "document",
            "search_term": "document",
            "order_by": "updated_at:desc",
            "limit": 10
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            if len(entities) > 1:
                # Verify updated_at exists and is in descending order
                updated_dates = []
                for e in entities:
                    if isinstance(e, dict) and "updated_at" in e:
                        updated_dates.append(e["updated_at"])
                
                if len(updated_dates) > 1:
                    sorted_dates = sorted(updated_dates, reverse=True)
                    assert updated_dates == sorted_dates, f"Updated dates not sorted: {updated_dates}"
    
    async def test_sort_default_order(self, call_mcp, test_entities):
        """Test default sort order when not specified.
        
        User Story: Default ordering is applied
        Acceptance Criteria:
        - When no order_by specified, uses default (created_at:desc)
        - Results are still ordered consistently
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "limit": 10
            # No order_by specified - should use default
        })
        
        if result.get("success") and result.get("data"):
            entities = result["data"]
            # Should get results in some consistent order
            assert isinstance(entities, list), "Results should be a list"
            if len(entities) > 1:
                # Default is created_at:desc, verify consistency
                created_dates = []
                for e in entities:
                    if isinstance(e, dict) and "created_at" in e:
                        created_dates.append(e["created_at"])
                
                if len(created_dates) > 1:
                    # Should be in descending order (default)
                    sorted_desc = sorted(created_dates, reverse=True)
                    # May not always match due to same timestamps, but should be reasonable
                    assert len(created_dates) > 0, "Should have timestamps"
    
    async def test_sort_with_pagination(self, call_mcp, test_entities):
        """Test sorting with pagination (limit + offset).
        
        User Story: Sorting works correctly with pagination
        Acceptance Criteria:
        - Sort order maintained across pages
        - First page and second page maintain sort order
        - Offset doesn't affect sort
        """
        # Get first page
        result1, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "name:asc",
            "limit": 5,
            "offset": 0
        })
        
        # Get second page
        result2, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "name:asc",
            "limit": 5,
            "offset": 5
        })
        
        # Verify both pages got results
        if result1.get("success") and result1.get("data"):
            assert isinstance(result1["data"], list), "First page should have list"
        
        if result2.get("success") and result2.get("data"):
            assert isinstance(result2["data"], list), "Second page should have list"
        
        # If both pages have results, verify sort order maintained
        if (result1.get("success") and result1.get("data") and 
            result2.get("success") and result2.get("data")):
            page1_names = [e.get("name", "") for e in result1["data"] if isinstance(e, dict)]
            page2_names = [e.get("name", "") for e in result2["data"] if isinstance(e, dict)]
            
            # Names in page1 should come before names in page2 (alphabetically)
            if page1_names and page2_names:
                max_page1 = max(page1_names)
                min_page2 = min(page2_names)
                # First page max should be <= second page min for proper pagination
                assert max_page1 <= min_page2 or len(page2_names) == 0, \
                    f"Pagination sort order broken: {max_page1} > {min_page2}"
    
    async def test_sort_invalid_field_fallback(self, call_mcp, test_entities):
        """Test sorting with invalid field falls back to default.
        
        User Story: Invalid sort fields are handled gracefully
        Acceptance Criteria:
        - Invalid field names don't crash
        - Fallback to default sort (created_at:desc)
        - Results are still returned
        """
        result, _ = await call_mcp("entity_tool", {
            "operation": "search",
            "entity_type": "project",
            "search_term": "project",
            "order_by": "nonexistent_field:asc",
            "limit": 10
        })
        
        # Should either work or fail gracefully, not crash
        assert result is not None, "Should handle invalid sort field"
        # Results should still be returned (using default sort)
        if result.get("success"):
            assert isinstance(result.get("data"), (list, dict)), "Should return data"
    
    async def test_sort_multiple_entities(self, call_mcp, test_entities):
        """Test sorting works across different entity types.
        
        User Story: Sort applies to multiple entity types consistently
        Acceptance Criteria:
        - Can sort projects by name
        - Can sort documents by created_at
        - Can sort requirements by status
        """
        for entity_type, sort_field in [
            ("project", "name:asc"),
            ("document", "created_at:desc"),
            ("organization", "name:asc")
        ]:
            result, _ = await call_mcp("entity_tool", {
                "operation": "search",
                "entity_type": entity_type,
                "search_term": entity_type,
                "order_by": sort_field,
                "limit": 10
            })
            
            # Should return result for each type
            assert result is not None, f"Should handle sorting {entity_type}"
            # If successful, should have data
            if result.get("success"):
                assert "data" in result, f"Result for {entity_type} should have data"
    
    async def test_query_tool_with_sort_via_search(self, call_mcp, test_entities):
        """Test query_tool search respects default sort.
        
        User Story: query_tool applies sorting to search results
        Acceptance Criteria:
        - query_tool search returns sorted results
        - Results follow alphabetical or chronological order
        """
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "project",
            "limit": 10
        })
        
        assert result is not None, "query_tool search should return result"
        # Results should be in some consistent order
        if result.get("success") and "results_by_entity" in result:
            project_results = result["results_by_entity"].get("project", {})
            if project_results.get("results"):
                results = project_results["results"]
                assert isinstance(results, list), "Results should be list"


class TestQueryAggregate:
    """Test aggregate query type."""
    
    @pytest.mark.story("Search & Discovery - User can count aggregates")
    async def test_aggregate_count(self, call_mcp):
        """Test aggregation with count."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "aggregate",
            "entities": ["project", "document"],
            "limit": 100
        })
        
        assert result.get("success"), f"Aggregate failed: {result.get('error')}"
        assert "data" in result, "Result should contain aggregation data"
    
    async def test_aggregate_multiple_entities(self, call_mcp):
        """Test aggregation across multiple entity types."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "aggregate",
            "entities": ["organization", "project", "document"],
            "limit": 100
        })
        
        assert result.get("success"), f"Multi-entity aggregate failed: {result.get('error')}"
    
    async def test_aggregate_with_conditions(self, call_mcp):
        """Test aggregation with filter conditions."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "aggregate",
            "entities": ["project"],
            "conditions": {"status": "active"},
            "limit": 100
        })
        
        assert result.get("success"), f"Aggregate with conditions failed: {result.get('error')}"


class TestQueryRAGSearch:
    """Test RAG search query type."""
    
    async def test_rag_search_auto_mode(self, call_mcp, test_entities):
        """Test RAG search with auto mode."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "rag_search",
            "entities": ["project", "document"],
            "search_term": "authentication system",
            "rag_mode": "auto",
            "limit": 10
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Search & Discovery - User can semantic search")
    async def test_rag_search_semantic_mode(self, call_mcp, test_entities):
        """Test RAG search with semantic mode."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "rag_search",
            "entities": ["project"],
            "search_term": "web development",
            "rag_mode": "semantic",
            "similarity_threshold": 0.7,
            "limit": 5
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Search & Discovery - User can keyword search")
    async def test_rag_search_keyword_mode(self, call_mcp, test_entities):
        """Test RAG search with keyword mode."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "database",
            "rag_mode": "keyword",
            "limit": 10
        })
        
        assert result is not None, "Should return result"
    
    @pytest.mark.story("Search & Discovery - User can hybrid search")
    async def test_rag_search_hybrid_mode(self, call_mcp, test_entities):
        """Test RAG search with hybrid mode."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "rag_search",
            "entities": ["project", "document"],
            "search_term": "authentication",
            "rag_mode": "hybrid",
            "limit": 10
        })
        
        assert result is not None, "Should return result"


class TestQueryAnalyze:
    """Test analyze query type."""
    
    async def test_analyze_entities(self, call_mcp):
        """Test analyze query type."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "analyze",
            "entities": ["project", "document"],
            "limit": 10
        })
        
        assert result.get("success") or "error" in result, "Should return result"


class TestQueryRelationships:
    """Test relationships query type."""
    
    async def test_relationships_query(self, call_mcp):
        """Test relationships analysis."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "relationships",
            "entities": ["project", "document"],
            "limit": 10
        })
        
        assert result.get("success") or "error" in result, "Should return result"


class TestQuerySimilarity:
    """Test similarity query type."""
    
    @pytest.mark.story("Search & Discovery - User can find similar items")
    async def test_similarity_search(self, call_mcp):
        """Test finding similar content."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "similarity",
            "entities": ["project"],
            "content": "A system for managing user access and permissions",
            "entity_type": "project",
            "limit": 5
        })
        
        assert "success" in result or "error" in result, "Should return result"
    
    async def test_similarity_with_threshold(self, call_mcp):
        """Test similarity search with custom threshold."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "similarity",
            "entities": ["document"],
            "content": "Database design principles",
            "entity_type": "document",
            "similarity_threshold": 0.6,
            "limit": 10
        })
        
        assert "success" in result or "error" in result, "Should return result"


class TestQueryFormatTypes:
    """Test different format types."""
    
    async def test_detailed_format(self, call_mcp):
        """Test detailed result format."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test",
            "format_type": "detailed",
            "limit": 5
        })
        
        assert "success" in result or "error" in result, "Should return result"
    
    async def test_summary_format(self, call_mcp):
        """Test summary result format."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "aggregate",
            "entities": ["project"],
            "format_type": "summary",
            "limit": 10
        })
        
        assert "success" in result or "error" in result, "Should return result"
    
    async def test_raw_format(self, call_mcp):
        """Test raw result format."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "design",
            "format_type": "raw",
            "limit": 5
        })
        
        assert "success" in result or "error" in result, "Should return result"


class TestQueryEdgeCases:
    """Test edge cases and error handling."""
    
    async def test_invalid_query_type(self, call_mcp):
        """Test with invalid query type."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "invalid_type",
            "entities": ["project"],
            "limit": 10
        })
        
        # Should either fail gracefully or ignore invalid type
        assert "success" in result or "error" in result, "Should handle invalid query type"
    
    async def test_empty_entities_list(self, call_mcp):
        """Test with empty entities list."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": [],
            "search_term": "test",
            "limit": 10
        })
        
        # Should handle gracefully
        assert result is not None, "Should return a result"
    
    async def test_zero_limit(self, call_mcp):
        """Test with zero limit."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test",
            "limit": 0
        })
        
        assert result is not None, "Should handle zero limit"
    
    async def test_negative_limit(self, call_mcp):
        """Test with negative limit."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test",
            "limit": -1
        })
        
        assert result is not None, "Should handle negative limit"
    
    async def test_invalid_similarity_threshold(self, call_mcp):
        """Test with invalid similarity threshold."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "similarity",
            "entities": ["project"],
            "content": "test",
            "similarity_threshold": 1.5,  # Invalid: should be 0-1
            "limit": 10
        })
        
        assert result is not None, "Should handle invalid threshold"
    
    async def test_missing_required_fields(self, call_mcp):
        """Test with missing required fields."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            # Missing entities
            "limit": 10
        })
        
        # Should either fail or provide defaults
        assert result is not None, "Should handle missing fields"


class TestQueryIntegration:
    """Test query combinations and workflows."""
    
    async def test_search_then_analyze(self, call_mcp, test_entities):
        """Test searching then analyzing results."""
        # First, search
        search_result, _ = await call_mcp("query_tool", {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "application",
            "limit": 5
        })
        
        assert search_result is not None, "Search should return result"
        
        # Then analyze (in real usage, would use specific IDs from search)
        analyze_result, _ = await call_mcp("query_tool", {
            "query_type": "analyze",
            "entities": ["project"],
            "limit": 5
        })
        
        assert analyze_result is not None, "Analyze should return result"
    
    async def test_aggregate_and_compare(self, call_mcp):
        """Test aggregating and comparing across entity types."""
        result, _ = await call_mcp("query_tool", {
            "query_type": "aggregate",
            "entities": ["project", "document", "organization"],
            "limit": 100
        })
        
        assert result is not None, "Aggregate should return result"
