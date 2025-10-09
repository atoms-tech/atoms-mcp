"""Pytest configuration and shared fixtures with pheno-sdk integration."""

import os
import sys
import pytest
import pytest_asyncio
import time
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env files
from dotenv import load_dotenv
load_dotenv()
load_dotenv(".env.local", override=True)

# Import pheno-sdk kits for testing (optional)
try:
    from event_kit import EventBus, Event
    HAS_EVENT_KIT = True
except ImportError:
    HAS_EVENT_KIT = False
    EventBus = None
    Event = None

try:
    from workflow_kit import WorkflowEngine, Workflow, WorkflowStep
    HAS_WORKFLOW_KIT = True
except ImportError:
    HAS_WORKFLOW_KIT = False
    WorkflowEngine = None
    Workflow = None
    WorkflowStep = None

# Configure pytest-asyncio mode
pytest_plugins = ["pytest_asyncio"]

# Import TDD fixtures to make them available
try:
    from .fixtures.auth import *
    from .fixtures.tools import *
    from .fixtures.data import *
    from .fixtures.providers import *
except ImportError as e:
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
    """Provide session-scoped event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def check_server_running():
    """Check if MCP server is running on localhost:8000."""
    import httpx

    try:
        response = httpx.get("http://127.0.0.1:8000/health", timeout=2.0)
        if response.status_code == 200:
            return True
    except:
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
# MCP TEST FRAMEWORK INTEGRATION
# ============================================================================

@pytest_asyncio.fixture(scope="session")
async def mcp_client():
    """Provide authenticated MCP client using UnifiedCredentialBroker."""
    from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker
    
    mcp_endpoint = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")
    provider = os.getenv("ATOMS_OAUTH_PROVIDER", "authkit")
    
    broker = UnifiedCredentialBroker(mcp_endpoint=mcp_endpoint, provider=provider)
    
    try:
        client, credentials = await broker.get_authenticated_client()
        yield client
    finally:
        await broker.close()


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
            category = test_info.get("category", "functional")
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
