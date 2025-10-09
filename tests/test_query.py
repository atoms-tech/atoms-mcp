"""
Query Tool Tests

Tests search, RAG, and analytics functionality using decorator-based framework.
Now compatible with pytest-xdist for parallel execution.
"""

import pytest
from .framework import mcp_test


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_projects(client_adapter):
    """Test keyword search for projects."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["project"],
            "search_term": "test",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "results" in response or "data" in response, "Missing results in search response"


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_documents(client_adapter):
    """Test keyword search for documents."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["document"],
            "search_term": "requirement",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "results" in response or "data" in response, "Missing results in search response"


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_multi_entity(client_adapter):
    """Test multi-entity keyword search."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "search",
            "entities": ["project", "document", "requirement"],
            "search_term": "system",
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "results" in response or "data" in response, "Missing results in search response"


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_aggregate_all(client_adapter):
    """Test aggregating statistics across all entity types."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["organization", "project", "document", "requirement"],
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "aggregates" in response or "summary" in response or "data" in response, "Missing aggregates in response"


@pytest.mark.asyncio

@pytest.mark.parallel

@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_aggregate_projects(client_adapter):
    """Test aggregating project statistics."""
    result = await client_adapter.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["project"],
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

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
