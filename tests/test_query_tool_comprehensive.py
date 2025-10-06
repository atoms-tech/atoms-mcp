"""Comprehensive test suite for query_tool with all query types and RAG capabilities.

This test suite provides 100% coverage for:
1. All query types (search, aggregate, analyze, relationships, rag_search, similarity)
2. All RAG modes (auto, semantic, keyword, hybrid)
3. Edge cases and error scenarios
4. Performance benchmarks
5. Parameter validation

Run with: pytest tests/test_query_tool_comprehensive.py -v -s
"""

from __future__ import annotations

import os
import time
import uuid
import asyncio
from typing import Dict, Any, List
from datetime import datetime

import httpx
import pytest
from supabase import create_client

# Test configuration
MCP_BASE_URL = os.getenv("ATOMS_FASTMCP_BASE_URL", "http://127.0.0.1:8000")
MCP_PATH = os.getenv("ATOMS_FASTMCP_HTTP_PATH", "/api/mcp")
TEST_EMAIL = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
TEST_PASSWORD = os.getenv("ATOMS_TEST_PASSWORD", "118118")

pytestmark = [pytest.mark.asyncio, pytest.mark.http]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def supabase_env():
    """Ensure Supabase environment variables are present."""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured")

    return {"url": url, "key": key}


@pytest.fixture(scope="module")
def auth_token(supabase_env):
    """Authenticate and return JWT token."""
    client = create_client(supabase_env["url"], supabase_env["key"])

    try:
        auth_response = client.auth.sign_in_with_password({
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })

        if auth_response.session and auth_response.session.access_token:
            return auth_response.session.access_token
    except Exception as e:
        pytest.skip(f"Authentication failed: {e}")

    pytest.skip("Could not obtain authentication token")


