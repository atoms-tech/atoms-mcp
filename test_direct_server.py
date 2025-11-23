#!/usr/bin/env python3
"""Direct HTTP test against local MCP server to verify it's working.

This bypasses all mocking and hits the actual HTTP server.
Run with: python test_direct_server.py (after starting server)
"""

import asyncio
import httpx
import os
import sys

async def main():
    # Check if server is running
    base_url = "http://localhost:8000"
    
    print("🧪 Direct Server Test")
    print("=" * 60)
    print(f"Target: {base_url}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test 1: Health check
            print("Test 1: Health check (/health)")
            health_resp = await client.get(f"{base_url}/health")
            print(f"  Status: {health_resp.status_code}")
            print(f"  Response: {health_resp.json()}")
            print()
            
            # Test 2: Root endpoint
            print("Test 2: Root endpoint (/)")
            root_resp = await client.get(f"{base_url}/")
            print(f"  Status: {root_resp.status_code}")
            print(f"  Response: {root_resp.json()}")
            print()
            
            # Test 3: Debug tools
            print("Test 3: Debug tools endpoint (/debug/tools)")
            tools_resp = await client.get(f"{base_url}/debug/tools")
            print(f"  Status: {tools_resp.status_code}")
            tools_data = tools_resp.json()
            print(f"  Total tools registered: {tools_data.get('total_tools', 0)}")
            if tools_data.get('tools'):
                print("  Tools:")
                for tool in tools_data['tools'][:5]:
                    print(f"    - {tool['name']}")
                if len(tools_data['tools']) > 5:
                    print(f"    ... and {len(tools_data['tools']) - 5} more")
            print()
            
            # Test 4: MCP POST (requires token, will likely fail but should show HTTP response)
            print("Test 4: MCP endpoint POST (/api/mcp)")
            print("  (Expecting 401 or 400 without proper auth header)")
            mcp_resp = await client.post(
                f"{base_url}/api/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                headers={"Content-Type": "application/json"}
            )
            print(f"  Status: {mcp_resp.status_code}")
            try:
                print(f"  Response: {mcp_resp.json()}")
            except:
                print(f"  Response text: {mcp_resp.text[:200]}")
            print()
            
            print("✅ Server is responding!")
            return 0
            
    except httpx.ConnectError as e:
        print(f"❌ Cannot connect to server at {base_url}")
        print(f"   Error: {e}")
        print()
        print("Make sure the server is running:")
        print("   Option 1: python app.py")
        print("   Option 2: vercel dev --listen 8000")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
