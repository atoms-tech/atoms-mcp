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
async def mcp_client_http(test_server):
    """Provide HTTP MCP client for integration tests.
    
    Usage:
        @pytest.mark.integration
        async def test_entity_creation(mcp_client_http):
            result = await mcp_client_http.call_tool(
                "entity_tool",
                {"operation": "create", "entity_type": "organization", ...}
            )
            assert result.success
    
    Benefits:
        - Tests real HTTP transport
        - Uses live database
        - Validates authentication and middleware
        - Real-world performance characteristics
    """
    import os
    
    # Use deployed mcpdev target if available, otherwise fall back to local
    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")
    
    # If explicitly set to use mcpdev, use it directly (no need for local test_server)
    if "mcpdev.atoms.tech" in base_url:
        server_url = base_url
    else:
        server_url = base_url

    # Create client with proper configuration
    async with Client(server_url, timeout=10.0) as client:
        yield client


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
async def integration_auth_token(live_supabase):
    """Get authenticated token for integration tests."""
    try:
        auth_response = live_supabase.auth.sign_in_with_password({
            "email": "kooshapari@kooshapari.com",
            "password": "118118"
        })

        if auth_response.session:
            return auth_response.session.access_token
        else:
            pytest.skip("Could not authenticate with Supabase")
    except Exception as e:
        pytest.skip(f"Authentication failed: {e}")


@pytest_asyncio.fixture
async def integration_client():
    """Integration client wrapper for backward compatibility."""
    import os
    
    # Use deployed mcpdev target if available
    base_url = os.getenv("MCP_INTEGRATION_BASE_URL", "http://127.0.0.1:8000/api/mcp")
    
    async with Client(base_url, timeout=10.0) as client:
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
