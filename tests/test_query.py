"""
Query Tool Tests

Tests search, RAG, and analytics functionality using decorator-based framework.
"""

from .framework import mcp_test


@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_projects(client):
    """Test keyword search for projects."""
    result = await client.call_tool(
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

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_documents(client):
    """Test keyword search for documents."""
    result = await client.call_tool(
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

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_search_multi_entity(client):
    """Test multi-entity keyword search."""
    result = await client.call_tool(
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

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_aggregate_all(client):
    """Test aggregating statistics across all entity types."""
    result = await client.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["organization", "project", "document", "requirement"],
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "aggregates" in response or "summary" in response or "data" in response, "Missing aggregates in response"

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=10)
async def test_aggregate_projects(client):
    """Test aggregating project statistics."""
    result = await client.call_tool(
        "query_tool",
        {
            "query_type": "aggregate",
            "entities": ["project"],
        },
    )

    assert result["success"], f"Failed: {result.get('error')}"

    response = result["response"]
    assert "aggregates" in response or "summary" in response or "data" in response, "Missing aggregates in response"

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=5)
async def test_rag_search_semantic(client):
    """Test RAG semantic search (known embedding issue)."""
    result = await client.call_tool(
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

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=8)
async def test_rag_search_keyword(client):
    """Test RAG keyword search."""
    result = await client.call_tool(
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

    return {"success": True, "error": None}


@mcp_test(tool_name="query_tool", category="query", priority=8)
async def test_rag_search_hybrid(client):
    """Test RAG hybrid search (keyword + semantic)."""
    result = await client.call_tool(
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

    return {"success": True, "error": None}
