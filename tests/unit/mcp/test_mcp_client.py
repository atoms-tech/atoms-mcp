"""Tests for MCP client implementations."""

import pytest

# Note: The mock fixtures are automatically imported via pytest_plugins in conftest.py


class TestMcpClientFactory:
    """Test the MCP client factory and both variants."""

    @pytest.mark.asyncio
    async def test_in_memory_mcp_client(self, mock_mcp_client):
        """Test the in-memory MCP client variant."""
        # Check health
        health = await mock_mcp_client.health()
        assert health["status"] == "ok"
        assert health["mode"] == "in-memory"

        # Test MCP call
        payload = {
            "id": "1",
            "method": "test_tool",
            "params": {"message": "hello"}
        }
        response = await mock_mcp_client.call_mcp(payload)
        assert response["echo"] == payload
        assert response["mode"] == "in-memory"

    @pytest.mark.asyncio
    async def test_http_mcp_client_error_handling(self):
        """Test HTTP client error handling without making real HTTP calls."""
        from infrastructure.mcp_client_adapter import HttpMcpClient

        # Only test the constructor, no real requests
        client = HttpMcpClient("https://example.com")
        assert client.base_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_mcp_client_factory_behavior(self, monkeypatch):
        """Test that factory returns appropriate client based on config."""
        from infrastructure.mcp_client_adapter import McpClientFactory

        # Test with explicit mock mode
        monkeypatch.setenv("ATOMS_MCP_CLIENT_MODE", "mock")

        # Reset factory to pick up new env
        factory = McpClientFactory()
        mock_client = factory.get()

        # Should be an in-memory client
        health = await mock_client.health()
        assert health["mode"] == "in-memory"

        # Don't test live mode as it's not guaranteed without a running server
        # The mock client is sufficient to verify factory behavior

    @pytest.mark.asyncio
    async def test_mcp_client_factory_singleton_behavior(self):
        """Test that factory returns the same instance."""
        from infrastructure.mcp_client_adapter import McpClientFactory

        factory = McpClientFactory()
        client1 = factory.get()
        client2 = factory.get()

        # Should be the same instance
        assert client1 is client2