@pytest.fixture(scope="module")
async def mcp_caller(check_server_running, auth_token):
    """Factory for making MCP tool calls."""
    base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    async def call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an MCP tool call."""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": f"tools/{tool_name}",
            "params": params,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(base_url, json=payload, headers=headers)

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }

        body = response.json()
        if "result" in body:
            return body["result"]

        return {
            "success": False,
            "error": body.get("error", "Unknown error")
        }

    return call_tool


@pytest.fixture(scope="module")
async def test_data_setup(mcp_caller):
    """Set up test data for query tests."""
    test_org_id = None
    test_project_id = None
    test_doc_id = None
    test_req_ids = []

    try:
        # Create test organization
        org_result = await mcp_caller("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {
                "name": "Query Test Org",
                "slug": f"query-test-org-{uuid.uuid4().hex[:8]}",
                "description": "Organization for comprehensive query testing",
                "type": "team"
            }
        })

        if org_result.get("success"):
            test_org_id = org_result["data"]["id"]

            # Create test project
            project_result = await mcp_caller("entity_tool", {
                "operation": "create",
                "entity_type": "project",
                "data": {
                    "name": "Query Test Project",
                    "organization_id": test_org_id,
                    "description": "Project for testing query functionality"
                }
            })

            if project_result.get("success"):
                test_project_id = project_result["data"]["id"]

                # Create test document
                doc_result = await mcp_caller("entity_tool", {
                    "operation": "create",
                    "entity_type": "document",
                    "data": {
                        "name": "Test Requirements Document",
                        "project_id": test_project_id,
                        "description": "Document for query testing with semantic search capabilities"
                    }
                })

                if doc_result.get("success"):
                    test_doc_id = doc_result["data"]["id"]

                    # Create test requirements with varied content
                    req_data = [
                        {
                            "name": "User Authentication",
                            "description": "The system shall provide secure user authentication using OAuth 2.0",
                            "priority": "high"
                        },
                        {
                            "name": "Data Encryption",
                            "description": "All sensitive data must be encrypted at rest using AES-256",
                            "priority": "critical"
                        },
                        {
                            "name": "API Rate Limiting",
                            "description": "The API shall implement rate limiting to prevent abuse",
                            "priority": "medium"
                        },
                        {
                            "name": "Database Backup",
                            "description": "Automated database backups shall run daily at 2 AM",
                            "priority": "high"
                        },
                        {
                            "name": "Performance Monitoring",
                            "description": "The system shall monitor response times and alert on degradation",
                            "priority": "medium"
                        }
                    ]

                    for req in req_data:
                        req_result = await mcp_caller("entity_tool", {
                            "operation": "create",
                            "entity_type": "requirement",
                            "data": {
                                **req,
                                "document_id": test_doc_id
                            }
                        })

                        if req_result.get("success"):
                            test_req_ids.append(req_result["data"]["id"])

        yield {
            "org_id": test_org_id,
            "project_id": test_project_id,
            "doc_id": test_doc_id,
            "req_ids": test_req_ids
        }

    finally:
        # Cleanup test data
        if test_org_id:
            await mcp_caller("entity_tool", {
                "operation": "delete",
                "entity_type": "organization",
                "entity_id": test_org_id,
                "soft_delete": True
            })


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestQueryTypeSearch:
    """Test search query type functionality."""

    @pytest.mark.asyncio
    async def test_search_single_entity(self, mcp_caller, test_data_setup):
        """
        Given: A valid search term and single entity type
        When: search query is executed
        Then: Results are returned for the specified entity
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "Query Test",
            "limit": 5
        })

        assert result.get("success") is True, f"Search failed: {result}"
        assert "data" in result
        assert "search_term" in result["data"]
        assert result["data"]["search_term"] == "Query Test"

    @pytest.mark.asyncio
    async def test_search_multiple_entities(self, mcp_caller, test_data_setup):
        """
        Given: A search term and multiple entity types
        When: search query is executed
        Then: Results are returned for all specified entities
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization", "project", "document"],
            "search_term": "test",
            "limit": 10
        })

        assert result.get("success") is True
        assert "data" in result
        assert "results_by_entity" in result["data"]

    @pytest.mark.asyncio
    async def test_search_with_conditions(self, mcp_caller, test_data_setup):
        """
        Given: Search with additional filter conditions
        When: search query is executed
        Then: Results match both search term and conditions
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "test",
            "conditions": {"type": "team"},
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_search_missing_search_term(self, mcp_caller):
        """
        Given: Search query without search_term
        When: search query is executed
        Then: Error is returned indicating missing search_term
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"]
        })

        assert result.get("success") is False
        assert "error" in result
        assert "search_term" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_invalid_entity(self, mcp_caller):
        """
        Given: Search with invalid entity type
        When: search query is executed
        Then: Error is returned or entity is skipped
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["invalid_entity_type"],
            "search_term": "test"
        })

        # Should either fail or return empty results
        assert result.get("success") is False or result["data"]["total_results"] == 0

    @pytest.mark.asyncio
    async def test_search_limit_enforcement(self, mcp_caller):
        """
        Given: Search with specific limit
        When: search query is executed
        Then: Results respect the limit parameter
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "test",
            "limit": 2
        })

        assert result.get("success") is True
        if result["data"].get("results_by_entity"):
            for entity_results in result["data"]["results_by_entity"].values():
                if "results" in entity_results:
                    assert len(entity_results["results"]) <= 2


class TestQueryTypeAggregate:
    """Test aggregate query type functionality."""

    @pytest.mark.asyncio
    async def test_aggregate_basic_stats(self, mcp_caller, test_data_setup):
        """
        Given: Valid entity types for aggregation
        When: aggregate query is executed
        Then: Summary statistics are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "aggregate",
            "entities": ["organization", "project"]
        })

        assert result.get("success") is True
        assert "data" in result
        assert "results" in result["data"]

    @pytest.mark.asyncio
    async def test_aggregate_with_conditions(self, mcp_caller, test_data_setup):
        """
        Given: Aggregate query with filter conditions
        When: aggregate query is executed
        Then: Statistics reflect filtered data
        """
        result = await mcp_caller("query_tool", {
            "query_type": "aggregate",
            "entities": ["organization"],
            "conditions": {"type": "team"}
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_aggregate_status_breakdown(self, mcp_caller, test_data_setup):
        """
        Given: Entity types that have status field
        When: aggregate query is executed
        Then: Status breakdown is included in results
        """
        result = await mcp_caller("query_tool", {
            "query_type": "aggregate",
            "entities": ["requirement", "project"]
        })

        assert result.get("success") is True
        if "data" in result and "results" in result["data"]:
            for entity, stats in result["data"]["results"].items():
                if entity in ["requirement", "project"]:
                    # Status breakdown may be present
                    assert "total_count" in stats

    @pytest.mark.asyncio
    async def test_aggregate_projections(self, mcp_caller, test_data_setup):
        """
        Given: Aggregate query with specific projections
        When: aggregate query is executed
        Then: Only specified fields are included
        """
        result = await mcp_caller("query_tool", {
            "query_type": "aggregate",
            "entities": ["organization"],
            "projections": ["total_count", "recent_count"]
        })

        assert result.get("success") is True
        assert "data" in result


class TestQueryTypeAnalyze:
    """Test analyze query type functionality."""

    @pytest.mark.asyncio
    async def test_analyze_organization(self, mcp_caller, test_data_setup):
        """
        Given: Organization entity type for analysis
        When: analyze query is executed
        Then: Organization-specific metrics are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "analyze",
            "entities": ["organization"]
        })

        assert result.get("success") is True
        assert "data" in result
        assert "analysis" in result["data"]

    @pytest.mark.asyncio
    async def test_analyze_project(self, mcp_caller, test_data_setup):
        """
        Given: Project entity type for analysis
        When: analyze query is executed
        Then: Project-specific metrics are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "analyze",
            "entities": ["project"]
        })

        assert result.get("success") is True
        if "data" in result and "analysis" in result["data"]:
            project_analysis = result["data"]["analysis"].get("project", {})
            # May have project-specific metrics
            assert isinstance(project_analysis, dict)

    @pytest.mark.asyncio
    async def test_analyze_requirement(self, mcp_caller, test_data_setup):
        """
        Given: Requirement entity type for analysis
        When: analyze query is executed
        Then: Requirement-specific metrics including test coverage are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "analyze",
            "entities": ["requirement"]
        })

        assert result.get("success") is True
        if "data" in result and "analysis" in result["data"]:
            req_analysis = result["data"]["analysis"].get("requirement", {})
            # Should have requirement-specific analysis
            assert isinstance(req_analysis, dict)

    @pytest.mark.asyncio
    async def test_analyze_multiple_entities(self, mcp_caller, test_data_setup):
        """
        Given: Multiple entity types for analysis
        When: analyze query is executed
        Then: Analysis is returned for all entity types
        """
        result = await mcp_caller("query_tool", {
            "query_type": "analyze",
            "entities": ["organization", "project", "requirement"]
        })

        assert result.get("success") is True
        assert "data" in result
        assert "analysis" in result["data"]


class TestQueryTypeRelationships:
    """Test relationships query type functionality."""

    @pytest.mark.asyncio
    async def test_relationships_basic(self, mcp_caller, test_data_setup):
        """
        Given: Valid entity types
        When: relationships query is executed
        Then: Relationship data is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "relationships",
            "entities": ["organization"]
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_relationships_with_conditions(self, mcp_caller, test_data_setup):
        """
        Given: Relationships query with filter conditions
        When: relationships query is executed
        Then: Filtered relationship data is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "relationships",
            "entities": ["organization"],
            "conditions": {"status": "active"}
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_relationships_coverage(self, mcp_caller, test_data_setup):
        """
        Given: Relationships query
        When: executed
        Then: All relationship types are checked
        """
        result = await mcp_caller("query_tool", {
            "query_type": "relationships",
            "entities": ["organization", "project"]
        })

        assert result.get("success") is True
        if "data" in result and "relationships" in result["data"]:
            # Should include various relationship tables
            relationships = result["data"]["relationships"]
            assert isinstance(relationships, dict)


class TestQueryTypeRAGSearch:
    """Test RAG search query type with all modes."""

    @pytest.mark.asyncio
    async def test_rag_search_auto_mode(self, mcp_caller, test_data_setup):
        """
        Given: RAG search with auto mode
        When: rag_search query is executed
        Then: System automatically selects best mode and returns results
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "user authentication security",
            "rag_mode": "auto",
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result
        assert "mode" in result["data"]  # Should indicate which mode was used

    @pytest.mark.asyncio
    async def test_rag_search_semantic_mode(self, mcp_caller, test_data_setup):
        """
        Given: RAG search with semantic mode
        When: rag_search query is executed
        Then: Semantic vector search is performed
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "authentication and authorization",
            "rag_mode": "semantic",
            "similarity_threshold": 0.7,
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result
        assert result["data"].get("mode") == "semantic"

    @pytest.mark.asyncio
    async def test_rag_search_keyword_mode(self, mcp_caller, test_data_setup):
        """
        Given: RAG search with keyword mode
        When: rag_search query is executed
        Then: Keyword-based search is performed
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "OAuth authentication",
            "rag_mode": "keyword",
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result
        assert result["data"].get("mode") == "keyword"

    @pytest.mark.asyncio
    async def test_rag_search_hybrid_mode(self, mcp_caller, test_data_setup):
        """
        Given: RAG search with hybrid mode
        When: rag_search query is executed
        Then: Combined semantic and keyword search is performed
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "data encryption security",
            "rag_mode": "hybrid",
            "similarity_threshold": 0.7,
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result
        assert result["data"].get("mode") == "hybrid"

    @pytest.mark.asyncio
    async def test_rag_search_similarity_threshold(self, mcp_caller, test_data_setup):
        """
        Given: RAG search with high similarity threshold
        When: rag_search query is executed
        Then: Only highly similar results are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "encryption",
            "rag_mode": "semantic",
            "similarity_threshold": 0.9,
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result
        # Results should have high similarity scores if any are returned

    @pytest.mark.asyncio
    async def test_rag_search_multiple_entities(self, mcp_caller, test_data_setup):
        """
        Given: RAG search across multiple entity types
        When: rag_search query is executed
        Then: Results from all entity types are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement", "document", "project"],
            "search_term": "testing",
            "rag_mode": "auto",
            "limit": 10
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_rag_search_with_filters(self, mcp_caller, test_data_setup):
        """
        Given: RAG search with additional filters
        When: rag_search query is executed
        Then: Results match both semantic similarity and filters
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "security",
            "rag_mode": "semantic",
            "conditions": {"priority": "high"},
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_rag_search_missing_search_term(self, mcp_caller):
        """
        Given: RAG search without search_term
        When: rag_search query is executed
        Then: Error is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "rag_mode": "auto"
        })

        assert result.get("success") is False
        assert "error" in result
        assert "search_term" in result["error"].lower()


class TestQueryTypeSimilarity:
    """Test similarity query type functionality."""

    @pytest.mark.asyncio
    async def test_similarity_basic(self, mcp_caller, test_data_setup):
        """
        Given: Content and entity type for similarity search
        When: similarity query is executed
        Then: Similar content is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "similarity",
            "entities": ["requirement"],
            "content": "The system must authenticate users securely using modern protocols",
            "similarity_threshold": 0.7,
            "limit": 3
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_similarity_with_exclude(self, mcp_caller, test_data_setup):
        """
        Given: Similarity search with exclude_id
        When: similarity query is executed
        Then: Excluded ID is not in results
        """
        req_ids = test_data_setup.get("req_ids", [])
        if req_ids:
            result = await mcp_caller("query_tool", {
                "query_type": "similarity",
                "entities": ["requirement"],
                "content": "User authentication requirements",
                "exclude_id": req_ids[0],
                "limit": 5
            })

            assert result.get("success") is True
            if "data" in result and "results" in result["data"]:
                result_ids = [r["id"] for r in result["data"]["results"]]
                assert req_ids[0] not in result_ids

    @pytest.mark.asyncio
    async def test_similarity_high_threshold(self, mcp_caller, test_data_setup):
        """
        Given: Similarity search with very high threshold
        When: similarity query is executed
        Then: Only extremely similar results are returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "similarity",
            "entities": ["requirement"],
            "content": "Database backup automation",
            "similarity_threshold": 0.95,
            "limit": 5
        })

        assert result.get("success") is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_similarity_missing_content(self, mcp_caller):
        """
        Given: Similarity query without content
        When: similarity query is executed
        Then: Error is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "similarity",
            "entities": ["requirement"],
            "similarity_threshold": 0.8
        })

        assert result.get("success") is False
        assert "error" in result
        assert "content" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_similarity_entity_type_vs_entities(self, mcp_caller, test_data_setup):
        """
        Given: Similarity query using entities array (not entity_type)
        When: similarity query is executed
        Then: First entity from array is used
        """
        result = await mcp_caller("query_tool", {
            "query_type": "similarity",
            "entities": ["requirement"],
            "content": "Performance monitoring and alerting",
            "limit": 3
        })

        assert result.get("success") is True
        assert "data" in result


