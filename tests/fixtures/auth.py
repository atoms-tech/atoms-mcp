"""Authentication fixtures for session-scoped OAuth and multi-provider testing."""

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from utils.logging_setup import get_logger

from ..framework.auth_session import (
    AuthSessionBroker,
    AuthCredentials,
    AuthenticatedHTTPClient,
    get_auth_broker,
    get_authenticated_client,
)

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def auth_session_broker() -> AuthSessionBroker:
    """Session-scoped auth broker - shared across all tests."""
    return get_auth_broker()


@pytest.fixture(scope="session")
async def authenticated_credentials(auth_session_broker: AuthSessionBroker) -> AuthCredentials:
    """Session-scoped auth credentials.
    
    This performs OAuth ONCE per test session and provides credentials to all tests.
    """
    logger.info("🔐 Acquiring session-scoped authentication credentials...")
    credentials = await auth_session_broker.get_authenticated_credentials(provider="authkit")
    logger.info(f"✅ Authentication successful - credentials valid until {credentials.expires_at}")
    return credentials


@pytest.fixture(scope="session")
async def authenticated_client(authenticated_credentials: AuthCredentials) -> AsyncGenerator[AuthenticatedHTTPClient, None]:
    """Session-scoped authenticated HTTP client.
    
    This is the main fixture for direct HTTP tool calls - no MCP client overhead.
    
    Usage:
        async def test_workspace_tool(authenticated_client):
            result = await authenticated_client.call_tool("workspace_operation", {
                "session_token": "auto-provided",
                "operation": "list_projects",
                "params": {}
            })
            assert result["success"]
    """
    client = AuthenticatedHTTPClient(authenticated_credentials)
    
    # Verify client is working
    health_ok = await client.health_check()
    if not health_ok:
        pytest.skip("MCP server health check failed")
    
    yield client
    
    # Cleanup handled by client context manager


@pytest.fixture(scope="session") 
async def github_client(auth_session_broker: AuthSessionBroker) -> AsyncGenerator[AuthenticatedHTTPClient, None]:
    """GitHub OAuth client for testing GitHub SSO flows."""
    try:
        credentials = await auth_session_broker.get_authenticated_credentials(provider="github")
        client = AuthenticatedHTTPClient(credentials)
        yield client
    except Exception as e:
        pytest.skip(f"GitHub OAuth not available: {e}")


@pytest.fixture(scope="session")
async def google_client(auth_session_broker: AuthSessionBroker) -> AsyncGenerator[AuthenticatedHTTPClient, None]:  
    """Google OAuth client for testing Google SSO flows."""
    try:
        credentials = await auth_session_broker.get_authenticated_credentials(provider="google")
        client = AuthenticatedHTTPClient(credentials)
        yield client
    except Exception as e:
        pytest.skip(f"Google OAuth not available: {e}")


@pytest.fixture
async def fresh_authenticated_client(auth_session_broker: AuthSessionBroker) -> AsyncGenerator[AuthenticatedHTTPClient, None]:
    """Function-scoped client with fresh credentials.
    
    Use this when you need to test auth refresh or credential expiry.
    """
    credentials = await auth_session_broker.get_authenticated_credentials(
        provider="authkit", 
        force_refresh=True
    )
    client = AuthenticatedHTTPClient(credentials)
    yield client


@pytest.fixture
def mock_auth_credentials() -> AuthCredentials:
    """Mock credentials for unit testing (no real OAuth)."""
    return AuthCredentials(
        access_token="mock_token_for_unit_tests",
        provider="mock",
        base_url="http://localhost:8000"
    )


@pytest.fixture
async def mock_authenticated_client(mock_auth_credentials: AuthCredentials) -> AuthenticatedHTTPClient:
    """Mock authenticated client for unit tests."""
    return AuthenticatedHTTPClient(mock_auth_credentials)


# Parallel testing support
@pytest.fixture(scope="session") 
def worker_auth_credentials(authenticated_credentials: AuthCredentials) -> AuthCredentials:
    """Worker-specific auth credentials for parallel testing.
    
    pytest-xdist creates separate workers - this ensures each worker
    has access to the shared session credentials.
    """
    return authenticated_credentials


@pytest.fixture
async def isolated_client(worker_auth_credentials: AuthCredentials) -> AsyncGenerator[AuthenticatedHTTPClient, None]:
    """Worker-isolated client for parallel test execution."""
    client = AuthenticatedHTTPClient(worker_auth_credentials)
    yield client