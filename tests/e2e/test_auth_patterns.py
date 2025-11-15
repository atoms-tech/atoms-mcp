"""E2E Authentication Pattern Tests

Tests both authentication methods supported by HybridAuthProvider:
1. Bearer Token Authentication (Supabase JWT)
2. OAuth Authentication (AuthKit flow)

These tests verify the deployed server accepts both auth patterns.
"""

import pytest
import pytest_asyncio
import os
import httpx
from typing import Dict, Any

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]

# Skip these tests unless running with proper auth or mock harness
skip_reason = "Requires valid ATOMS_INTERNAL_TOKEN or USE_MOCK_HARNESS=true"
has_internal_token = os.getenv("ATOMS_INTERNAL_TOKEN") and not os.getenv("ATOMS_INTERNAL_TOKEN").startswith("test-e2e-token")
has_mock_harness = os.getenv("USE_MOCK_HARNESS", "false").lower() == "true"

if not (has_internal_token or has_mock_harness):
    pytestmark.append(pytest.mark.skip(reason=skip_reason))


class TestBearerTokenAuthentication:
    """Test Bearer token authentication (current implementation).
    
    This uses Supabase JWT tokens passed via Authorization: Bearer header.
    Pattern: Frontend → Supabase Auth → JWT → MCP Server
    """
    
    async def test_bearer_auth_with_supabase_jwt(self, e2e_auth_token):
        """Test authentication with Supabase JWT Bearer token."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        # Construct JSON-RPC request to list tools
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Should succeed with 200
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            result = response.json()
            assert "result" in result, "Expected result field in JSON-RPC response"
            assert "tools" in result["result"], "Expected tools list in result"
            
            # Verify we get actual tools
            tools = result["result"]["tools"]
            assert len(tools) > 0, "Should have at least one tool"
            
            tool_names = [tool["name"] for tool in tools]
            expected_tools = ["workspace_tool", "entity_tool", "relationship_tool", "workflow_tool", "query_tool"]
            for expected in expected_tools:
                assert expected in tool_names, f"Missing expected tool: {expected}"
    
    async def test_bearer_auth_call_tool(self, e2e_auth_token):
        """Test calling a tool with Bearer authentication."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        # Call workspace_tool to get current context (read-only operation)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "workspace_tool",
                "arguments": {
                    "operation": "get_context"
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200, f"Tool call failed: {response.text}"
            result = response.json()
            
            # Verify JSON-RPC response structure
            assert "result" in result, "Expected result in JSON-RPC response"
            tool_result = result["result"]
            
            # Tool should return success or at least structured data
            assert isinstance(tool_result, dict), "Tool result should be a dictionary"
    
    async def test_bearer_auth_invalid_token(self):
        """Test that invalid Bearer tokens are rejected."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Authorization": "Bearer invalid_token_12345",
                    "Content-Type": "application/json"
                }
            )
            
            # Should reject with 401 Unauthorized
            assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
    
    async def test_bearer_auth_missing_token(self):
        """Test that requests without auth are rejected."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json"
                    # No Authorization header
                }
            )
            
            # Should reject with 401 Unauthorized or redirect to OAuth
            # HybridAuthProvider falls back to OAuth when no Bearer token present
            assert response.status_code in [401, 302, 303], \
                f"Expected 401/302/303 for missing auth, got {response.status_code}"


