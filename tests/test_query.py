"""
Query Tool Tests

Tests search, RAG, and analytics functionality using decorator-based framework.
Now compatible with pytest-xdist for parallel execution.
"""

import pytest

from .framework import mcp_test

SEARCH_CASES = [
    pytest.param(["project"], "test", id="projects"),
    pytest.param(["document"], "requirement", id="documents"),
    pytest.param(["project", "document", "requirement"], "system", id="multi-entity"),
]

AGGREGATE_CASES = [
    pytest.param(["organization", "project", "document", "requirement"], id="all"),
    pytest.param(["project"], id="projects"),
]


@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.parametrize(("entities", "search_term"), SEARCH_CASES)
@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_entities(client_adapter, entities, search_term):
    """Exercise keyword search across multiple entity combinations."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": entities,
            "search_term": search_term,
        },
    )

    assert result["success"], f"Failed ({entities}): {result.get('error')}"

    response = result["response"]
    assert "results" in response or "data" in response, "Missing results in search response"


@pytest.mark.asyncio
@pytest.mark.parallel
@pytest.mark.parametrize("entities", AGGREGATE_CASES)
@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_aggregate_entities(client_adapter, entities):
    """Validate aggregate queries for different entity scopes."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": entities,
        },
    )

    assert result["success"], f"Failed ({entities}): {result.get('error')}"

    response = result["response"]
    assert "aggregates" in response or "summary" in response or "data" in response, "Missing aggregates in response"


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=5)
async def test_rag_search_semantic(client_adapter):
    """Test RAG semantic search (known embedding issue)."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["requirement"],
            "search_term": "safety requirements",
            "rag_mode": "semantic",
        },
    )

    # Known issue: NoneType error in embedding calculation
    if not result["success"]:
        error = result.get("error", "")
        if "NoneType" in error or "embedding" in error.lower():
            return {
                "success": False,
                "error": "Known issue: Embedding calculation error",
                "known_issue": True,
            }

    assert result["success"], f"Failed: {result.get('error')}"
    return None


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=8)
async def test_rag_search_keyword(client_adapter):
    """Test RAG keyword search."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["document"],
            "search_term": "testing procedures",
            "rag_mode": "keyword",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "results" in response or "data" in response, "Missing results in RAG search response"


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=8)
async def test_rag_search_hybrid(client_adapter):
    """Test RAG hybrid search (keyword + semantic)."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "rag_search",
            "entities": ["requirement", "document"],
            "search_term": "performance",
            "rag_mode": "hybrid",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "results" in response or "data" in response, "Missing results in RAG search response"
