"""MCP client adapter interface with in-memory and HTTP variants."""

from __future__ import annotations

from typing import Any, Dict

try:
    from .mock_adapters import HttpMcpClient
    from .mock_config import get_service_config, ServiceMode
except ImportError:
    from infrastructure.mock_adapters import HttpMcpClient
    from infrastructure.mock_config import get_service_config, ServiceMode


class InMemoryMcpClient:
    """Trivial in-memory MCP client useful for unit tests."""

    async def health(self) -> Dict[str, Any]:
        return {"status": "ok", "mode": "in-memory"}

    async def call_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Echo response for tests
        return {"echo": payload, "mode": "in-memory"}


class McpClientFactory:
    def __init__(self):
        self._config = get_service_config()
        self._client = None

    def get(self):
        if self._client is not None:
            return self._client
        mode = self._config.get_service_mode("mcp_client")
        if mode == ServiceMode.MOCK:
            self._client = InMemoryMcpClient()
        else:
            endpoint = self._config.get_mcp_endpoint()
            self._client = HttpMcpClient(endpoint)
        return self._client
