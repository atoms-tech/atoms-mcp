"""Authentication fixtures for session-scoped OAuth and multi-provider testing."""

import pytest
from typing import AsyncGenerator
from utils.logging_setup import get_logger

from ..framework.auth_session import (
    AuthSessionBroker,
    AuthCredentials,
    AuthenticatedHTTPClient,
    get_auth_broker,
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
async def authenticated_client(request):
    """Session-scoped authenticated FastHTTPClient.

    Uses credentials from auth plugin (if available) or performs OAuth.
    The auth plugin handles OAuth before test collection, so this typically
    just retrieves cached credentials.

    Usage:
        async def test_entity_tool(authenticated_client):
            result = await authenticated_client.call_tool("entity_tool", {
                "entity_type": "organization",
                "operation": "list"
            })
            assert result["success"]
    """
    from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker
    from mcp_qa.adapters.fast_http_client import FastHTTPClient
    import os

    mcp_endpoint = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")

    # Try to get cached credentials from auth plugin
    cached_credentials = None
    if hasattr(request.session.config, '_mcp_credentials'):
        cached_credentials = request.session.config._mcp_credentials
        logger.info("Using cached credentials from auth plugin")

    # Use UnifiedCredentialBroker for OAuth (will use cache if available)
    broker = UnifiedCredentialBroker(
        mcp_endpoint=mcp_endpoint,
        provider="authkit",
        cached_credentials=cached_credentials
    )

    client = None
    try:
        # Get authenticated client (uses cache if plugin provided credentials)
        mcp_client, credentials = await broker.get_authenticated_client()

        # Extract the access token
        access_token = credentials.access_token

        logger.info(f"🔑 Token captured: {len(access_token)} chars, starts with {access_token[:10]}...")

        # Create re-authentication callback to handle token expiration
        async def reauthenticate():
            """Re-authenticate and return fresh access token when current token expires."""
            logger.info("🔄 Re-authenticating due to token expiration...")
            mcp_client, new_creds = await broker.get_authenticated_client()
            logger.info(f"✅ Re-authentication successful - new token valid until {new_creds.expires_at}")
            return new_creds.access_token

        # Create FastHTTPClient with token, DEBUG enabled, and re-auth callback
        client = FastHTTPClient(
            mcp_endpoint=mcp_endpoint,
            access_token=access_token,
            debug=True,  # Enable network-level logging
            reauthenticate_callback=reauthenticate  # Auto re-auth on 401
        )

        yield client

    finally:
        if client:
            await client.close()
        await broker.close()


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