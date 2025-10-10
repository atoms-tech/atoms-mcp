#!/usr/bin/env python3
"""Simple OAuth test for Atoms MCP using FastMCP built-in OAuth."""

import asyncio

from fastmcp import Client

MCP_URL = "https://mcp.atoms.tech/api/mcp"

async def main():
    print(f"Connecting to {MCP_URL} with OAuth...")
    print("This will open a browser for authentication.")
    print()

    # Use FastMCP's built-in OAuth - it handles everything automatically
    async with Client(MCP_URL, auth="oauth") as client:
        print("✅ Connected and authenticated!")
        print()

        # List available tools
        print("📋 Available tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}")
        print()

        # Test workspace_tool
        print("🧪 Testing workspace_tool...")
        result = await client.call_tool(
            "workspace_tool",
            {"operation": "get_context", "format_type": "summary"}
        )
        print(f"Result: {result}")
        print()

        # Test entity list
        print("🧪 Testing entity_tool (list organizations)...")
        result = await client.call_tool(
            "entity_tool",
            {"entity_type": "organization", "operation": "list", "limit": 5}
        )
        print(f"Organizations count: {result.get('count', 0)}")
        print()

        print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
