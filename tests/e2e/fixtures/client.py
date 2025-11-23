"""E2E MCP client fixtures for testing against real HTTP endpoints."""

import os
import httpx
import pytest_asyncio
from typing import Optional


@pytest_asyncio.fixture(params=["integration", "e2e"])
async def mcp_client(request, end_to_end_client):
    """Parametrized MCP client for testing across integration/e2e variants.
    
    This fixture runs each test 2 times:
    - integration: HTTP client to localhost:8000 (real local services)
    - e2e: HTTP client to mcpdev.atoms.tech (real deployment)
    
    NOTE: Unit tests should NOT use this fixture. Use dedicated unit test fixtures
    with mocks instead. This fixture is ONLY for integration and e2e tests that
    require actual HTTP connections to a running server.
    
    Each test receives the appropriate client variant automatically.
    """
    # Both variants use the real HTTP client
    # The difference is determined by environment variables (MCP_E2E_BASE_URL)
    return end_to_end_client


@pytest_asyncio.fixture
async def end_to_end_client(e2e_auth_token):
    """E2E-ready MCP client with full authentication.
    
    This client connects to the deployed mcpdev.atoms.tech instance with:
    - Real authentication via Bearer token
    - Production configuration
    - Full middleware stack
    - Actual database connectivity
    - Automatic token refresh on 401 errors
    
    The client's call_tool method makes real HTTP calls.
    
    Usage:
        @pytest.mark.e2e
        async def test_complete_workflow(end_to_end_client):
            result = await end_to_end_client.call_tool(...)
            assert result.success
    """
    # Get deployment URL from environment variable set by TestEnvManager (atoms CLI)
    # This respects the --env flag from atoms CLI:
    # - atoms test:e2e --env local → http://localhost:8000/api/mcp (real JWT, same WorkOS keys)
    # - atoms test:e2e --env dev → https://mcpdev.atoms.tech/api/mcp (real JWT, prod WorkOS keys)
    # - atoms test:e2e --env prod → https://mcp.atoms.tech/api/mcp (real JWT, prod WorkOS keys)
    deployment_url = os.getenv("MCP_E2E_BASE_URL")
    if not deployment_url:
        # Fallback to dev if not set by TestEnvManager
        deployment_url = "https://mcpdev.atoms.tech/api/mcp"
        print("⚠️  MCP_E2E_BASE_URL not set, using dev: mcpdev.atoms.tech")

    # Disable test mode for all environments - use real WorkOS authentication
    # Local server uses the same WorkOS keys as prod (from .env)
    if "ATOMS_TEST_MODE" in os.environ:
        del os.environ["ATOMS_TEST_MODE"]

    # Determine environment name for logging
    if "localhost" in deployment_url or "127.0.0.1" in deployment_url:
        env_name = "Local (localhost:8000)"
    elif "mcpdev" in deployment_url:
        env_name = "Development (mcpdev.atoms.tech)"
    elif "mcp.atoms.tech" in deployment_url:
        env_name = "Production (mcp.atoms.tech)"
    else:
        env_name = deployment_url

    print(f"✅ Target environment: {env_name}")
    print("   Using real WorkOS authentication (fresh token per test)")

    # Create httpx client with authentication headers
    headers = {
        "Authorization": f"Bearer {e2e_auth_token}",
        "Content-Type": "application/json",
    }

    # Create httpx AsyncClient with auth headers (keep alive for test duration)
    http_client = httpx.AsyncClient(
        base_url=deployment_url.rsplit('/api/mcp', 1)[0] if '/api/mcp' in deployment_url else deployment_url,
        headers=headers,
        timeout=30.0
    )

    try:
        # Create MCP client wrapper that uses authenticated httpx client
        from tests.e2e.mcp_http_wrapper import AuthenticatedMcpClient

        mcp_client = AuthenticatedMcpClient(
            base_url=deployment_url,
            http_client=http_client,
            auth_token=e2e_auth_token
        )

        yield mcp_client
    finally:
        # Close the httpx client after test completes
        await http_client.aclose()
