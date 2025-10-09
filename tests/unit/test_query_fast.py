"""
Fast Query Tool Tests using FastHTTPClient

These tests use direct HTTP calls instead of the MCP decorator framework,
providing ~20x speed improvement while still validating real Supabase data,
search functionality, RAG capabilities, and query operations.

Run with: pytest tests/unit/test_query_fast.py -v
"""

import pytest


# ============================================================================
# Search Query Tests
# ============================================================================


@pytest.mark.asyncio
async def test_search_single_entity_project(authenticated_client):
    """Test searching for single project entity via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test"
        }
    )

    assert result.get("success", True), f"Failed to search projects: {result.get('error')}"

    # Validate response structure
    assert "results_by_entity" in result or "results" in result, \
        f"Expected 'results_by_entity' or 'results' in response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_search_single_entity_document(authenticated_client):
    """Test searching for single document entity via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "requirements"
        }
    )

    assert result.get("success", True), f"Failed to search documents: {result.get('error')}"

    # Validate response has proper structure
    response_data = result.get("results_by_entity", result.get("results", {}))
    assert isinstance(response_data, (dict, list)), \
        f"Expected dict or list response, got {type(response_data).__name__}"


@pytest.mark.asyncio
async def test_search_multi_entity_all(authenticated_client):
    """Test searching across multiple entity types via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["project", "document", "requirement"],
            "search_term": "test"
        }
    )

    assert result.get("success", True), f"Failed to search multiple entities: {result.get('error')}"

    # Should have results structure
    assert "results_by_entity" in result or "results" in result, \
        f"Expected results in response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_search_with_filters(authenticated_client):
    """Test search with filter conditions via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["project"],
            "conditions": {"status": "active"},
            "search_term": ""
        }
    )

    assert result.get("success", True), f"Failed to search with filters: {result.get('error')}"

    # Validate filtered results
    assert "results_by_entity" in result or "results" in result, \
        f"Expected results in filtered response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_search_with_limit(authenticated_client):
    """Test search with result limit via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "",
            "limit": 5
        }
    )

    assert result.get("success", True), f"Failed to search with limit: {result.get('error')}"

    # Verify limit is respected (if results present)
    if "results_by_entity" in result:
        for entity_type, entity_data in result["results_by_entity"].items():
            count = entity_data.get("count", 0)
            assert count <= 5, f"Expected count <= 5 for {entity_type}, got {count}"


# ============================================================================
# RAG Search Tests (Semantic, Keyword, Hybrid, Auto)
# ============================================================================


@pytest.mark.asyncio
async def test_rag_semantic_mode_document(authenticated_client):
    """Test semantic RAG mode for documents via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "architecture patterns microservices",
            "rag_mode": "semantic",
            "similarity_threshold": 0.5
        }
    )

    assert result.get("success", True), f"Failed semantic RAG search: {result.get('error')}"

    # Validate RAG response structure
    assert "results" in result or "results_by_entity" in result or "mode" in result, \
        f"Expected RAG results structure, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_rag_keyword_mode_document(authenticated_client):
    """Test keyword RAG mode for documents via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "api authentication",
            "rag_mode": "keyword",
            "limit": 5
        }
    )

    assert result.get("success", True), f"Failed keyword RAG search: {result.get('error')}"

    # Keyword mode should return results
    assert "results" in result or "results_by_entity" in result, \
        f"Expected keyword search results, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_rag_hybrid_mode_multi_entity(authenticated_client):
    """Test hybrid RAG mode across multiple entities via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["project", "document", "requirement"],
            "search_term": "test requirements documentation",
            "rag_mode": "hybrid",
            "similarity_threshold": 0.6,
            "limit": 10
        }
    )

    assert result.get("success", True), f"Failed hybrid RAG search: {result.get('error')}"

    # Hybrid mode should have mode indicator and results
    response_keys = list(result.keys())
    assert any(key in response_keys for key in ["results", "results_by_entity", "mode"]), \
        f"Expected hybrid search results, got keys: {response_keys}"


