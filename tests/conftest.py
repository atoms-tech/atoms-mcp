"""Pytest configuration and shared fixtures with pheno-sdk integration."""

# Enable MCP Auth Plugin for automatic authentication
# NOTE: Plugin is auto-loaded by pytest.ini (mcp_auth_enable = true)
# pytest_plugins = ["mcp_qa.pytest_plugins.auth_plugin"]

# Load Phase 2 test infrastructure plugins
# These plugins provide test mode support, cascade flow ordering, and conditional fixtures
pytest_plugins = ["tests.framework.pytest_atoms_modes"]

import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env files
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
load_dotenv(".env.local", override=True)

# Import endpoint configuration from centralized mcp_qa library
from mcp_qa.config.endpoints import EndpointRegistry, Environment, MCPProject  # noqa: E402

# Import pheno-sdk kits for testing (optional)
try:
    from event_kit import Event, EventBus
    HAS_EVENT_KIT = True
except ImportError:
    HAS_EVENT_KIT = False
    EventBus = None
    Event = None

# Import workflow_kit - now properly installed from pheno-sdk
try:
    from workflow_kit import Workflow, WorkflowEngine, WorkflowStep
    from workflow_kit.task import Worker, task
    HAS_WORKFLOW_KIT = True
except ImportError:
    HAS_WORKFLOW_KIT = False
    WorkflowEngine = None
    Workflow = None
    WorkflowStep = None
    Worker = None
    task = None

# Import TDD fixtures to make them available
try:
    from .fixtures.auth import *  # noqa: F403
    from .fixtures.data import *  # noqa: F403
    from .fixtures.providers import *  # noqa: F403
    from .fixtures.tools import *  # noqa: F403
except ImportError:
    # TDD fixtures not available - continue with existing functionality
    pass


