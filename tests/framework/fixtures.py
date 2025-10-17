"""Conditional fixtures that adapt based on test mode.

This module provides mode-aware fixture implementations that automatically
switch between real, mocked, and simulated versions based on the active test mode.

Each fixture has:
- hot_impl: Real implementation using actual dependencies
- cold_impl: Mocked implementation using in-memory mocks
- dry_impl: Simulated implementation using full simulation

Usage:
    @pytest.fixture
    async def http_client(atoms_mode_config):
        async with ConditionalFixture.create_async(
            atoms_mode_config,
            hot_impl=create_real_client,
            cold_impl=create_mock_client,
            dry_impl=create_simulated_client,
        ) as client:
            yield client
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from .test_modes import ConditionalFixture, TestMode, TestModeConfig

logger = logging.getLogger(__name__)


# ============================================================================
# Implementation Functions
# ============================================================================


async def create_real_mcp_client(endpoint: str) -> Any:
    """Create real MCP client for HOT mode."""
    from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker

    broker = UnifiedCredentialBroker(mcp_endpoint=endpoint, provider="authkit")
    client, _ = await broker.get_authenticated_client()
    return client


async def create_mock_mcp_client() -> Any:
    """Create mocked MCP client for COLD mode."""
    mock_client = AsyncMock()

    # Mock successful tool calls
    async def mock_call_tool(tool_name: str, arguments: dict) -> dict:
        return {
            "success": True,
            "result": {"id": f"{tool_name}_result_123", "data": arguments},
        }

    mock_client.call_tool = mock_call_tool
    mock_client.list_tools = AsyncMock(
        return_value={
            "result": {
                "tools": [
                    {"name": "workspace_tool", "inputSchema": {}},
                    {"name": "entity_tool", "inputSchema": {}},
                ]
            }
        }
    )
    mock_client.health_check = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()

    return mock_client


async def create_simulated_mcp_client() -> Any:
    """Create fully simulated MCP client for DRY mode."""
    # Simulate a complete MCP server
    class SimulatedMCPClient:
        def __init__(self):
            self.entities = {}
            self.call_count = 0

        async def call_tool(self, tool_name: str, arguments: dict) -> dict:
            self.call_count += 1
            operation = arguments.get("operation", "unknown")

            if operation == "create":
                entity_id = f"sim_{tool_name}_{self.call_count}"
                self.entities[entity_id] = arguments
                return {"success": True, "id": entity_id, "data": arguments}

            elif operation == "read":
                entity_id = arguments.get("id")
                if entity_id in self.entities:
                    return {"success": True, "data": self.entities[entity_id]}
                return {"success": False, "error": "not_found"}

            elif operation == "update":
                entity_id = arguments.get("id")
                if entity_id in self.entities:
                    self.entities[entity_id].update(arguments.get("data", {}))
                    return {"success": True, "id": entity_id, "data": self.entities[entity_id]}
                return {"success": False, "error": "not_found"}

            elif operation == "delete":
                entity_id = arguments.get("id")
                if entity_id in self.entities:
                    del self.entities[entity_id]
                    return {"success": True}
                return {"success": False, "error": "not_found"}

            elif operation == "list":
                return {"success": True, "items": list(self.entities.values())}

            else:
                return {"success": True, "result": arguments}

        async def list_tools(self) -> dict:
            return {
                "result": {
                    "tools": [
                        {"name": "workspace_tool", "inputSchema": {}},
                        {"name": "entity_tool", "inputSchema": {}},
                        {"name": "relationship_tool", "inputSchema": {}},
                        {"name": "workflow_tool", "inputSchema": {}},
                        {"name": "query_tool", "inputSchema": {}},
                    ]
                }
            }

        async def health_check(self) -> bool:
            return True

        async def close(self) -> None:
            pass

    return SimulatedMCPClient()


# ============================================================================
# Conditional Fixtures
# ============================================================================


@pytest.fixture(scope="session")
async def conditional_mcp_client(atoms_mode_config: TestModeConfig) -> AsyncIterator[Any]:
    """Mode-aware MCP client fixture.

    HOT: Real authenticated client
    COLD: Mocked client with predictable responses
    DRY: Fully simulated client with in-memory storage
    """

    async def hot_impl():
        import os

        endpoint = os.getenv("MCP_ENDPOINT", "http://localhost:8000/api/mcp")
        return await create_real_mcp_client(endpoint)

    async def cold_impl():
        return await create_mock_mcp_client()

    async def dry_impl():
        return await create_simulated_mcp_client()

    client = await ConditionalFixture.create_async(
        atoms_mode_config, hot_impl=hot_impl, cold_impl=cold_impl, dry_impl=dry_impl
    )

    yield client

    # Cleanup
    if hasattr(client, "close"):
        await client.close()


@pytest.fixture(scope="session")
async def conditional_http_client(atoms_mode_config: TestModeConfig) -> AsyncIterator[Any]:
    """Mode-aware HTTP client fixture.

    HOT: Real HTTP client with authentication
    COLD: Mocked HTTP client
    DRY: Simulated HTTP client
    """

    async def hot_impl():
        from tests.fixtures.auth import authenticated_client

        async for client in authenticated_client():
            return client

    async def cold_impl():
        mock_client = AsyncMock()
        mock_client.call_tool = AsyncMock(return_value={"success": True})
        mock_client.health_check = AsyncMock(return_value=True)
        mock_client.close = AsyncMock()
        return mock_client

    async def dry_impl():
        return await create_simulated_mcp_client()

    client = await ConditionalFixture.create_async(
        atoms_mode_config, hot_impl=hot_impl, cold_impl=cold_impl, dry_impl=dry_impl
    )

    yield client

    # Cleanup
    if hasattr(client, "close"):
        await client.close()


@pytest.fixture
async def conditional_database(atoms_mode_config: TestModeConfig) -> AsyncIterator[Any]:
    """Mode-aware database fixture.

    HOT: Real Supabase connection
    COLD: Mocked in-memory database
    DRY: Simulated in-memory database
    """

    async def hot_impl():
        import os

        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
        return None

    async def cold_impl():
        # Mock Supabase client
        mock_db = MagicMock()
        mock_db.table = MagicMock(
            return_value=MagicMock(
                select=MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=MagicMock(data=[])))),
                insert=MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=MagicMock(data=[{"id": "test_1"}])))),
                update=MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=MagicMock(data=[])))),
                delete=MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=MagicMock(data=[])))),
            )
        )
        return mock_db

    async def dry_impl():
        # Simulate in-memory database
        class SimulatedDatabase:
            def __init__(self):
                self.tables = {}

            def table(self, table_name: str):
                if table_name not in self.tables:
                    self.tables[table_name] = []

                class TableAPI:
                    def __init__(self, data_list):
                        self.data_list = data_list

                    def select(self, *args, **kwargs):
                        class SelectAPI:
                            def __init__(self, data_list):
                                self.data_list = data_list

                            async def execute(self):
                                return type("Result", (), {"data": self.data_list})()

                        return SelectAPI(self.data_list)

                    def insert(self, data):
                        class InsertAPI:
                            async def execute(inner_self):
                                self.data_list.append(data)
                                return type("Result", (), {"data": [data]})()

                        return InsertAPI()

                    def update(self, data):
                        class UpdateAPI:
                            async def execute(inner_self):
                                self.data_list.append(data)
                                return type("Result", (), {"data": [data]})()

                        return UpdateAPI()

                    def delete(self):
                        class DeleteAPI:
                            async def execute(inner_self):
                                self.data_list.clear()
                                return type("Result", (), {"data": []})()

                        return DeleteAPI()

                return TableAPI(self.tables[table_name])

        return SimulatedDatabase()

    db = await ConditionalFixture.create_async(
        atoms_mode_config, hot_impl=hot_impl, cold_impl=cold_impl, dry_impl=dry_impl
    )

    yield db


@pytest.fixture
async def conditional_auth_manager(atoms_mode_config: TestModeConfig) -> AsyncIterator[Any]:
    """Mode-aware authentication manager fixture.

    HOT: Real OAuth authentication
    COLD: Mocked authentication
    DRY: Simulated authentication
    """

    async def hot_impl():
        from mcp_qa.oauth.credential_broker import UnifiedCredentialBroker

        broker = UnifiedCredentialBroker(mcp_endpoint="http://localhost:8000/api/mcp", provider="authkit")
        return broker

    async def cold_impl():
        mock_auth = AsyncMock()
        mock_auth.authenticate = AsyncMock(
            return_value={
                "token": "mock_token_12345",
                "expires_at": 9999999999,
            }
        )
        mock_auth.refresh_token = AsyncMock(return_value={"token": "mock_token_refreshed"})
        mock_auth.logout = AsyncMock()
        return mock_auth

    async def dry_impl():
        class SimulatedAuthManager:
            def __init__(self):
                self.token = "sim_token_12345"
                self.expires_at = 9999999999

            async def authenticate(self, *args, **kwargs):
                return {"token": self.token, "expires_at": self.expires_at}

            async def refresh_token(self, *args, **kwargs):
                return {"token": self.token}

            async def logout(self):
                self.token = None

        return SimulatedAuthManager()

    auth_mgr = await ConditionalFixture.create_async(
        atoms_mode_config, hot_impl=hot_impl, cold_impl=cold_impl, dry_impl=dry_impl
    )

    yield auth_mgr


@pytest.fixture
def conditional_temp_directory(atoms_mode_config: TestModeConfig) -> AsyncIterator[str]:
    """Mode-aware temporary directory fixture.

    HOT/COLD/DRY: All use real temp directories (no difference in modes)
    """
    import tempfile

    def impl():
        with tempfile.TemporaryDirectory() as tmpdir:
            return tmpdir

    tmpdir = ConditionalFixture.create(
        atoms_mode_config, hot_impl=impl, cold_impl=impl, dry_impl=impl
    )

    yield tmpdir


@pytest.fixture(scope="session")
def conditional_event_loop(atoms_mode_config: TestModeConfig) -> AsyncIterator[asyncio.AbstractEventLoop]:
    """Mode-aware event loop fixture.

    HOT/COLD/DRY: All use the same event loop implementation
    """

    def impl():
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    loop = ConditionalFixture.create(
        atoms_mode_config, hot_impl=impl, cold_impl=impl, dry_impl=impl
    )

    yield loop

    if not loop.is_closed():
        loop.close()


__all__ = [
    "conditional_mcp_client",
    "conditional_http_client",
    "conditional_database",
    "conditional_auth_manager",
    "conditional_temp_directory",
    "conditional_event_loop",
    "create_real_mcp_client",
    "create_mock_mcp_client",
    "create_simulated_mcp_client",
]
