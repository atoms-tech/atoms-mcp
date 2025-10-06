#!/usr/bin/env python3
"""Simplified test client that works with Atoms' session-based auth.

This client manually handles the AuthKit OAuth flow to get a session_id,
then uses that session_id as a Bearer token for subsequent requests.
"""

import asyncio
import webbrowser
import httpx
from typing import Optional
import json

MCP_ENDPOINT = "https://mcp.atoms.tech/api/mcp"


async def get_session_via_oauth() -> Optional[str]:
    """Open browser for OAuth and get session_id.

    Returns:
        session_id (UUID string) or None
    """
    print("\n🔐 Starting OAuth flow...")
    print(f"📡 Endpoint: {MCP_ENDPOINT}")

    # Open browser to start OAuth
    auth_url = f"{MCP_ENDPOINT}/auth/start"
    print(f"\n🌐 Opening browser: {auth_url}")
    webbrowser.open(auth_url)

    print("\n⏳ Complete the login in your browser...")
    print("   After authentication, you should see a success page.")
    print("\n📋 The session_id will be in the MCP client's token cache.")
    print("   For this test, please paste your session_id here:")
    print("   (You can find it in ~/.fastmcp/oauth-mcp-client-cache/ if using FastMCP)")

    session_id = input("\nSession ID: ").strip()

    if not session_id:
        print("❌ No session_id provided")
        return None

    return session_id


async def test_tools_with_session(session_id: str):
    """Test MCP tools using session_id as Bearer token."""

    print(f"\n✅ Using session_id: {session_id[:8]}...{session_id[-8:]}")

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {session_id}",
            "Content-Type": "application/json"
        }

        # Test 1: List tools
        print("\n📋 Test 1: Listing tools...")
        list_req = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }

        response = await client.post(MCP_ENDPOINT, json=list_req, headers=headers)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                tools = data["result"].get("tools", [])
                print(f"   ✅ Found {len(tools)} tools")
                for tool in tools[:5]:  # Show first 5
                    print(f"      - {tool.get('name')}")
            else:
                print(f"   ❌ Unexpected response: {data}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False

        # Test 2: Call workspace_tool
        print("\n📋 Test 2: Calling workspace_tool...")
        call_req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "workspace_tool",
                "arguments": {
                    "operation": "list_workspaces"
                }
            },
            "id": 2
        }

        response = await client.post(MCP_ENDPOINT, json=call_req, headers=headers)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                result = data["result"]
                # Parse the content
                if "content" in result and len(result["content"]) > 0:
                    text = result["content"][0].get("text", "{}")
                    parsed = json.loads(text)
                    print(f"   ✅ Result: {json.dumps(parsed, indent=2)[:200]}...")
                else:
                    print(f"   Result: {result}")
            else:
                print(f"   ❌ Error in response: {data}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False

        # Test 3: Call entity_tool
        print("\n📋 Test 3: Calling entity_tool (list projects)...")
        call_req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "entity_tool",
                "arguments": {
                    "entity_type": "project",
                    "operation": "list"
                }
            },
            "id": 3
        }

        response = await client.post(MCP_ENDPOINT, json=call_req, headers=headers)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                result = data["result"]
                if "content" in result and len(result["content"]) > 0:
                    text = result["content"][0].get("text", "{}")
                    parsed = json.loads(text)
                    count = parsed.get("count", 0)
                    print(f"   ✅ Found {count} projects")
                else:
                    print(f"   Result: {result}")
            else:
                print(f"   ❌ Error in response: {data}")
        else:
            print(f"   ❌ Error: {response.text}")
            return False

        print("\n✅ All tests passed!")
        return True


async def main():
    """Main entry point."""
    print("="*80)
    print("ATOMS MCP SIMPLE TEST CLIENT")
    print("="*80)

    # Get session_id via OAuth
    session_id = await get_session_via_oauth()

    if not session_id:
        print("\n❌ Failed to get session_id")
        return 1

    # Test tools with session
    success = await test_tools_with_session(session_id)

    if success:
        print("\n✅ Test client completed successfully!")
        return 0
    else:
        print("\n❌ Test client failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