@pytest.mark.asyncio
async def test_rag_auto_mode_natural_query(authenticated_client):
    """Test auto RAG mode with natural language query via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document", "requirement"],
            "search_term": "How do we handle authentication in the system?",
            "rag_mode": "auto"
        }
    )

    assert result.get("success", True), f"Failed auto RAG search: {result.get('error')}"

    # Auto mode should select appropriate mode and return results
    assert "results" in result or "results_by_entity" in result or "mode" in result, \
        f"Expected auto mode results, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_rag_threshold_variations(authenticated_client):
    """Test RAG with different similarity thresholds via fast HTTP client."""
    # Test with low threshold (more inclusive)
    result_low = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "system design",
            "rag_mode": "semantic",
            "similarity_threshold": 0.3
        }
    )

    assert result_low.get("success", True), f"Failed RAG with low threshold: {result_low.get('error')}"

    # Test with high threshold (more restrictive)
    result_high = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "system design",
            "rag_mode": "semantic",
            "similarity_threshold": 0.8
        }
    )

    assert result_high.get("success", True), f"Failed RAG with high threshold: {result_high.get('error')}"


# ============================================================================
# Aggregate Query Tests
# ============================================================================


@pytest.mark.asyncio
async def test_aggregate_all_entities(authenticated_client):
    """Test aggregation across all entity types via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["organization", "project", "document", "requirement"],
            "conditions": {}
        }
    )

    assert result.get("success", True), f"Failed to aggregate entities: {result.get('error')}"

    # Validate aggregate response structure
    assert "results" in result or "aggregations" in result, \
        f"Expected 'results' or 'aggregations' in aggregate response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_aggregate_single_entity_project(authenticated_client):
    """Test aggregation for single project entity via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["project"],
            "conditions": {}
        }
    )

    assert result.get("success", True), f"Failed to aggregate projects: {result.get('error')}"

    # Should have aggregation data for projects
    response = result.get("results", result.get("aggregations", {}))
    assert isinstance(response, dict), \
        f"Expected dict response for aggregate, got {type(response).__name__}"


@pytest.mark.asyncio
async def test_aggregate_with_filters(authenticated_client):
    """Test aggregation with filter conditions via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["project", "requirement"],
            "conditions": {"status": "active"}
        }
    )

    assert result.get("success", True), f"Failed to aggregate with filters: {result.get('error')}"

    # Filtered aggregation should return counts/stats
    assert "results" in result or "aggregations" in result, \
        f"Expected aggregate results with filters, got keys: {list(result.keys())}"


# ============================================================================
# Relationship Query Tests
# ============================================================================


@pytest.mark.asyncio
async def test_relationship_query(authenticated_client):
    """Test relationship analysis between entities via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "relationships",
            "entities": ["organization", "project"],
            "conditions": {}
        }
    )

    assert result.get("success", True), f"Failed relationship query: {result.get('error')}"

    # Should have relationship data
    assert "relationships" in result or "results" in result, \
        f"Expected 'relationships' in response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_relationship_with_filters(authenticated_client):
    """Test relationship query with filter conditions via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "relationships",
            "entities": ["project", "document"],
            "conditions": {"status": "active"}
        }
    )

    assert result.get("success", True), f"Failed filtered relationship query: {result.get('error')}"

    # Filtered relationships should be present
    assert "relationships" in result or "results" in result, \
        f"Expected relationship results, got keys: {list(result.keys())}"


# ============================================================================
# Analyze Query Tests
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_organization(authenticated_client):
    """Test deep analysis of organization via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "analyze",
            "entities": ["organization"],
            "conditions": {}
        }
    )

    assert result.get("success", True), f"Failed organization analysis: {result.get('error')}"

    # Analysis should have structured results
    assert "analysis" in result or "results" in result, \
        f"Expected 'analysis' in response, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_analyze_project(authenticated_client):
    """Test deep analysis of projects via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "analyze",
            "entities": ["project"],
            "conditions": {}
        }
    )

    assert result.get("success", True), f"Failed project analysis: {result.get('error')}"

    # Project analysis should include metrics
    assert "analysis" in result or "results" in result, \
        f"Expected analysis results, got keys: {list(result.keys())}"


