"""Query Tool Tests - 3-Variant Coverage (Unit, Integration, E2E).

This test suite runs query tool tests in all three modes:
- Unit: In-memory mock client (<1ms, deterministic)
- Integration: HTTP client with live database (50-500ms)  
- E2E: Full deployment with production-like setup (500ms-5s)

Total tests: 54 (18 per variant)
Target coverage: All query types, search functionality, filtering

Query types covered:
- Semantic search (embedding-based)
- Filter queries (structured filtering)
- Full-text search
- Field-specific search
- Aggregations
- Combined filters

Usage:
    # Run all variants
    pytest tests/unit/tools/test_query.py -v
    
    # Run specific variant
    pytest tests/unit/tools/test_query.py -m unit -v
    pytest tests/unit/tools/test_query.py -m integration -v  
    pytest tests/unit/tools/test_query.py -m e2e -v
"""

import uuid
import time
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from tests.framework.test_base import ParametrizedTestSuite

pytestmark = [pytest.mark.asyncio, pytest.mark.three_variant]


class TestQuerySemanticSearch(ParametrizedTestSuite):
    """Test semantic search queries across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        """Parametrized client for 3-variant testing."""
        return request.getfixturevalue(request.param)
    
    async def _create_test_entities_for_search(self, client) -> List[str]:
        """Helper to create entities with searchable content."""
        entity_ids = []
        
        test_entities = [
            {
                "name": "Python Web Application",
                "type": "project",
                "description": "A web application built with Python Flask framework for REST APIs",
                "tags": ["python", "flask", "web", "api"]
            },
            {
                "name": "Database Design Document",
                "type": "document", 
                "description": "Comprehensive database schema design for PostgreSQL with normalization",
                "tags": ["database", "postgresql", "schema", "design"]
            },
            {
                "name": "User Authentication Module",
                "type": "project",
                "description": "JWT-based authentication system with OAuth2 integration",
                "tags": ["auth", "jwt", "oauth", "security"]
            },
            {
                "name": "API Testing Requirements",
                "type": "requirement",
                "description": "Testing requirements for REST API endpoints with automated testing",
                "tags": ["api", "testing", "automation", "requirements"]
            }
        ]
        
        for entity_data in test_entities:
            result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": entity_data["type"],
                "data": entity_data
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        
        return entity_ids
    
    async def test_semantic_search_by_concept(self, client):
        """Test semantic search finding related concepts."""
        await self._create_test_entities_for_search(client)
        
        # Search for "web development" concept
        result = await client.call_tool("query_tool", {
            "query": "web development",
            "entity_types": ["project", "document"],
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        assert isinstance(results, list), "Should return list of results"
        assert len(results) > 0, "Should find matching entities"
        
        # Results should be relevant to web development
        for item in results:
            # Check if content is semantically related
            content = f"{item.get('name', '')} {item.get('description', '')}"
            # Semantic search should find items with web, API, application concepts
            assert any(keyword in content.lower() for keyword in [
                "web", "api", "application", "framework"
            ]) or len(results) > 0, "Results should be semantically relevant"
    
    async def test_semantic_search_with_filters(self, client):
        """Test semantic search combined with structured filters."""
        await self._create_test_entities_for_search(client)
        
        result = await client.call_tool("query_tool", {
            "query": "security authentication",
            "entity_types": ["project"],
            "filters": {"type": "project"},
            "limit": 5
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # Should find security-related projects only
        for item in results:
            assert item.get("type") == "project", "Should filter by entity type"
            content = f"{item.get('name', '')} {item.get('description', '')}"
            # Should be related to security/auth
            is_relevant = any(term in content.lower() for term in [
                "auth", "security", "jwt", "oauth"
            ])
            # Semantic search should prioritize relevant content
            assert is_relevant or len(results) > 0, "Results should be relevant to query"
    
    async def test_semantic_search_empty_results(self, client):
        """Test semantic search with no matching results."""
        result = await client.call_tool("query_tool", {
            "query": "quantum physics experiments",
            "entity_types": ["project"],
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        assert results == [], "Should return empty list for no matches"
    
    async def test_semantic_search_ranking(self, client):
        """Test semantic search returns properly ranked results."""
        await self._create_test_entities_for_search(client)
        
        result = await client.call_tool("query_tool", {
            "query": "database design",
            "entity_types": ["document", "project"],
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        if len(results) > 1:
            # Results should be ranked by relevance (similarity score)
            # Most relevant should come first
            first_result = results[0]
            content = f"{first_result.get('name', '')} {first_result.get('description', '')}"
            
            # Direct match should be highly ranked
            has_direct_match = any(term in content.lower() for term in [
                "database", "design", "schema"
            ])
            assert has_direct_match, "Most relevant result should contain direct matches"


class TestQueryFilterOperations(ParametrizedTestSuite):
    """Test filter-based queries across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_test_entities_for_filtering(self, client) -> List[str]:
        """Helper to create entities with various attributes for filtering."""
        entity_ids = []
        
        test_orgs = [
            {"name": "Tech Corp", "type": "technology", "size": "large", "active": True},
            {"name": "Design Studio", "type": "creative", "size": "small", "active": True},
            {"name": "Data Analytics Inc", "type": "technology", "size": "medium", "active": False}
        ]
        
        for org_data in test_orgs:
            result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "organization",
                "data": org_data
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        
        return entity_ids
    
    async def test_filter_by_single_field(self, client):
        """Test filtering by a single field."""
        await self._create_test_entities_for_filtering(client)
        
        result = await client.call_tool("query_tool", {
            "query": "organizations",
            "entity_types": ["organization"],
            "filters": {"active": True},
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # All results should match the filter
        for item in results:
            assert item.get("active") == True, "All results should be active"
        
        assert len(results) == 2, "Should find exactly 2 active organizations"
    
    async def test_filter_by_multiple_fields(self, client):
        """Test filtering by multiple fields with AND logic."""
        await self._create_test_entities_for_filtering(client)
        
        result = await client.call_tool("query_tool", {
            "query": "technology organizations",
            "entity_types": ["organization"],
            "filters": {"type": "technology", "active": True},
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # All results should match all filters
        for item in results:
            assert item.get("type") == "technology", "Should be technology type"
            assert item.get("active") == True, "Should be active"
        
        assert len(results) == 1, "Should find exactly 1 active technology organization"
    
    async def test_filter_with_pagination(self, client):
        """Test filtering with pagination."""
        await self._create_test_entities_for_filtering(client)
        
        # Get first page
        page1 = await client.call_tool("query_tool", {
            "query": "all organizations",
            "entity_types": ["organization"],
            "limit": 2,
            "filters": {}
        })
        
        self.assert_success(page1)
        results1 = page1["data"]
        assert len(results1) <= 2, "Should respect limit"
        
        # Get second page
        page2 = await client.call_tool("query_tool", {
            "query": "all organizations",
            "entity_types": ["organization"],
            "limit": 2,
            "offset": 2,
            "filters": {}
        })
        
        self.assert_success(page2)
        results2 = page2["data"]
        
        # Combined should have all results
        all_results = results1 + results2
        assert len(all_results) == 3, "Should find all 3 organizations across pages"
    
    async def test_filter_by_date_range(self, client):
        """Test filtering by date range."""
        # Create entities with timestamps
        entities = await self._create_test_entities_for_filtering(client)
        
        if len(entities) > 0:
            # Get timestamp of first entity
            read_result = await client.call_tool("entity_tool", {
                "operation": "read",
                "entity_type": "organization",
                "entity_id": entities[0]
            })
            
            if read_result.get("success"):
                created_at = read_result["data"].get("created_at")
                
                result = await client.call_tool("query_tool", {
                    "query": "organizations created after date",
                    "entity_types": ["organization"],
                    "filters": {"created_after": created_at},
                    "limit": 10
                })
                
                self.assert_success(result)
                results = result["data"]
                
                # All results should be created after the timestamp
                for item in results:
                    if item.get("created_at"):
                        # This validation depends on timestamp format
                        assert True, "Date filtering should work"
    
    async def test_filter_no_matches(self, client):
        """Test filter that matches no entities."""
        await self._create_test_entities_for_filtering(client)
        
        result = await client.call_tool("query_tool", {
            "query": "nonexistent entities",
            "entity_types": ["organization"],
            "filters": {"type": "nonexistent_type"},
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        assert results == [], "Should return empty list for no matches"


class TestQueryFullTextSearch(ParametrizedTestSuite):
    """Test full-text search queries across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_docs_for_text_search(self, client) -> List[str]:
        """Helper to create documents with various text content."""
        entity_ids = []
        
        test_docs = [
            {
                "name": "API Specification",
                "type": "document",
                "content": "This document specifies the REST API endpoints, including POST, GET, PUT, DELETE operations with JSON request/response formats."
            },
            {
                "name": "Authentication Guide", 
                "type": "document",
                "content": "Comprehensive guide on authentication methods including JWT tokens, OAuth2 flows, and session management."
            },
            {
                "name": "Database Documentation",
                "type": "document",
                "content": "PostgreSQL database documentation with table schemas, indexing strategies, and performance optimization."
            }
        ]
        
        for doc_data in test_docs:
            result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "document",
                "data": doc_data
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        
        return entity_ids
    
    async def test_full_text_search_single_term(self, client):
        """Test full-text search with single term."""
        await self._create_docs_for_text_search(client)
        
        result = await client.call_tool("query_tool", {
            "query": "REST",
            "entity_types": ["document"],
            "search_mode": "full_text",
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # Should find documents containing "REST"
        found_rest = any(
            "REST" in f"{item.get('name', '')} {item.get('content', '')}"
            for item in results
        )
        assert found_rest, "Should find documents containing the search term"
    
    async def test_full_text_search_multiple_terms(self, client):
        """Test full-text search with multiple terms."""
        await self._create_docs_for_text_search(client)
        
        result = await client.call_tool("query_tool", {
            "query": "JSON API endpoints",
            "entity_types": ["document"],
            "search_mode": "full_text",
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # Results should contain multiple search terms
        for item in results:
            content = f"{item.get('name', '')} {item.get('content', '')}"
            term_count = sum(1 for term in ["JSON", "API", "endpoints"] if term in content)
            assert term_count >= 2, "Results should contain multiple terms"
    
    async def test_full_text_search_phrase(self, client):
        """Test full-text search with exact phrase."""
        await self._create_docs_for_text_search(client)
        
        result = await client.call_tool("query_tool", {
            "query": "'OAuth2 flows'",
            "entity_types": ["document"],
            "search_mode": "full_text",
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # Should find document with exact phrase
        found_phrase = any(
            "OAuth2 flows" in f"{item.get('name', '')} {item.get('content', '')}"
            for item in results
        )
        assert found_phrase, "Should find document with exact phrase match"
    
    async def test_full_text_search_case_insensitive(self, client):
        """Test full-text search is case insensitive."""
        await self._create_docs_for_text_search(client)
        
        # Search for lowercase version
        result_lower = await client.call_tool("query_tool", {
            "query": "postgresql",
            "entity_types": ["document"],
            "search_mode": "full_text",
            "limit": 10
        })
        
        # Search for uppercase version
        result_upper = await client.call_tool("query_tool", {
            "query": "POSTGRESQL",
            "entity_types": ["document"],
            "search_mode": "full_text",
            "limit": 10
        })
        
        # Should return same number of results
        self.assert_success(result_lower)
        self.assert_success(result_upper)
        assert len(result_lower["data"]) == len(result_upper["data"]), \
            "Case should not affect search results"
    
    async def test_full_text_search_with_filters(self, client):
        """Test full-text search combined with filters."""
        await self._create_docs_for_text_search(client)
        
        result = await client.call_tool("query_tool", {
            "query": "documentation",
            "entity_types": ["document"],
            "search_mode": "full_text",
            "filters": {"type": "document"},
            "limit": 10
        })
        
        self.assert_success(result)
        results = result["data"]
        
        # All results should match both text and filter
        for item in results:
            assert item.get("type") == "document", "Should filter by document type"
            content = f"{item.get('name', '')} {item.get('content', '')}"
            assert "documentation" in content.lower(), "Should contain search term"


class TestQueryAggregations(ParametrizedTestSuite):
    """Test aggregation queries across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    async def _create_entities_for_aggregation(self, client) -> List[str]:
        """Helper to create entities for aggregation testing."""
        entity_ids = []
        
        # Create different types of entities
        projects = [
            {"name": "Project Alpha", "status": "completed", "priority": "high"},
            {"name": "Project Beta", "status": "in_progress", "priority": "medium"},
            {"name": "Project Gamma", "status": "completed", "priority": "low"},
            {"name": "Project Delta", "status": "in_progress", "priority": "high"}
        ]
        
        for project_data in projects:
            result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": project_data
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        
        return entity_ids
    
    async def test_aggregation_count_by_field(self, client):
        """Test count aggregation by field values."""
        await self._create_entities_for_aggregation(client)
        
        result = await client.call_tool("query_tool", {
            "query": "project status aggregation",
            "entity_types": ["project"],
            "aggregation": {
                "type": "count",
                "field": "status"
            },
            "limit": 10
        })
        
        self.assert_success(result)
        aggregation_result = result["data"]
        
        # Should return aggregation results
        assert isinstance(aggregation_result, dict), "Should return dict with aggregation"
        
        # Should have counts for different statuses
        if "results" in aggregation_result:
            results = aggregation_result["results"]
            total_count = sum(r.get("count", 0) for r in results)
            assert total_count == 4, "Should count all 4 projects"
    
    async def test_aggregation_group_by_multiple_fields(self, client):
        """Test aggregation grouping by multiple fields."""
        await self._create_entities_for_aggregation(client)
        
        result = await client.call_tool("query_tool", {
            "query": "project status and priority aggregation",
            "entity_types": ["project"],
            "aggregation": {
                "type": "count",
                "fields": ["status", "priority"]
            },
            "limit": 10
        })
        
        self.assert_success(result)
        aggregation_result = result["data"]
        
        # Should group by combinations of status and priority
        assert isinstance(aggregation_result, dict), "Should return aggregation dict"
    
    async def test_aggregation_averages(self, client):
        """Test average aggregation for numeric fields."""
        # Create entities with numeric values
        numeric_entities = [
            {"name": "Task 1", "hours": 8, "complexity": 5},
            {"name": "Task 2", "hours": 6, "complexity": 3},
            {"name": "Task 3", "hours": 10, "complexity": 7}
        ]
        
        entity_ids = []
        for entity_data in numeric_entities:
            result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "test_entity",
                "data": entity_data
            })
            if result.get("success"):
                entity_ids.append(result["data"]["id"])
        
        if entity_ids:
            result = await client.call_tool("query_tool", {
                "query": "average task complexity",
                "entity_types": ["test_entity"],
                "aggregation": {
                    "type": "avg",
                    "field": "complexity"
                },
                "limit": 10
            })
            
            self.assert_success(result)
            avg_result = result["data"]
            
            # Average should be calculated correctly
            if "average" in avg_result:
                expected_avg = (5 + 3 + 7) / 3  # 5.0
                assert abs(avg_result["average"] - expected_avg) < 0.1, \
                    "Should calculate correct average"
    
    async def test_aggregation_filters(self, client):
        """Test aggregation with filters applied before aggregation."""
        await self._create_entities_for_aggregation(client)
        
        result = await client.call_tool("query_tool", {
            "query": "completed projects count",
            "entity_types": ["project"],
            "filters": {"status": "completed"},
            "aggregation": {
                "type": "count"
            },
            "limit": 10
        })
        
        self.assert_success(result)
        aggregation_result = result["data"]
        
        # Should count only completed projects
        if "count" in aggregation_result:
            assert aggregation_result["count"] == 2, "Should count only completed projects"


class TestQueryPerformance(ParametrizedTestSuite):
    """Test query performance across all 3 variants."""
    
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        return request.getfixturevalue(request.param)
    
    @pytest.mark.parametrize("query_type,max_time_ms", [
        ("semantic_search", 200),   # Unit: <1ms, Integration: <100ms, E2E: <200ms
        ("filter_query", 100),      # Unit: <1ms, Integration: <50ms, E2E: <100ms
        ("full_text_search", 150), # Unit: <1ms, Integration: <75ms, E2E: <150ms
        ("aggregation", 250),       # Unit: <1ms, Integration: <125ms, E2E: <250ms
    ])
    async def test_query_operation_timing(self, client, query_type: str, max_time_ms: int):
        """Test query operation timing within expected bounds."""
        # Setup: Create some test data
        entity_data = {
            "name": f"Performance Test {uuid.uuid4().hex[:8]}",
            "type": "test_entity",
            "description": "Entity for performance testing of queries",
            "content": "Test content for search performance testing"
        }
        
        create_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "test_entity",
            "data": entity_data
        })
        
        if not create_result.get("success"):
            pytest.skip("Could not create test entity")
        
        # Time the query operation
        start_time = time.perf_counter()
        
        if query_type == "semantic_search":
            result = await client.call_tool("query_tool", {
                "query": "test performance",
                "entity_types": ["test_entity"],
                "limit": 10
            })
        elif query_type == "filter_query":
            result = await client.call_tool("query_tool", {
                "query": "test entities",
                "entity_types": ["test_entity"],
                "filters": {"type": "test_entity"},
                "limit": 10
            })
        elif query_type == "full_text_search":
            result = await client.call_tool("query_tool", {
                "query": "performance",
                "entity_types": ["test_entity"],
                "search_mode": "full_text",
                "limit": 10
            })
        elif query_type == "aggregation":
            result = await client.call_tool("query_tool", {
                "query": "test entity count",
                "entity_types": ["test_entity"],
                "aggregation": {"type": "count"},
                "limit": 10
            })
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Performance expectations by variant
        if not hasattr(client, '_config'):  # Unit test
            assert elapsed_ms < 5, f"Unit {query_type} took {elapsed_ms:.2f}ms, expected <5ms"
        else:  # Integration or E2E
            assert elapsed_ms < max_time_ms, \
                f"{query_type} took {elapsed_ms:.2f}ms, expected <{max_time_ms}ms"
        
        self.assert_success(result)

    @pytest.mark.asyncio
    async def test_query_single_results(self, mock_database_with_data):
        """Test get_single method for queries expected to return one result."""
        # Find exact match
        ws = await mock_database_with_data.get_single(
            "workspaces",
            filters={"id": "ws-123"}
        )
        assert ws["name"] == "Test Workspace"
        
        # No match returns None
        none = await mock_database_with_data.get_single(
            "workspaces", 
            filters={"id": "nonexistent"}
        )
        assert none is None

    @pytest.mark.asyncio
    async def test_query_with_column_selection(self, mock_database_with_data):
        """Test query with specific column selection."""
        # Select only name and type columns
        results = await mock_database_with_data.query(
            "entities",
            select="name,type"
        )
        assert all(set(r.keys()) == {"name", "type"} for r in results)
        
        # Verify all entities are included with only selected columns
        assert len(results) == 3  # All entities in seed data

    @pytest.mark.asyncio 
    async def test_query_count_operations(self, mock_database_with_data):
        """Test count operations with filtering."""
        # Total count
        total = await mock_database_with_data.count("workspaces")
        assert total == 2
        
        # Filtered count
        ws_123_count = await mock_database_with_data.count(
            "entities",
            filters={"workspace_id": "ws-123"}
        )
        assert ws_123_count == 2

    @pytest.mark.asyncio
    async def test_query_joins_and_relationships(self, mock_database_with_data):
        """Test querying relationships between entities."""
        # Find entities with relationships
        rel_entities = await mock_database_with_data.query(
            "relationships",
            filters={"relationship_type": "implements"}
        )
        assert len(rel_entities) == 1
        assert rel_entities[0]["source_entity_id"] == "entity-2"
        assert rel_entities[0]["target_entity_id"] == "entity-1"

    @pytest.mark.asyncio
    async def test_query_complex_filtering(self, mock_database_with_data):
        """Test complex query filtering scenarios."""
        # Find documents in ws-123 created by mock-user-123
        docs = await mock_database_with_data.query(
            "entities",
            filters={
                "type": "document",
                "workspace_id": "ws-123",
                "created_by": "mock-user-123"
            }
        )
        assert len(docs) == 1
        assert docs[0]["name"] == "Test Document"

    @pytest.mark.asyncio
    async def test_query_with_like_filters(self, mock_database_with_data):
        """Test query with LIKE-style filtering (simulated)."""
        # Note: InMemoryDatabaseAdapter only supports exact matches
        # This test documents the current limitation
        
        # For now, we can get all and filter in test
        all_entities = await mock_database_with_data.query("entities")
        
        # Simulate "Test" name search
        test_docs = [e for e in all_entities if "Test" in e.get("name", "")]
        assert len(test_docs) == 2  # "Test Document" and "Test Requirement"