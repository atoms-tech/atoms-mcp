#!/usr/bin/env python3
"""Test MCP server connection (initialize + list tools).

This script tests the MCP server by:
1. Initializing the connection
2. Listing available tools

Usage:
    python scripts/test_mcp_connection.py
    python scripts/test_mcp_connection.py --token YOUR_TOKEN
    python scripts/test_mcp_connection.py --url http://localhost:8000/api/mcp
    
Environment variables:
    - MCP_BASE_URL (optional, defaults to http://localhost:8000/api/mcp)
    - ATOMS_TEST_AUTH_TOKEN (optional, token can be passed via --token)
    - WORKOS_API_KEY, WORKOS_CLIENT_ID (optional, for auto-fetching token)

Options:
    --token TOKEN        Bearer token to use for authentication
    --url URL            MCP server URL (default: http://localhost:8000/api/mcp)
    --auto-token         Automatically fetch token from WorkOS (requires credentials)
    --verbose            Show detailed request/response information
"""

import os
import sys
import json
import argparse
import asyncio
import httpx
from pathlib import Path
from typing import Optional

# Load .env file if it exists
env_file = Path(".env")
if env_file.exists():
    try:
        from dotenv import dotenv_values
        env_vars = dotenv_values(".env")
        for k, v in env_vars.items():
            if v and k not in os.environ:
                os.environ[k] = v
    except ImportError:
        pass


async def get_token_auto() -> Optional[str]:
    """Automatically fetch JWT token from WorkOS."""
    try:
        # Import the get_jwt_token function
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir.parent))
        
        from scripts.get_jwt_token import get_jwt_token
        return await get_jwt_token()
    except Exception as e:
        print(f"⚠️  Failed to auto-fetch token: {e}", file=sys.stderr)
        return None


async def send_mcp_request(
    url: str,
    token: str,
    method: str,
    params: Optional[dict] = None,
    request_id: int = 1,
    verbose: bool = False
) -> dict:
    """Send MCP JSON-RPC request and return response.
    
    Args:
        url: MCP server URL
        token: Bearer token for authentication
        method: MCP method name (e.g., "initialize", "tools/list")
        params: Optional parameters for the method
        request_id: JSON-RPC request ID
        verbose: If True, print request/response details
        
    Returns:
        Response dictionary
    """
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    
    if params:
        payload["params"] = params
    
    if verbose:
        print(f"\n📤 Request ({method}):", file=sys.stderr)
        print(json.dumps(payload, indent=2), file=sys.stderr)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            
            if verbose:
                print(f"\n📥 Response ({response.status_code}):", file=sys.stderr)
                print(response.text[:500], file=sys.stderr)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error: {e.response.status_code}", file=sys.stderr)
            try:
                error_body = e.response.json()
                print(f"   Error: {json.dumps(error_body, indent=2)}", file=sys.stderr)
            except:
                print(f"   Response: {e.response.text[:200]}", file=sys.stderr)
            return {"error": {"code": e.response.status_code, "message": str(e)}}
        except httpx.RequestError as e:
            print(f"❌ Request error: {e}", file=sys.stderr)
            return {"error": {"message": str(e)}}
        except Exception as e:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            return {"error": {"message": str(e)}}


async def test_mcp_connection(
    url: str,
    token: str,
    verbose: bool = False
) -> bool:
    """Test MCP connection by initializing and listing tools.
    
    Args:
        url: MCP server URL
        token: Bearer token for authentication
        verbose: If True, show detailed information
        
    Returns:
        True if both operations succeed, False otherwise
    """
    print(f"🔗 Testing MCP connection: {url}", file=sys.stderr)
    print(f"🔑 Using token: {token[:20]}...", file=sys.stderr)
    
    # Step 1: Initialize
    print(f"\n1️⃣  Initializing connection...", file=sys.stderr)
    init_response = await send_mcp_request(
        url=url,
        token=token,
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-mcp-connection",
                "version": "1.0.0"
            }
        },
        request_id=1,
        verbose=verbose
    )
    
    if "error" in init_response:
        print(f"❌ Initialize failed: {init_response['error']}", file=sys.stderr)
        return False
    
    if "result" in init_response:
        print(f"✅ Initialize successful", file=sys.stderr)
        if verbose:
            print(f"   Result: {json.dumps(init_response['result'], indent=2)}", file=sys.stderr)
    else:
        print(f"⚠️  Initialize response missing 'result' field", file=sys.stderr)
        if verbose:
            print(f"   Response: {json.dumps(init_response, indent=2)}", file=sys.stderr)
    
    # Step 2: List tools
    print(f"\n2️⃣  Listing tools...", file=sys.stderr)
    tools_response = await send_mcp_request(
        url=url,
        token=token,
        method="tools/list",
        request_id=2,
        verbose=verbose
    )
    
    if "error" in tools_response:
        print(f"❌ List tools failed: {tools_response['error']}", file=sys.stderr)
        return False
    
    if "result" in tools_response:
        tools = tools_response["result"].get("tools", [])
        print(f"✅ Found {len(tools)} tools:", file=sys.stderr)
        for tool in tools:
            tool_name = tool.get("name", "unknown")
            tool_desc = tool.get("description", "")[:60]
            print(f"   - {tool_name}: {tool_desc}...", file=sys.stderr)
        
        # Output tools list as JSON to stdout for scripting
        print(json.dumps({"tools": tools}, indent=2))
        return True
    else:
        print(f"⚠️  Tools list response missing 'result' field", file=sys.stderr)
        if verbose:
            print(f"   Response: {json.dumps(tools_response, indent=2)}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test MCP server connection (initialize + list tools)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Bearer token for authentication (or set ATOMS_TEST_AUTH_TOKEN)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=os.getenv("MCP_BASE_URL", "http://localhost:8000/api/mcp"),
        help="MCP server URL"
    )
    parser.add_argument(
        "--auto-token",
        action="store_true",
        help="Automatically fetch token from WorkOS (requires WORKOS_API_KEY, WORKOS_CLIENT_ID)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed request/response information"
    )
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.getenv("ATOMS_TEST_AUTH_TOKEN")
    
    if args.auto_token and not token:
        print("🔄 Auto-fetching token from WorkOS...", file=sys.stderr)
        token = asyncio.run(get_token_auto())
        if not token:
            print("❌ Failed to auto-fetch token", file=sys.stderr)
            sys.exit(1)
    
    if not token:
        print("❌ No token provided. Use --token, set ATOMS_TEST_AUTH_TOKEN, or use --auto-token", file=sys.stderr)
        sys.exit(1)
    
    # Test connection
    success = asyncio.run(test_mcp_connection(
        url=args.url,
        token=token,
        verbose=args.verbose
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
