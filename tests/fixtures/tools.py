"""Tool-specific fixtures for granular testing of individual MCP tools."""

from collections.abc import Callable
from typing import Any

import pytest

from ..framework.auth_session import AuthenticatedHTTPClient


class ToolClient:
    """Wrapper for tool-specific operations.

    Fixed to use the correct API pattern based on working test examples:
    - Tool names: "workspace_tool" not "workspace_operation"
    - Parameters: flat structure, not nested in "params"
    - Auth: handled via Authorization header only
    """

    def __init__(self, http_client: AuthenticatedHTTPClient, operation_name: str):
        self.http_client = http_client
        # Map operation names to actual tool names in the API
        tool_name_mapping = {
            "workspace_operation": "workspace_tool",
            "entity_operation": "entity_tool",
            "relationship_operation": "relationship_tool",
            "workflow_execute": "workflow_tool",
            "data_query": "query_tool"
        }
        self.tool_name = tool_name_mapping.get(operation_name, operation_name)
        self.operation_name = operation_name

    async def call(self, operation: str, arguments: dict[str, Any] = None, **kwargs) -> dict[str, Any]:
        """Call the tool with operation and parameters.

        Uses the same parameter structure as working tests:
        - Direct parameters (not nested in "params")
        - "operation" parameter for the specific operation
        - Auth handled via Authorization Bearer header
        """
        # Construct parameters as in working tests
        tool_params = {
            "operation": operation
        }

        # Add any provided arguments directly (not nested)
        if arguments:
            tool_params.update(arguments)

        # Add any additional kwargs
        if kwargs:
            tool_params.update(kwargs)

        return await self.http_client.call_tool(self.tool_name, tool_params)

    async def health_check(self) -> bool:
        """Quick health check for the tool."""
        try:
            result = await self.call("health_check")
            return result.get("success", False)
        except Exception:
            return False


@pytest.fixture
async def workspace_client(authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Client specifically for workspace_operation tool.

    Usage:
        async def test_list_projects(workspace_client):
            result = await workspace_client.call("list_projects")
            assert result["success"]
    """
    return ToolClient(authenticated_client, "workspace_operation")


@pytest.fixture
async def entity_client(authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Client specifically for entity_operation tool.

    Usage:
        async def test_create_document(entity_client):
            result = await entity_client.call("create", {
                "entity_type": "document",
                "data": {"title": "Test Doc", "content": "Test content"}
            })
            assert result["success"]
    """
    return ToolClient(authenticated_client, "entity_operation")


@pytest.fixture
async def relationship_client(authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Client specifically for relationship_operation tool."""
    return ToolClient(authenticated_client, "relationship_operation")


@pytest.fixture
async def workflow_client(authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Client specifically for workflow_execute tool."""
    return ToolClient(authenticated_client, "workflow_execute")


@pytest.fixture
async def query_client(authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Client specifically for query_tool."""
    return ToolClient(authenticated_client, "query_tool")


@pytest.fixture
def tool_client_factory(authenticated_client: AuthenticatedHTTPClient) -> Callable[[str], ToolClient]:
    """Factory for creating clients for any tool.

    Usage:
        def test_custom_tool(tool_client_factory):
            client = tool_client_factory("my_custom_tool")
            result = await client.call("some_operation")
    """
    def create_tool_client(tool_name: str) -> ToolClient:
        return ToolClient(authenticated_client, tool_name)

    return create_tool_client


# Mock versions for unit testing
@pytest.fixture
def mock_workspace_client(mock_authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Mock workspace client for unit tests."""
    return ToolClient(mock_authenticated_client, "workspace_operation")


@pytest.fixture
def mock_entity_client(mock_authenticated_client: AuthenticatedHTTPClient) -> ToolClient:
    """Mock entity client for unit tests."""
    return ToolClient(mock_authenticated_client, "entity_operation")


# Batch operation helpers
class BatchToolClient:
    """Client for batch operations across multiple tools."""

    def __init__(self, http_client: AuthenticatedHTTPClient):
        self.http_client = http_client
        self._tool_clients = {}

    def get_tool_client(self, tool_name: str) -> ToolClient:
        """Get or create a tool client."""
        if tool_name not in self._tool_clients:
            self._tool_clients[tool_name] = ToolClient(self.http_client, tool_name)
        return self._tool_clients[tool_name]

    async def call_multiple(self, operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Call multiple tools in sequence.

        Args:
            operations: List of {"tool": "tool_name", "operation": "op", "params": {...}}
        """
        results = []
        for op in operations:
            client = self.get_tool_client(op["tool"])
            result = await client.call(op["operation"], op.get("params", {}))
            results.append(result)
        return results


@pytest.fixture
async def batch_client(authenticated_client: AuthenticatedHTTPClient) -> BatchToolClient:
    """Client for batch operations across multiple tools."""
    return BatchToolClient(authenticated_client)


# Tool discovery and validation
@pytest.fixture
async def available_tools(authenticated_client: AuthenticatedHTTPClient) -> list[str]:
    """List of available tools from the server.

    Useful for dynamic test generation or validation.
    """
    try:
        result = await authenticated_client.list_tools()
        if "result" in result and "tools" in result["result"]:
            return [tool["name"] for tool in result["result"]["tools"]]
        return []
    except Exception:
        return []


@pytest.fixture
async def tool_schemas(authenticated_client: AuthenticatedHTTPClient) -> dict[str, dict]:
    """Tool schemas for validation and test generation."""
    try:
        result = await authenticated_client.list_tools()
        if "result" in result and "tools" in result["result"]:
            return {
                tool["name"]: tool.get("inputSchema", {})
                for tool in result["result"]["tools"]
            }
        return {}
    except Exception:
        return {}


# Performance testing helpers
class PerformanceToolClient:
    """Tool client with performance monitoring."""

    def __init__(self, tool_client: ToolClient):
        self.tool_client = tool_client
        self.call_times = []

    async def call(self, operation: str, params: dict[str, Any] = None, **kwargs) -> dict[str, Any]:
        """Call tool with timing measurement."""
        import time
        start_time = time.time()
        try:
            result = await self.tool_client.call(operation, params, **kwargs)
            return result
        finally:
            end_time = time.time()
            self.call_times.append(end_time - start_time)

    @property
    def avg_call_time(self) -> float:
        """Average call time in seconds."""
        return sum(self.call_times) / len(self.call_times) if self.call_times else 0.0

    @property
    def total_calls(self) -> int:
        """Total number of calls made."""
        return len(self.call_times)


@pytest.fixture
def performance_workspace_client(workspace_client: ToolClient) -> PerformanceToolClient:
    """Performance-monitoring workspace client."""
    return PerformanceToolClient(workspace_client)


@pytest.fixture
def performance_entity_client(entity_client: ToolClient) -> PerformanceToolClient:
    """Performance-monitoring entity client."""
    return PerformanceToolClient(entity_client)
