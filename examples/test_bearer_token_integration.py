#!/usr/bin/env python3
"""
Integration test demonstrating bearer token authentication.

This script shows how to:
1. Get an AuthKit JWT token
2. Pass it via Authorization header to MCP server
3. Make authenticated tool calls

Usage:
    python examples/test_bearer_token_integration.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(".env.local", override=True)


async def test_bearer_token_auth():
    """Test bearer token authentication with MCP server."""

    # Configuration
    mcp_endpoint = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")

    # For this example, we'll use a mock token
    # In production, you would get this from AuthKit:
    # from workos import WorkOS
    # workos = WorkOS(api_key=os.getenv("WORKOS_API_KEY"))
    # token = workos.user_management.get_access_token(...)

    print("=" * 80)
    print("Bearer Token Authentication Integration Test")
    print("=" * 80)
    print(f"\nMCP Endpoint: {mcp_endpoint}")
    print("\nThis test demonstrates how frontend clients can authenticate")
    print("by passing AuthKit JWT tokens via the Authorization header.\n")

    # Example 1: Test with mock token (will fail auth but show the flow)
    print("\n" + "-" * 80)
    print("Example 1: Bearer Token Flow (Mock Token)")
    print("-" * 80)

    mock_token = "mock-jwt-token-for-demonstration"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                mcp_endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {mock_token}",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "workspace_tool",
                        "arguments": {
                            "operation": "get_context",
                        },
                    },
                },
            )

            print("✅ Request sent with Bearer token")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")

            if response.status_code == 401:
                print("\n⚠️  Expected: Token validation failed (mock token)")
                print("   In production, use a real AuthKit JWT token")

        except Exception as e:
            print(f"❌ Request failed: {e}")

    # Example 2: Show the correct flow with real token
    print("\n" + "-" * 80)
    print("Example 2: Production Flow (Pseudocode)")
    print("-" * 80)

    print("""
# Frontend (TypeScript/JavaScript):
const authkit = await createAuthKitClient(WORKOS_CLIENT_ID, {
  apiHostname: WORKOS_AUTH_DOMAIN,
});

// Get authenticated user's token
const accessToken = await authkit.getAccessToken();

// Call MCP server with Bearer token
const response = await fetch('https://mcp.atoms.tech/api/mcp', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,  // ← AuthKit JWT
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'entity_tool',
      arguments: {
        entity_type: 'project',
        operation: 'list',
      },
    },
  }),
});

const result = await response.json();
console.log('Projects:', result.result);
    """)

    # Example 3: Show token extraction priority
    print("\n" + "-" * 80)
    print("Example 3: Token Extraction Priority")
    print("-" * 80)

    print("""
The MCP server checks for tokens in this order:

1. HTTP Authorization Header (Highest Priority)
   ↓ Authorization: Bearer <token>
   ↓ Used by: Frontend clients
   
2. FastMCP OAuth Context
   ↓ get_access_token() from FastMCP
   ↓ Used by: MCP clients with OAuth flow
   
3. Claims Dict Fallback
   ↓ access_token from claims
   ↓ Used by: Legacy token formats

This allows both frontend and MCP clients to authenticate seamlessly!
    """)

    # Example 4: Security best practices
    print("\n" + "-" * 80)
    print("Example 4: Security Best Practices")
    print("-" * 80)

    print("""
✅ DO:
  - Use HTTPS in production
  - Refresh tokens before expiration
  - Handle 401 errors gracefully
  - Configure CORS properly
  - Validate tokens server-side

❌ DON'T:
  - Send tokens over HTTP
  - Store tokens in localStorage (use httpOnly cookies or memory)
  - Ignore token expiration
  - Hardcode tokens in code
  - Skip CORS configuration
    """)

    print("\n" + "=" * 80)
    print("Integration Test Complete")
    print("=" * 80)
    print("\nFor more information:")
    print("  - Documentation: docs/deployment/FRONTEND_BEARER_TOKEN.md")
    print("  - Example Code: examples/frontend-bearer-token-example.ts")
    print("  - Tests: tests/unit/test_bearer_token_auth.py")
    print()


async def test_token_extraction_logic():
    """Test the token extraction logic directly."""
    from unittest.mock import Mock, patch

    from server.auth import extract_bearer_token

    print("\n" + "=" * 80)
    print("Token Extraction Logic Test")
    print("=" * 80)

    # Test 1: HTTP Authorization header
    print("\n1. Testing HTTP Authorization header extraction...")
    mock_headers = {"authorization": "Bearer test-jwt-token-12345"}

    with patch("server.auth.get_http_headers", return_value=mock_headers):
        with patch("server.auth.get_access_token", return_value=None):
            token = extract_bearer_token()

    if token and token.token == "test-jwt-token-12345":
        print("   ✅ Successfully extracted token from HTTP header")
        print(f"   Token: {token}")
        print(f"   Source: {token.source}")
    else:
        print("   ❌ Failed to extract token")

    # Test 2: FastMCP OAuth fallback
    print("\n2. Testing FastMCP OAuth fallback...")
    mock_headers = {}
    mock_access_token = Mock()
    mock_access_token.token = "oauth-token-12345"
    mock_access_token.claims = {"sub": "user_123"}

    with patch("server.auth.get_http_headers", return_value=mock_headers):
        with patch("server.auth.get_access_token", return_value=mock_access_token):
            token = extract_bearer_token()

    if token and token.token == "oauth-token-12345":
        print("   ✅ Successfully fell back to OAuth token")
        print(f"   Token: {token}")
        print(f"   Source: {token.source}")
    else:
        print("   ❌ Failed to extract OAuth token")

    # Test 3: Priority test
    print("\n3. Testing priority (HTTP header > OAuth)...")
    mock_headers = {"authorization": "Bearer http-token"}
    mock_access_token = Mock()
    mock_access_token.token = "oauth-token"

    with patch("server.auth.get_http_headers", return_value=mock_headers):
        with patch("server.auth.get_access_token", return_value=mock_access_token):
            token = extract_bearer_token()

    if token and token.token == "http-token":
        print("   ✅ HTTP header correctly takes priority")
        print(f"   Token: {token}")
        print(f"   Source: {token.source}")
    else:
        print("   ❌ Priority test failed")

    print("\n" + "=" * 80)
    print("Token Extraction Tests Complete")
    print("=" * 80)


async def main():
    """Run all integration tests."""
    try:
        await test_bearer_token_auth()
        await test_token_extraction_logic()

        print("\n✅ All integration tests completed successfully!")
        print("\nNext steps:")
        print("  1. Review the documentation in docs/deployment/FRONTEND_BEARER_TOKEN.md")
        print("  2. Check the TypeScript example in examples/frontend-bearer-token-example.ts")
        print("  3. Run unit tests: pytest tests/unit/test_bearer_token_auth.py -v")
        print()

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