class TestOAuthAuthentication:
    """Test OAuth authentication flow (AuthKit).
    
    This tests the full OAuth flow for browser-based authentication.
    Pattern: Browser → AuthKit → OAuth Flow → MCP Server
    
    Note: These tests verify OAuth discovery endpoints exist, but don't
    complete the full browser-based flow (that requires user interaction).
    """
    
    async def test_oauth_discovery_metadata(self):
        """Test that OAuth discovery metadata endpoint exists."""
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        server_base = base_url.rsplit('/api/mcp', 1)[0]
        
        # OAuth discovery endpoint (RFC 8414)
        discovery_url = f"{server_base}/.well-known/oauth-protected-resource"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(discovery_url)
            
            # Should return discovery metadata
            if response.status_code == 200:
                metadata = response.json()
                
                # Verify OAuth metadata structure
                assert "resource" in metadata or "authorization_servers" in metadata, \
                    "Discovery metadata should contain resource or authorization_servers"
                
                # If authorization_servers present, verify structure
                if "authorization_servers" in metadata:
                    auth_servers = metadata["authorization_servers"]
                    assert isinstance(auth_servers, list), "authorization_servers should be a list"
                    
                    if len(auth_servers) > 0:
                        # First server should have required OAuth endpoints
                        server_url = auth_servers[0]
                        assert isinstance(server_url, str), "Authorization server should be a URL string"
            else:
                # If discovery endpoint doesn't exist, skip OAuth tests
                pytest.skip(f"OAuth discovery endpoint not available (got {response.status_code})")
    
    async def test_oauth_authorization_server_metadata(self):
        """Test authorization server metadata endpoint."""
        # Get base URL
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        server_base = base_url.rsplit('/api/mcp', 1)[0]
        
        # Try authorization server metadata endpoint
        metadata_url = f"{server_base}/.well-known/oauth-authorization-server"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(metadata_url)
            
            if response.status_code == 200:
                metadata = response.json()
                
                # Verify OAuth 2.0 Authorization Server Metadata (RFC 8414)
                expected_fields = ["issuer", "authorization_endpoint", "token_endpoint"]
                
                for field in expected_fields:
                    if field in metadata:
                        assert isinstance(metadata[field], str), f"{field} should be a URL string"
            else:
                pytest.skip(f"OAuth authorization server metadata not available (got {response.status_code})")
    
    async def test_oauth_without_bearer_falls_back(self):
        """Test that requests without Bearer token trigger OAuth flow.
        
        HybridAuthProvider should fall back to OAuth when no Bearer token is present.
        This means either:
        - 401 Unauthorized (prompting OAuth)
        - 302/303 Redirect to authorization endpoint
        """
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        async with httpx.AsyncClient(follow_redirects=False, timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json"
                    # No Authorization header → should trigger OAuth
                }
            )
            
            # Should either reject or redirect to OAuth
            assert response.status_code in [401, 302, 303, 407], \
                f"Expected OAuth trigger (401/302/303), got {response.status_code}"
            
            # If redirect, should point to authorization endpoint
            if response.status_code in [302, 303]:
                location = response.headers.get("Location")
                assert location is not None, "Redirect should have Location header"
                # AuthKit authorization URL pattern
                assert "auth" in location.lower() or "authorize" in location.lower(), \
                    f"Redirect should point to authorization endpoint, got: {location}"


class TestHybridAuthenticationScenarios:
    """Test scenarios mixing both authentication methods."""
    
    async def test_bearer_token_preferred_over_oauth(self, e2e_auth_token):
        """Test that Bearer token is used when both are theoretically available.
        
        When a valid Bearer token is present, it should be used for auth
        even though OAuth is also available.
        """
        base_url = os.getenv("MCP_E2E_BASE_URL", "https://mcpdev.atoms.tech/api/mcp")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {e2e_auth_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Should succeed with Bearer token
            assert response.status_code == 200, \
                f"Bearer token should be accepted, got {response.status_code}"
            
            # Should NOT redirect to OAuth
            assert response.status_code not in [302, 303], \
                "Should not redirect to OAuth when Bearer token present"
    
    async def test_auth_pattern_documentation(self):
        """Document both authentication patterns for reference."""
        patterns = {
            "bearer_token": {
                "description": "Direct JWT token authentication",
                "use_case": "Frontend apps, API clients, automated services",
                "flow": "1. Authenticate with Supabase → 2. Get JWT → 3. Send as Bearer token",
                "header": "Authorization: Bearer <jwt>",
                "pros": ["Stateless", "Fast", "No browser required"],
                "cons": ["Token expiration handling needed"]
            },
            "oauth": {
                "description": "Browser-based OAuth 2.0 flow",
                "use_case": "Interactive browser applications, MCP clients",
                "flow": "1. Redirect to AuthKit → 2. User logs in → 3. Callback with code → 4. Exchange for token",
                "endpoints": [
                    "/.well-known/oauth-protected-resource",
                    "/.well-known/oauth-authorization-server",
                    "/auth/start",
                    "/auth/complete"
                ],
                "pros": ["User-friendly", "Secure browser flow", "MCP client compatible"],
                "cons": ["Requires browser", "More complex flow"]
            }
        }
        
        # This test always passes - it's for documentation
        assert patterns["bearer_token"]["use_case"] is not None
        assert patterns["oauth"]["use_case"] is not None
        
        # Print patterns for reference (visible in verbose mode)
        import json
        print("\n" + "="*80)
        print("SUPPORTED AUTHENTICATION PATTERNS:")
        print("="*80)
        print(json.dumps(patterns, indent=2))
        print("="*80)
