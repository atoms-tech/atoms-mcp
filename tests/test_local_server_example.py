"""
Example tests demonstrating local server usage.

These tests show how to use the local test server for fast, isolated testing.

Setup:
    1. Start local server: python start_server.py
    2. Enable in tests: export ATOMS_USE_LOCAL_SERVER=true
    3. Run tests: pytest tests/test_local_server_example.py -v

The fixtures will automatically use the local server if available,
otherwise fall back to production.
"""

import os

import pytest


@pytest.mark.integration
async def test_health_check_local_server(fast_http_client, local_server_config):
    """Test server health check.

    This test demonstrates:
    - Automatic local server detection
    - Health check endpoint
    - Fixture usage
    """
    # Show which server we're using
    if local_server_config:
        print(f"\nUsing local server: {local_server_config['url']}")
        assert "localhost" in local_server_config["url"]
    else:
        print("\nUsing production server (local server not available)")

    # Health check should work regardless of which server
    health_ok = await fast_http_client.health_check()
    assert health_ok, "Server health check failed"


@pytest.mark.integration
async def test_list_tools_local_server(fast_http_client, local_server_config):
    """Test listing MCP tools.

    This test demonstrates:
    - Tool discovery via MCP protocol
    - Automatic authentication
    - Session-scoped client reuse
    """
    # Call tools/list
    result = await fast_http_client.call_mcp_method("tools/list", {})

    # Should return list of tools
    assert "tools" in result
    assert isinstance(result["tools"], list)
    assert len(result["tools"]) > 0

    # Verify expected tools are present
    tool_names = [tool["name"] for tool in result["tools"]]
    assert "workspace_operation" in tool_names
    assert "entity_operation" in tool_names

    # Show server info
    if local_server_config:
        print(f"\nLocal server provides {len(result['tools'])} tools")
    else:
        print(f"\nProduction server provides {len(result['tools'])} tools")


@pytest.mark.integration
@pytest.mark.skip(reason="Requires actual workspace - for demonstration only")
async def test_workspace_operation_local_server(fast_http_client, local_server_config):
    """Test workspace operation on local server.

    This test demonstrates:
    - Creating entities via local server
    - Fast iteration during development
    - No impact on production data
    """
    # Create test workspace (would actually create if not skipped)
    result = await fast_http_client.call_tool("workspace_operation", {
        "action": "create",
        "name": f"Local Test Workspace {os.getpid()}",
        "description": "Created by local test server"
    })

    # Verify result
    assert result.get("success") is True
    workspace_id = result.get("workspace_id")
    assert workspace_id is not None

    if local_server_config:
        print(f"\nCreated workspace on local server: {workspace_id}")
    else:
        print(f"\nCreated workspace on production: {workspace_id}")


def test_local_server_config_fixture(local_server_config):
    """Test the local_server_config fixture.

    This test demonstrates:
    - How to check if local server is available
    - Config structure
    - Environment variable usage
    """
    use_local = os.getenv("ATOMS_USE_LOCAL_SERVER", "").lower() in ("true", "1", "yes", "on")

    if use_local and local_server_config:
        # Local server is configured and available
        assert "port" in local_server_config
        assert "url" in local_server_config
        assert "mcp_endpoint" in local_server_config
        assert local_server_config["port"] >= 8000
        assert local_server_config["port"] < 9000
        print(f"\nLocal server config: {local_server_config}")
    elif use_local and not local_server_config:
        # Local server requested but not available
        print("\nWarning: ATOMS_USE_LOCAL_SERVER=true but server not running")
        print("Start with: python start_server.py")
    else:
        # Using production server
        assert local_server_config is None
        print("\nUsing production server (set ATOMS_USE_LOCAL_SERVER=true for local)")


@pytest.mark.integration
async def test_server_performance_local_vs_production(fast_http_client, local_server_config):
    """Compare local vs production performance.

    This test demonstrates:
    - Performance benefits of local testing
    - Time measurement
    - Response time comparison
    """
    import time

    # Measure health check response time
    start = time.time()
    health_ok = await fast_http_client.health_check()
    duration = time.time() - start

    assert health_ok, "Server health check failed"

    # Show results
    server_type = "local" if local_server_config else "production"
    print(f"\n{server_type.title()} server health check: {duration*1000:.2f}ms")

    # Local server should typically be faster
    if local_server_config:
        # Local server should respond quickly
        assert duration < 1.0, f"Local server too slow: {duration}s"
        print("Fast local response confirmed")
    else:
        # Production may be slower due to network
        print(f"Production response time: {duration*1000:.2f}ms")


@pytest.mark.unit
def test_smart_infra_manager_import():
    """Test SmartInfraManager can be imported.

    This is a unit test that doesn't require the server to be running.
    """
    from kinfra import SmartInfraManager, get_smart_infra_manager

    # Should be able to create manager
    manager = get_smart_infra_manager(project_name="atoms_mcp", domain="atomcp.kooshapari.com")
    assert isinstance(manager, SmartInfraManager)
    assert manager.project_name == "atoms_mcp"
    assert manager.domain == "atomcp.kooshapari.com"
    assert manager.port_range == (50002, 50002)

    # Config directory should exist
    assert manager.config_dir.exists()
    print(f"\nConfig directory: {manager.config_dir}")


@pytest.mark.unit
def test_smart_infra_manager_config():
    """Test SmartInfraManager configuration persistence.

    This is a unit test that doesn't require the server to be running.
    """
    from kinfra import get_smart_infra_manager

    manager = get_smart_infra_manager(project_name="atoms_mcp", domain="atomcp.kooshapari.com")

    # Should be able to get config (even if empty)
    config = manager.get_project_config()
    assert isinstance(config, dict)
    assert config["project_name"] == "atoms_mcp"
    assert config["domain"] == "atomcp.kooshapari.com"

    # Show config
    import json
    print(f"\nCurrent config:\n{json.dumps(config, indent=2)}")

    # If server is running, config should have port info
    if config.get("server_running"):
        assert config.get("assigned_port") is not None
        print(f"\nServer running on port: {config['assigned_port']}")
    else:
        print("\nNo server running (start with: python start_server.py)")
