"""Pytest fixtures for session-wide OAuth brokerage and tool testing."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest

# Import from shared mcp-QA library
from mcp_qa.oauth import UnifiedCredentialBroker

from tests.framework import AtomsMCPClientAdapter


def _build_credential_overrides() -> dict[str, str]:
    overrides: dict[str, str] = {}
    email = os.getenv("ATOMS_TEST_EMAIL") or os.getenv("ZEN_TEST_EMAIL")
    password = os.getenv("ATOMS_TEST_PASSWORD") or os.getenv("ZEN_TEST_PASSWORD")
    username = os.getenv("ATOMS_TEST_USERNAME") or os.getenv("ZEN_TEST_USERNAME")

    if email:
        overrides["email"] = email
        overrides.setdefault("username", email)
    if username:
        overrides["username"] = username
    if password:
        overrides["password"] = password

    return overrides


@pytest.fixture(scope="session")
async def oauth_broker() -> AsyncIterator[UnifiedCredentialBroker]:
    """Provide a session-scoped OAuth broker using mcp-QA."""

    endpoint = os.getenv("ATOMS_MCP_ENDPOINT", os.getenv("ZEN_MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp"))
    provider = os.getenv("ATOMS_OAUTH_PROVIDER", os.getenv("ZEN_OAUTH_PROVIDER", "authkit"))

    broker = UnifiedCredentialBroker(
        mcp_endpoint=endpoint,
        provider=provider
    )

    try:
        yield broker
    finally:
        await broker.close()


@pytest.fixture(scope="session")
async def authenticated_client(oauth_broker: UnifiedCredentialBroker):
    """Return a session-scoped FastMCP client authenticated via OAuth."""

    client, credentials = await oauth_broker.get_authenticated_client()
    return client


@pytest.fixture(scope="session")
async def client_adapter(authenticated_client) -> AsyncIterator[AtomsMCPClientAdapter]:
    """Expose the MCP client through the adapter helpers."""

    adapter = AtomsMCPClientAdapter(authenticated_client, verbose_on_fail=True)
    return adapter


@pytest.fixture(scope="session")
async def oauth_credentials(oauth_broker: UnifiedCredentialBroker):
    """Access OAuth credentials for direct HTTP usage."""

    _, credentials = await oauth_broker.get_authenticated_client()
    return credentials


@pytest.fixture(scope="session")
async def oauth_http_client(oauth_credentials):
    """Yield an ``httpx.AsyncClient`` authenticated with the shared OAuth token."""

    import httpx

    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {oauth_credentials.access_token}"}
    ) as client:
        yield client


@pytest.fixture
def tool_runner(client_adapter: AtomsMCPClientAdapter) -> Callable[[str, dict], Awaitable[dict]]:
    """Utility fixture for invoking MCP tools in tests."""

    async def _run(tool_name: str, arguments: dict) -> dict:
        return await client_adapter.call_tool(tool_name, arguments)

    return _run