def pytest_configure(config):
    """Register custom markers."""
    # Existing markers
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require server running)"
    )
    config.addinivalue_line(
        "markers", "http: marks tests that call MCP via HTTP"
    )

    # New TDD markers
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (full workflows)"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests that require OAuth authentication"
    )
    config.addinivalue_line(
        "markers", "tool: marks tests for specific MCP tools"
    )
    config.addinivalue_line(
        "markers", "provider: marks tests for specific OAuth providers"
    )
    config.addinivalue_line(
        "markers", "parallel: marks tests that can run in parallel"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that take longer than 5 seconds"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Provide session-scoped event loop for async tests.

    Note: This creates a new event loop for the entire test session.
    The loop is closed after all tests complete.
    """
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    # Close the loop after all tests complete
    # Use try-except to handle cases where loop is already closed
    try:
        if not loop.is_closed():
            loop.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def check_server_running():
    """Check if MCP server is running on localhost:8000."""
    import httpx

    try:
        response = httpx.get("http://127.0.0.1:8000/health", timeout=2.0)
        if response.status_code == 200:
            return True
    except Exception:
        pass

    pytest.skip("MCP server not running on http://127.0.0.1:8000")


# Supabase JWT fixture removed - using AuthKit OAuth only


@pytest.fixture(scope="session")
def event_bus():
    """Provide event-kit event bus for test events."""
    if not HAS_EVENT_KIT:
        pytest.skip("event_kit not installed")
    return EventBus()


@pytest.fixture(scope="session")
def workflow_engine():
    """Provide workflow-kit engine for test workflows."""
    if not HAS_WORKFLOW_KIT:
        pytest.skip("workflow_kit not installed")
    return WorkflowEngine()


@pytest.fixture
async def test_event_tracker(event_bus):
    """Track events during tests using event-kit."""
    events_captured = []

    async def capture_event(event):
        events_captured.append(event)

    # Subscribe to all test events
    event_bus.subscribe("test.*", capture_event)

    yield events_captured

    # Cleanup
    event_bus.unsubscribe("test.*", capture_event)


@pytest.fixture
def workflow_builder():
    """Helper to build test workflows using workflow-kit."""
    if not HAS_WORKFLOW_KIT:
        pytest.skip("workflow_kit not installed")

    def build(name: str, steps: list):
        workflow_steps = [
            WorkflowStep(name=step["name"], handler=step["handler"])
            for step in steps
        ]
        return Workflow(name=name, steps=workflow_steps)
    return build


# ============================================================================
# IMPORT AUTH FIXTURES
# ============================================================================
# Import fixtures from fixtures/auth.py so they're available to all tests
from tests.fixtures.auth import authenticated_client  # noqa: F401, E402

# ============================================================================
# MCP TEST FRAMEWORK INTEGRATION
# ============================================================================

@pytest.fixture(scope="session")
def local_server_config():
    """Get local server configuration if available.

    Checks if local MCP server is running on port 50002 (new atoms port).
    Returns config dict with port, url, etc. if local server enabled.

    Environment Variable:
        ATOMS_USE_LOCAL_SERVER=true  # Enable local server for tests (set by --local flag)
    """
    use_local = os.getenv("ATOMS_USE_LOCAL_SERVER", "").lower() in ("true", "1", "yes", "on")

    if not use_local:
        return None

    try:
        import httpx
        # Check if server is running on port 50002 (new atoms port)
        try:
            response = httpx.get("http://localhost:50002/health", timeout=2.0)
            if response.status_code == 200:
                return {
                    "port": 50002,
                    "url": "http://localhost:50002",
                    "mcp_endpoint": "http://localhost:50002/api/mcp",
                }
        except Exception:
            pass

        # Fallback: try to get config from SmartInfraManager
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from kinfra import get_smart_infra_manager

            infra = get_smart_infra_manager(project_name="atoms_mcp", domain="atomcp.kooshapari.com")
            config = infra.get_project_config()

            # Check if server is actually running
            if config.get("server_running"):
                port = config.get("assigned_port", 50002)
                is_healthy, reason = infra.check_mcp_server_health(port)

                if is_healthy:
                    return {
                        "port": port,
                        "url": f"http://localhost:{port}",
                        "mcp_endpoint": f"http://localhost:{port}/api/mcp",
                        "tunnel_url": config.get("tunnel_url"),
                    }
                print(f"Warning: Local server not healthy: {reason}")
            else:
                print("Warning: Local server not running. Start with: python start_server.py")
        except Exception as e:
            print(f"Warning: Failed to get local server config: {e}")

    except Exception as e:
        print(f"Warning: Failed to check local server: {e}")

    return None


@pytest_asyncio.fixture(scope="session")
async def mcp_client(request, local_server_config):
    """Provide authenticated MCP client using credentials from auth plugin.

    The auth plugin handles OAuth automatically before test collection.
    This fixture just retrieves the cached credentials from the session config.

    Automatically uses local server if available (ATOMS_USE_LOCAL_SERVER=true),
    otherwise falls back to production server at mcp.atoms.tech.
    """
    from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker

    # Use local server if available, otherwise production
    if local_server_config:
        mcp_endpoint = local_server_config["mcp_endpoint"]
        print(f"Using local MCP server: {mcp_endpoint}")
    else:
        # Get endpoint from environment (set by test_main.py or default to prod)
        mcp_endpoint = os.getenv("MCP_ENDPOINT")
        if not mcp_endpoint:
            mcp_endpoint = EndpointRegistry.get_endpoint(project=MCPProject.ATOMS, environment=Environment.PRODUCTION)
        print(f"Using MCP server: {mcp_endpoint}")

    # Get cached credentials from auth plugin (if available)
    credentials = None
    if hasattr(request.session.config, "_mcp_credentials"):
        credentials = request.session.config._mcp_credentials
        # Validate credentials before use - avoid expired tokens
        if credentials and hasattr(credentials, 'is_valid'):
            if not credentials.is_valid():
                print("⚠️  Cached credentials expired, will re-authenticate")
                credentials = None  # Force fresh authentication
            else:
                print("Using cached credentials from auth plugin")
        else:
            print("Using cached credentials from auth plugin")

    provider = os.getenv("ATOMS_OAUTH_PROVIDER", "authkit")

    broker = UnifiedCredentialBroker(
        mcp_endpoint=mcp_endpoint,
        provider=provider,
        cached_credentials=credentials  # Use plugin's cached credentials
    )

    try:
        client, credentials = await broker.get_authenticated_client()
        yield client
    finally:
        await broker.close()


# ============================================================================
# FAST HTTP CLIENT - Session-Scoped for Performance
# ============================================================================

@pytest_asyncio.fixture(scope="session")
async def fast_http_client(request, local_server_config):
    """Provide session-scoped authenticated HTTP client for fast testing.

    This fixture:
    - Uses credentials from the auth plugin (no manual OAuth)
    - Provides direct HTTP access to MCP tools (no MCP client overhead)
    - Supports parallel test execution
    - Returns AuthenticatedHTTPClient with session token
    - Automatically uses local server if available (ATOMS_USE_LOCAL_SERVER=true)

    Usage:
        @pytest.mark.integration
        async def test_entity_creation(fast_http_client):
            result = await fast_http_client.call_tool("create_entity", {
                "name": "Test Entity",
                "type": "document"
            })
            assert result["success"]

    The session token is automatically included in all tool calls via the
    AuthenticatedHTTPClient wrapper, so tests don't need to manually pass it.
    """
    from .fixtures.auth import authenticated_client as get_auth_client

    # Get cached credentials from auth plugin (if available)
    if hasattr(request.session.config, "_mcp_credentials"):
        _credentials = request.session.config._mcp_credentials
        print("Fast HTTP client using cached credentials from auth plugin")

    # Override MCP endpoint if using local server
    if local_server_config:
        original_endpoint = os.getenv("MCP_ENDPOINT")
        os.environ["MCP_ENDPOINT"] = local_server_config["mcp_endpoint"]
        print(f"Fast HTTP client using local server: {local_server_config['mcp_endpoint']}")

    try:
        # Get session-scoped authenticated client
        # The auth plugin has already handled OAuth, so this reuses cached credentials
        async for client in get_auth_client():
            # Verify client is working before yielding to tests
            health_ok = await client.health_check()
            if not health_ok:
                pytest.skip("MCP server health check failed - is the server running?")

            yield client

            # Cleanup handled by client context manager
    finally:
        # Restore original endpoint
        if local_server_config and original_endpoint:
            os.environ["MCP_ENDPOINT"] = original_endpoint
        elif local_server_config:
            os.environ.pop("MCP_ENDPOINT", None)


@pytest_asyncio.fixture
async def client_adapter(mcp_client):
    """Provide AtomsMCPClientAdapter for test framework."""
    from tests.framework import AtomsMCPClientAdapter
    return AtomsMCPClientAdapter(mcp_client, verbose_on_fail=True)


@pytest.fixture(scope="session")
def test_cache():
    """Provide test cache instance."""
    from tests.framework import TestCache
    return TestCache()


def pytest_collection_modifyitems(session, config, items):
    """Convert @mcp_test decorated functions to pytest tests."""
    from tests.framework.decorators import get_test_registry

    registry = get_test_registry()
    registered_tests = registry.get_tests()

    # Add pytest markers to registered tests
    for item in items:
        test_name = item.name

        # Check if this test is registered in our framework
        if test_name in registered_tests:
            test_info = registered_tests[test_name]

            # Add category marker
            _category = test_info.get("category", "functional")  # noqa: F841
            item.add_marker(pytest.mark.tool)

            # Add priority as metadata
            priority = test_info.get("priority", 5)
            item.user_properties.append(("priority", priority))

            # Add auth marker if needed
            if test_info.get("requires_auth", False):
                item.add_marker(pytest.mark.auth)

            # Mark as parallel-safe by default (MCP HTTP calls are isolated)
            item.add_marker(pytest.mark.parallel)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for custom reporters."""
    outcome = yield
    report = outcome.get_result()

    # Store result for custom reporters
    if report.when == "call":
        test_name = item.name
        result = {
            "name": test_name,
            "passed": report.outcome == "passed",
            "failed": report.outcome == "failed",
            "skipped": report.outcome == "skipped",
            "duration": report.duration,
            "error": str(report.longrepr) if report.failed else None,
        }

        # Store in session for aggregation
        if not hasattr(item.session, "test_results"):
            item.session.test_results = []
        item.session.test_results.append(result)


# ============================================================================
# ATOMS PYTEST PLUGIN SESSION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def atoms_test_cache():
    """Provide test cache for session."""
    from tests.framework import TestCache
    return TestCache()


@pytest.fixture(scope="session")
def atoms_auth_validation(request):
    """Get auth validation results from auth plugin.

    The auth plugin performs validation automatically before test collection.
    This fixture just retrieves the results from session config.
    """
    if hasattr(request.session.config, "_mcp_auth_valid"):
        is_valid = request.session.config._mcp_auth_valid
        credentials = getattr(request.session.config, "_mcp_credentials", None)

        if is_valid:
            print("Auth validation: PASSED (from plugin)")
            return {"valid": True, "credentials": credentials}
        print("Auth validation: FAILED (from plugin)")
        return {"valid": False, "credentials": None}

    # Fallback: no auth plugin results available
    print("Auth validation: NOT PERFORMED (plugin not active)")
    return None
