"""
MCP-QA Fixtures - Comprehensive Testing Fixtures for MCP Servers

Provides pytest fixtures for:
- Server management (mcp_server, test_server)
- Client creation (mcp_client, authenticated_client)
- Database isolation (isolated_database, db_pool)
- Worker-scoped resources for parallel testing
- Authentication and OAuth flows
- Tool-specific clients

Usage:
    from mcp_qa.fixtures import mcp_server, mcp_client, authenticated_client

    async def test_my_tool(mcp_client):
        result = await mcp_client.call_tool("my_tool", {"param": "value"})
        assert result["success"]
"""

from mcp_qa.fixtures.auth import (
    session_token_manager,
    oauth_tokens,
    authenticated_mcp_client,
    oauth_client_factory,
    clear_oauth_cache,
)

from mcp_qa.fixtures.clients import (
    http_client,
    mcp_client,
    mcp_client_pool,
    isolated_client,
    fast_http_tools,
)

from mcp_qa.fixtures.servers import (
    mcp_server,
    test_server,
    mock_server,
    server_factory,
)

from mcp_qa.fixtures.database import (
    isolated_database,
    db_pool,
    test_database,
)

from mcp_qa.fixtures.workers import (
    worker_id,
    worker_port,
    worker_database,
    worker_cleanup,
)

from mcp_qa.fixtures.tools import (
    tool_client_factory,
    chat_tool_client,
    query_tool_client,
)

__all__ = [
    # Authentication
    "session_token_manager",
    "oauth_tokens",
    "authenticated_mcp_client",
    "oauth_client_factory",
    "clear_oauth_cache",

    # Clients
    "http_client",
    "mcp_client",
    "mcp_client_pool",
    "isolated_client",
    "fast_http_tools",

    # Servers
    "mcp_server",
    "test_server",
    "mock_server",
    "server_factory",

    # Database
    "isolated_database",
    "db_pool",
    "test_database",

    # Workers
    "worker_id",
    "worker_port",
    "worker_database",
    "worker_cleanup",

    # Tools
    "tool_client_factory",
    "chat_tool_client",
    "query_tool_client",
]
