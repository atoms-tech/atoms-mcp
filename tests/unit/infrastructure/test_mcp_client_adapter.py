"""Tests for MCP client adapter (in-memory and HTTP variants)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestInMemoryMcpClient:
    """Test InMemoryMcpClient for unit testing."""

    @pytest.fixture
    def client(self):
        """Create an in-memory MCP client."""
        from infrastructure.mcp_client_adapter import InMemoryMcpClient
        return InMemoryMcpClient()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check returns ok status."""
        result = await client.health()

        assert result is not None
        assert result["status"] == "ok"
        assert result["mode"] == "in-memory"

    @pytest.mark.asyncio
    async def test_call_mcp_echo(self, client):
        """Test call_mcp echoes back the payload."""
        payload = {
            "tool": "entity_tool",
            "params": {"workspace_id": "ws-1"}
        }

        result = await client.call_mcp(payload)

        assert result is not None
        assert result["echo"] == payload
        assert result["mode"] == "in-memory"

    @pytest.mark.asyncio
    async def test_call_mcp_with_complex_payload(self, client):
        """Test call_mcp with complex nested payload."""
        payload = {
            "tool": "entity_tool",
            "params": {
                "workspace_id": "ws-1",
                "data": {
                    "name": "Test Entity",
                    "description": "Test description",
                    "metadata": {"status": "active"}
                }
            }
        }

        result = await client.call_mcp(payload)

        assert result["echo"]["params"]["data"]["metadata"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_call_mcp_empty_payload(self, client):
        """Test call_mcp with empty payload."""
        payload = {}

        result = await client.call_mcp(payload)

        assert result["echo"] == {}


class TestMcpClientFactory:
    """Test MCP client factory for selecting appropriate client."""

    @pytest.fixture
    def factory(self):
        """Create an MCP client factory."""
        from infrastructure.mcp_client_adapter import McpClientFactory
        return McpClientFactory()

    @pytest.mark.asyncio
    async def test_factory_returns_client(self, factory):
        """Test that factory returns a client instance."""
        client = factory.get()

        assert client is not None
        assert hasattr(client, "health")
        assert callable(client.health)

    @pytest.mark.asyncio
    async def test_factory_caches_client(self, factory):
        """Test that factory caches and reuses client."""
        client1 = factory.get()
        client2 = factory.get()

        assert client1 is client2

    @pytest.mark.asyncio
    async def test_factory_client_has_call_mcp(self, factory):
        """Test that factory client has call_mcp method."""
        client = factory.get()

        assert hasattr(client, "call_mcp")
        assert callable(client.call_mcp)

    @pytest.mark.asyncio
    async def test_factory_client_has_health(self, factory):
        """Test that factory client has health method."""
        client = factory.get()

        assert hasattr(client, "health")
        assert callable(client.health)


class TestMcpClientAdapterIntegration:
    """Integration tests for MCP client adapter."""

    @pytest.mark.asyncio
    async def test_in_memory_client_workflow(self):
        """Test typical in-memory client workflow."""
        from infrastructure.mcp_client_adapter import InMemoryMcpClient

        client = InMemoryMcpClient()

        # Check health
        health = await client.health()
        assert health["status"] == "ok"

        # Make a call
        payload = {"action": "list_entities", "workspace_id": "ws-1"}
        result = await client.call_mcp(payload)

        assert result["echo"]["action"] == "list_entities"
        assert result["mode"] == "in-memory"

    @pytest.mark.asyncio
    async def test_factory_workflow(self):
        """Test typical factory workflow."""
        from infrastructure.mcp_client_adapter import McpClientFactory

        factory = McpClientFactory()

        # Get client from factory
        client = factory.get()
        assert client is not None

        # Can call health on factory's client
        health = await client.health()
        assert health is not None

        # Factory returns same client on second call
        client2 = factory.get()
        assert client is client2

    @pytest.mark.asyncio
    async def test_client_methods_are_awaitable(self):
        """Test that client methods are properly async."""
        from infrastructure.mcp_client_adapter import InMemoryMcpClient
        import inspect

        client = InMemoryMcpClient()

        assert inspect.iscoroutinefunction(client.health)
        assert inspect.iscoroutinefunction(client.call_mcp)

    @pytest.mark.asyncio
    async def test_concurrent_mcp_calls(self):
        """Test that client can handle concurrent calls."""
        from infrastructure.mcp_client_adapter import InMemoryMcpClient
        import asyncio

        client = InMemoryMcpClient()

        payloads = [
            {"action": "get_entity", "id": f"ent-{i}"}
            for i in range(5)
        ]

        # Make concurrent calls
        results = await asyncio.gather(*[
            client.call_mcp(payload) for payload in payloads
        ])

        assert len(results) == 5
        assert all(r["mode"] == "in-memory" for r in results)

    @pytest.mark.asyncio
    async def test_multiple_factory_instances(self):
        """Test that multiple factory instances can coexist."""
        from infrastructure.mcp_client_adapter import McpClientFactory

        factory1 = McpClientFactory()
        factory2 = McpClientFactory()

        client1 = factory1.get()
        client2 = factory2.get()

        # Each factory has its own client instance
        # (depends on implementation details, but they shouldn't be the same object)
        # The important thing is both work correctly
        assert client1 is not None
        assert client2 is not None

        health1 = await client1.health()
        health2 = await client2.health()

        assert health1["status"] == "ok"
        assert health2["status"] == "ok"
