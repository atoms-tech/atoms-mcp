"""Fixtures for integration tests using HTTP MCP Client.

This conftest provides:
- mcp_client_http: HTTP-based MCP client for integration tests
- live_supabase: Real Supabase client for database interactions
- test_server: Running MCP server instance for HTTP tests
"""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import Dict, Any
import httpx
from fastmcp import Client


@pytest_asyncio.fixture(scope="session")
async def test_server():
    """Start MCP server for integration tests.
    
    Returns:
        Server process that can be used to make HTTP requests
    """
    import subprocess
    import os
    import signal

    # Ensure we're in project root
    original_cwd = os.getcwd()
    try:
        # Change to project directory if needed
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if os.getcwd() != project_root:
            os.chdir(project_root)

        # Start server in background
        env = os.environ.copy()
        env["ATOMS_SERVICE_MODE"] = "integration"  # Use integration mode
        env["ATOMS_TEST_MODE"] = "true"  # Enable unsigned JWT testing

        process = subprocess.Popen(
            ["python", "app.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create process group for cleanup
        )

        # Wait for server to start
        max_wait = 30  # seconds
        start_time = time.time()

        async def check_server():
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get("http://127.0.0.1:8000/health")
                    return response.status_code == 200
            except Exception:
                return False

        # Poll server health endpoint
        while time.time() - start_time < max_wait:
            if await check_server():
                yield process
                return
            await asyncio.sleep(0.5)

        # Server didn't start
        pytest.fail("MCP server failed to start within 30 seconds")

    finally:
        # Cleanup
        try:
            if 'process' in locals():
                # Kill entire process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=10)
        except:
            pass
        os.chdir(original_cwd)


@pytest_asyncio.fixture
async def mcp_client_http(test_server, integration_auth_token):
    """Provide HTTP MCP client for integration tests.

    Usage:
        @pytest.mark.integration
        async def test_entity_creation(mcp_client_http):
            result = await mcp_client_http("entity_tool", {
                "operation": "create",
                "entity_type": "organization",
                "data": {...}
            })
            assert result["success"] is True

    Benefits:
        - Tests real HTTP transport
        - Uses live database
        - Validates authentication and middleware
        - Real-world performance characteristics
    """
    import os
    import httpx
    import uuid
    import logging

    logger = logging.getLogger(__name__)

    # Skip if no auth token available
    if not integration_auth_token:
        logger.warning("⏭️  Skipping integration tests - no authentication token available")
        pytest.skip("No authentication token available for integration tests")

    # Use deployed mcpdev target if available, otherwise fall back to local
    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")

    # Strip trailing slash and construct full URL
    server_url = f"{base_url.rstrip('/')}"

    # Set up authentication headers with token
    headers = {"Content-Type": "application/json"}
    headers["Authorization"] = f"Bearer {integration_auth_token}"
    logger.info(f"🔐 Integration client using token: {integration_auth_token[:50]}...")
    
    async def call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via authenticated HTTP transport."""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(server_url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    return {
                        "success": False, 
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "status_code": response.status_code
                    }
                
                body = response.json()
                
                # Handle JSON-RPC error responses
                if "error" in body:
                    return {
                        "success": False,
                        "error": body["error"].get("message", "Unknown MCP error")
                    }
                
                # Extract tool result from JSON-RPC response
                if "result" in body:
                    tool_result = body["result"]
                    
                    # If tool_result is already structured with success/data/error, return as-is
                    if isinstance(tool_result, dict) and "success" in tool_result:
                        return tool_result
                    
                    # Otherwise, wrap in success structure  
                    return {
                        "success": True,
                        "data": tool_result
                    }
                
                return {
                    "success": False,
                    "error": "Unexpected response format from MCP server"
                }
                
            except httpx.RequestError as e:
                return {
                    "success": False,
                    "error": f"Request failed: {str(e)}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}"
                }
    
    # Return the helper function
    yield call_tool


@pytest_asyncio.fixture
async def live_supabase():
    """Provides real Supabase client for integration tests.
    
    Returns:
        Supabase client authenticated for testing
    """
    from supabase import create_client
    import os

    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured")

    client = create_client(url, key)

    # Verify connection
    try:
        # Test connection with a simple query
        result = client.table("organizations").select("id").limit(1).execute()
        # Success - connection is valid
    except Exception as e:
        pytest.skip(f"Cannot connect to Supabase: {e}")

    yield client


@pytest_asyncio.fixture
async def integration_auth_token():
    """Get authenticated token for integration tests.

    Uses WorkOS User Management API (password grant) to authenticate.
    This is the standard, reliable way to get JWT tokens for testing.
    """
    import os
    import logging

    logger = logging.getLogger(__name__)

    # Use WorkOS User Management (password grant) - always available
    from tests.utils.workos_auth import authenticate_with_workos

    email = os.getenv("ATOMS_TEST_EMAIL", "kooshapari@kooshapari.com")
    password = os.getenv("ATOMS_TEST_PASSWORD", "ASD3on54_Pax90")

    logger.info(f"🔐 Attempting WorkOS authentication for {email}...")
    token = await authenticate_with_workos(email, password)
    if token:
        logger.info(f"✅ Got WorkOS token for {email}")
        return token

    # Fallback: try environment variable
    if os.getenv("ATOMS_TEST_AUTH_TOKEN"):
        logger.info("✅ Using ATOMS_TEST_AUTH_TOKEN from environment")
        return os.getenv("ATOMS_TEST_AUTH_TOKEN")

    # No token available - skip integration tests
    logger.error("❌ No authentication token available for integration tests")
    logger.error("   Set ATOMS_TEST_EMAIL, ATOMS_TEST_PASSWORD, or ATOMS_TEST_AUTH_TOKEN")
    return None


@pytest_asyncio.fixture
async def integration_client():
    """Integration client wrapper for backward compatibility."""
    import os
    
    # Use deployed mcpdev target if available
    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")
    
    async with Client(base_url, timeout=10.0) as client:
        yield client


@pytest_asyncio.fixture
async def mcp_client(mcp_client_http):
    """Canonical client fixture alias for integration suites.

    Legacy tests reference ``mcp_client`` (shared with unit/e2e tiers). To keep
    those tests working without duplicating logic we simply alias the HTTP
    integration client here.
    """

    yield mcp_client_http


@pytest_asyncio.fixture
async def live_mcp_client(integration_auth_token):
    """Provide httpx AsyncClient for live service testing.

    This fixture provides a raw httpx client for making direct HTTP requests
    to the live MCP service. Used by parametrized tests that run against both
    mock and live services.
    """
    import os
    import logging

    logger = logging.getLogger(__name__)

    if not integration_auth_token:
        logger.warning("⏭️  Skipping live service tests - no authentication token available")
        pytest.skip("No authentication token available for live service tests")

    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")

    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {integration_auth_token}"},
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def integration_test_data():
    """Test data specific to integration environment."""
    return {
        "base_url": "http://127.0.0.1:8000/api/mcp",
        "timeout": 10.0,
        "retry_attempts": 3,
        "retry_delay": 1.0,
    }


# Database cleanup utilities

@pytest_asyncio.fixture
async def cleanup_test_data(live_supabase):
    """Clean up test data after integration tests."""
    created_entities = []

    def track_entity(entity_type: str, entity_id: str):
        """Track entities created during test for cleanup."""
        created_entities.append((entity_type, entity_id))
        return entity_id

    yield track_entity

    # Cleanup: delete all tracked entities
    for entity_type, entity_id in created_entities:
        try:
            live_supabase.table(f"mcp_{entity_type}s").delete().eq("id", entity_id).execute()
        except Exception:
            pass  # Best effort cleanup


# Error scenario fixtures

@pytest_asyncio.fixture
async def unreliable_server():
    """Mock server that experiences intermittent failures.
    
    Used to test error handling and retry logic.
    """
    import random

    original_client = None

    async def mock_call_tool_with_failures(tool_name: str, arguments: Dict[str, Any]):
        # 20% chance of failure for resilience testing
        if random.random() < 0.2:
            return {"success": False, "error": "Simulated network failure"}

        # 10% chance of timeout
        if random.random() < 0.1:
            await asyncio.sleep(15)  # Longer than timeout
            return {"success": False, "error": "Timeout"}

        # Otherwise, return success
        return {
            "success": True,
            "data": {"id": "test-id", "name": "test-entity"},
            "operation": "create"
        }

    yield mock_call_tool_with_failures


@pytest.fixture
def rate_limited_client():
    """Mock client that enforces rate limits.
    
    Used to test rate limiting behavior.
    """
    call_count = 0
    start_time = time.time()

    async def mock_call_tool_with_rate_limit(tool_name: str, arguments: Dict[str, Any]):
        nonlocal call_count

        current_time = time.time()
        elapsed = current_time - start_time

        # Reset counter every minute
        if elapsed > 60:
            call_count = 0
            start_time = current_time

        call_count += 1

        # Enforce 100 calls per minute limit
        if call_count > 100:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "status_code": 429
            }

        return {"success": True, "data": {"id": f"rate-limited-{call_count}"}}

    return mock_call_tool_with_rate_limit


# Authentication test fixtures

@pytest_asyncio.fixture
async def expired_token_client():
    """Mock client with expired authentication token."""
    return {
        "success": False,
        "error": "Authentication token has expired",
        "status_code": 401
    }


@pytest_asyncio.fixture
async def unauthorized_client():
    """Mock client with insufficient permissions."""
    return {
        "success": False,
        "error": "Insufficient permissions for this operation",
        "status_code": 403
    }


# Performance test fixtures

@pytest.fixture
def performance_tracker():
    """Track performance metrics during integration tests."""
    metrics = {
        "call_times": [],
        "call_count": 0,
        "errors": [],
        "start_time": None,
        "end_time": None,
    }

    class PerformanceTracker:
        def __init__(self, metrics_dict):
            self.metrics = metrics_dict

        async def track_call(self, func, *args, **kwargs):
            """Track a function call's performance."""
            start = time.time()
            self.metrics["call_count"] += 1

            try:
                result = await func(*args, **kwargs)
                if not result.get("success"):
                    self.metrics["errors"].append(result.get("error", "Unknown error"))
                return result
            except Exception as e:
                self.metrics["errors"].append(str(e))
                raise
            finally:
                elapsed = (time.time() - start) * 1000
                self.metrics["call_times"].append(elapsed)

        def get_report(self):
            """Generate performance report."""
            if not self.metrics["call_times"]:
                return {"error": "No calls tracked"}

            return {
                "total_calls": self.metrics["call_count"],
                "avg_time_ms": sum(self.metrics["call_times"]) / len(self.metrics["call_times"]),
                "min_time_ms": min(self.metrics["call_times"]),
                "max_time_ms": max(self.metrics["call_times"]),
                "error_count": len(self.metrics["errors"]),
                "error_rate": len(self.metrics["errors"]) / self.metrics["call_count"],
            }

    return PerformanceTracker(metrics)


# Test markers and configuration

def pytest_configure(config):
    """Configure integration test markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests that require running server and database"
    )
    config.addinivalue_line(
        "markers", "requires_server: marks tests that need MCP server running"
    )
    config.addinivalue_line(
        "markers", "requires_db: marks tests that need database connection"
    )
    config.addinivalue_line(
        "markers", "slow_integration: marks integration tests that take >1s"
    )