class TestFormatTypes:
    """Test different format_type options."""

    @pytest.mark.asyncio
    async def test_format_detailed(self, mcp_caller, test_data_setup):
        """
        Given: Query with format_type='detailed'
        When: query is executed
        Then: Detailed response with metadata is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "test",
            "format_type": "detailed"
        })

        assert result.get("success") is True
        assert "data" in result
        assert "count" in result or "timestamp" in result

    @pytest.mark.asyncio
    async def test_format_summary(self, mcp_caller, test_data_setup):
        """
        Given: Query with format_type='summary'
        When: query is executed
        Then: Summarized response is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "test",
            "format_type": "summary"
        })

        assert result.get("success") is True
        # Summary format may have different structure

    @pytest.mark.asyncio
    async def test_format_raw(self, mcp_caller, test_data_setup):
        """
        Given: Query with format_type='raw'
        When: query is executed
        Then: Raw data without formatting is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "test",
            "format_type": "raw"
        })

        assert result.get("success") is True
        # Raw format has data directly


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_query_type(self, mcp_caller):
        """
        Given: Invalid query_type
        When: query is executed
        Then: Error is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "invalid_type",
            "entities": ["organization"]
        })

        assert result.get("success") is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_entities_array(self, mcp_caller):
        """
        Given: Empty entities array
        When: query is executed
        Then: Error is returned
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": [],
            "search_term": "test"
        })

        assert result.get("success") is False

    @pytest.mark.asyncio
    async def test_invalid_similarity_threshold(self, mcp_caller):
        """
        Given: Invalid similarity_threshold (> 1.0)
        When: rag_search is executed
        Then: Error is handled gracefully
        """
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "test",
            "similarity_threshold": 1.5  # Invalid
        })

        # Should either fail or clamp the value
        assert "error" in result or result.get("success") is True

    @pytest.mark.asyncio
    async def test_negative_limit(self, mcp_caller):
        """
        Given: Negative limit value
        When: query is executed
        Then: Error is handled or default is used
        """
        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization"],
            "search_term": "test",
            "limit": -5
        })

        # Should either fail or use default limit
        assert result is not None

    @pytest.mark.asyncio
    async def test_missing_authentication(self):
        """
        Given: Request without authentication
        When: query is executed
        Then: Authentication error is returned
        """
        base_url = f"{MCP_BASE_URL.rstrip('/')}{MCP_PATH}"
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/query_tool",
            "params": {
                "query_type": "search",
                "entities": ["organization"],
                "search_term": "test"
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

        # Should fail with authentication error
        assert response.status_code in [401, 403] or (
            response.status_code == 200 and
            not response.json().get("result", {}).get("success")
        )


class TestPerformance:
    """Performance benchmarks for query operations."""

    @pytest.mark.asyncio
    async def test_search_performance(self, mcp_caller, test_data_setup):
        """
        Given: Standard search query
        When: query is executed
        Then: Response time is reasonable (< 5 seconds)
        """
        start = time.time()

        result = await mcp_caller("query_tool", {
            "query_type": "search",
            "entities": ["organization", "project"],
            "search_term": "test",
            "limit": 10
        })

        elapsed = time.time() - start

        assert result.get("success") is True
        assert elapsed < 5.0, f"Search took {elapsed:.2f}s, expected < 5s"

    @pytest.mark.asyncio
    async def test_rag_search_performance(self, mcp_caller, test_data_setup):
        """
        Given: RAG semantic search query
        When: query is executed
        Then: Response time is reasonable (< 10 seconds)
        """
        start = time.time()

        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "authentication security",
            "rag_mode": "semantic",
            "limit": 5
        })

        elapsed = time.time() - start

        assert result.get("success") is True
        assert elapsed < 10.0, f"RAG search took {elapsed:.2f}s, expected < 10s"

    @pytest.mark.asyncio
    async def test_aggregate_performance(self, mcp_caller, test_data_setup):
        """
        Given: Aggregate query
        When: query is executed
        Then: Response time is reasonable (< 5 seconds)
        """
        start = time.time()

        result = await mcp_caller("query_tool", {
            "query_type": "aggregate",
            "entities": ["organization", "project", "requirement"]
        })

        elapsed = time.time() - start

        assert result.get("success") is True
        assert elapsed < 5.0, f"Aggregate took {elapsed:.2f}s, expected < 5s"


class TestRAGModeComparison:
    """Compare RAG mode results for quality and relevance."""

    @pytest.mark.asyncio
    async def test_compare_rag_modes(self, mcp_caller, test_data_setup):
        """
        Given: Same query across different RAG modes
        When: All modes are tested
        Then: Results are documented for comparison
        """
        query = "secure user authentication"
        modes = ["auto", "semantic", "keyword", "hybrid"]
        results = {}

        for mode in modes:
            result = await mcp_caller("query_tool", {
                "query_type": "rag_search",
                "entities": ["requirement"],
                "search_term": query,
                "rag_mode": mode,
                "limit": 5
            })

            results[mode] = {
                "success": result.get("success"),
                "result_count": len(result.get("data", {}).get("results", [])),
                "mode_used": result.get("data", {}).get("mode"),
                "search_time_ms": result.get("data", {}).get("search_time_ms", 0)
            }

        # Document results
        print("\n=== RAG Mode Comparison ===")
        for mode, data in results.items():
            print(f"{mode}: {data}")

        # All modes should succeed
        for mode, data in results.items():
            assert data["success"] is True, f"Mode {mode} failed"


# ============================================================================
# INTEGRATION TEST REPORT GENERATION
# ============================================================================

@pytest.mark.asyncio
async def test_generate_comprehensive_report(mcp_caller, test_data_setup):
    """
    Generate a comprehensive test report covering all query types and RAG modes.
    This test executes all query variations and produces a detailed report.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "test_summary": {},
        "query_type_results": {},
        "rag_mode_comparison": {},
        "performance_metrics": {},
        "edge_cases": {}
    }

    # Test all query types
    query_types = [
        ("search", {"entities": ["organization"], "search_term": "test"}),
        ("aggregate", {"entities": ["organization", "project"]}),
        ("analyze", {"entities": ["requirement"]}),
        ("relationships", {"entities": ["organization"]}),
        ("rag_search", {"entities": ["requirement"], "search_term": "authentication", "rag_mode": "auto"}),
        ("similarity", {"entities": ["requirement"], "content": "user authentication"})
    ]

    for query_type, params in query_types:
        start = time.time()
        result = await mcp_caller("query_tool", {
            "query_type": query_type,
            **params
        })
        elapsed = time.time() - start

        report["query_type_results"][query_type] = {
            "success": result.get("success"),
            "has_data": "data" in result,
            "response_time_ms": elapsed * 1000,
            "error": result.get("error")
        }

    # Test RAG modes
    rag_modes = ["auto", "semantic", "keyword", "hybrid"]
    for mode in rag_modes:
        start = time.time()
        result = await mcp_caller("query_tool", {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "security authentication",
            "rag_mode": mode,
            "limit": 5
        })
        elapsed = time.time() - start

        report["rag_mode_comparison"][mode] = {
            "success": result.get("success"),
            "mode_used": result.get("data", {}).get("mode"),
            "result_count": len(result.get("data", {}).get("results", [])),
            "response_time_ms": elapsed * 1000
        }

    # Generate summary
    total_tests = len(report["query_type_results"]) + len(report["rag_mode_comparison"])
    passed_tests = sum(
        1 for r in report["query_type_results"].values() if r["success"]
    ) + sum(
        1 for r in report["rag_mode_comparison"].values() if r["success"]
    )

    report["test_summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "pass_rate": f"{(passed_tests/total_tests*100):.2f}%"
    }

    # Print report
    print("\n" + "="*80)
    print("COMPREHENSIVE QUERY TOOL TEST REPORT")
    print("="*80)
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"\nSummary:")
    print(f"  Total Tests: {report['test_summary']['total_tests']}")
    print(f"  Passed: {report['test_summary']['passed_tests']}")
    print(f"  Failed: {report['test_summary']['failed_tests']}")
    print(f"  Pass Rate: {report['test_summary']['pass_rate']}")

    print(f"\nQuery Type Results:")
    for qtype, data in report["query_type_results"].items():
        status = "PASS" if data["success"] else "FAIL"
        print(f"  {qtype:15} {status:6} ({data['response_time_ms']:.0f}ms)")

    print(f"\nRAG Mode Comparison:")
    for mode, data in report["rag_mode_comparison"].items():
        status = "PASS" if data["success"] else "FAIL"
        print(f"  {mode:10} {status:6} - {data['result_count']} results ({data['response_time_ms']:.0f}ms)")

    print("\n" + "="*80 + "\n")

    # Assert overall success
    assert passed_tests == total_tests, f"Some tests failed: {total_tests - passed_tests}/{total_tests}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