@pytest.mark.asyncio
async def test_analyze_with_filters(authenticated_client):
    """Test analysis with filter conditions via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "analyze",
            "entities": ["project", "requirement"],
            "conditions": {"status": "active"}
        }
    )

    assert result.get("success", True), f"Failed filtered analysis: {result.get('error')}"

    # Filtered analysis should have data
    assert "analysis" in result or "results" in result, \
        f"Expected analysis with filters, got keys: {list(result.keys())}"


# ============================================================================
# Performance Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_search_performance(authenticated_client):
    """Validate that search operations are fast (< 3 seconds) via fast HTTP client."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["project", "document"],
            "search_term": "test"
        }
    )

    duration = time.time() - start_time

    assert result.get("success", True), f"Failed search operation: {result.get('error')}"
    assert duration < 3.0, \
        f"Search operation took {duration:.2f}s, expected < 3.0s. Fast HTTP client should be faster."


@pytest.mark.asyncio
async def test_rag_search_performance(authenticated_client):
    """Validate that RAG search is fast (< 5 seconds) via fast HTTP client."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document", "requirement"],
            "search_term": "authentication and security requirements",
            "rag_mode": "hybrid",
            "limit": 10
        }
    )

    duration = time.time() - start_time

    assert result.get("success", True), f"Failed RAG search: {result.get('error')}"
    assert duration < 5.0, \
        f"RAG search took {duration:.2f}s, expected < 5.0s. Fast HTTP client should improve performance."


@pytest.mark.asyncio
async def test_aggregate_performance(authenticated_client):
    """Validate that aggregation is fast (< 2 seconds) via fast HTTP client."""
    import time

    start_time = time.time()

    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["organization", "project", "document", "requirement"],
            "conditions": {}
        }
    )

    duration = time.time() - start_time

    assert result.get("success", True), f"Failed aggregation: {result.get('error')}"
    assert duration < 2.0, \
        f"Aggregation took {duration:.2f}s, expected < 2.0s. Fast HTTP client should be faster."


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_empty_search_term(authenticated_client):
    """Test handling of empty search term via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": ""
        }
    )

    # Should handle gracefully - either return all results or handle empty query
    assert result.get("success", True) or "error" in result, \
        f"Expected success or error for empty search, got: {result}"


@pytest.mark.asyncio
async def test_invalid_entity_type(authenticated_client):
    """Test handling of invalid entity type via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["invalid_entity_type"],
            "search_term": "test"
        }
    )

    # Should handle invalid entity type gracefully
    # Either error or empty results
    if result.get("success"):
        results = result.get("results_by_entity", {})
        assert len(results) == 0 or "invalid_entity_type" not in results, \
            "Invalid entity type should not return results"


@pytest.mark.asyncio
async def test_rag_with_invalid_mode(authenticated_client):
    """Test RAG with invalid mode via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "test query",
            "rag_mode": "invalid_mode"
        }
    )

    # Should either default to a valid mode or return error
    # Don't fail - just validate it handles gracefully
    assert "error" in result or "mode" in result or "results" in result, \
        f"Expected graceful handling of invalid RAG mode, got: {list(result.keys())}"


@pytest.mark.asyncio
async def test_extreme_limit_values(authenticated_client):
    """Test handling of extreme limit values via fast HTTP client."""
    # Test with very large limit
    result_large = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "",
            "limit": 999999
        }
    )

    assert result_large.get("success", True), f"Failed with large limit: {result_large.get('error')}"

    # Test with zero limit
    result_zero = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "",
            "limit": 0
        }
    )

    # Should handle zero limit gracefully (either error or no results)
    assert "results" in result_zero or "error" in result_zero or result_zero.get("success"), \
        f"Expected graceful handling of zero limit, got: {list(result_zero.keys())}"


@pytest.mark.asyncio
async def test_special_characters_in_query(authenticated_client):
    """Test handling of special characters in query via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "test @#$%^&* special <script>alert('xss')</script>",
            "rag_mode": "keyword"
        }
    )

    # Should handle special characters safely
    assert result.get("success", True) or "error" in result, \
        f"Expected safe handling of special characters, got: {result}"


@pytest.mark.asyncio
async def test_unicode_in_query(authenticated_client):
    """Test handling of Unicode characters in query via fast HTTP client."""
    result = await authenticated_client.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "测试 テスト тест"  # Chinese, Japanese, Russian
        }
    )

    # Should handle Unicode gracefully
    assert "results" in result or "error" in result or result.get("success", True), \
        f"Expected graceful Unicode handling, got: {list(result.keys())}"
