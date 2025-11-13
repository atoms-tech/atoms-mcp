"""Example of switching between live/local/mock modes via environment.

Run with:
  # Mock all services (in-memory)
  ATOMS_SERVICE_MODE=mock python example_usage.py

  # Live MCP against production, mock Supabase/AuthKit
  ATOMS_SERVICE_MODE=mock ATOMS_MCP_CLIENT_MODE=live python example_usage.py

  # HTTP MCP against local server
  ATOMS_SERVICE_MODE=mock ATOMS_MCP_CLIENT_MODE=local ATOMS_MCP_LOCAL_PORT=8000 python example_usage.py
"""

import asyncio

try:
    from infrastructure.mcp_client_adapter import McpClientFactory
    from infrastructure.factory import AdapterFactory
    from infrastructure.mock_config import get_service_config
except ImportError:
    from mcp_client_adapter import McpClientFactory
    from factory import AdapterFactory
    from mock_config import get_service_config


async def main():
    cfg = get_service_config()
    print("Service config:", cfg.to_dict())

    # MCP client demo
    mcp_client = McpClientFactory().get()
    health = await mcp_client.health()
    print("MCP health:", health)

    # Adapters demo
    factory = AdapterFactory()
    adapters = factory.get_all_adapters()

    # Database
    await adapters["database"].insert("demo", {"id": 1, "name": "hello"})
    row = await adapters["database"].get_single("demo", filters={"id": 1})
    print("DB row:", row)

    # Auth
    token = await adapters["auth"].create_session("user-1", "demo@example.com")
    user = await adapters["auth"].validate_token(token)
    print("Auth user:", user)

    # Storage
    url = await adapters["storage"].upload("bucket", "path.txt", b"data")
    print("Uploaded URL:", url)

if __name__ == "__main__":
    asyncio.run(main())
