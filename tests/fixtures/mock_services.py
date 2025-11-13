"""Common test fixtures that provide mock implementations of services."""

from __future__ import annotations

import pytest

try:
    from infrastructure.mock_adapters import (
        InMemoryDatabaseAdapter, InMemoryAuthAdapter,
        InMemoryStorageAdapter, InMemoryRealtimeAdapter
    )
    from infrastructure.mock_config import ServiceConfig, ServiceMode
    from infrastructure.factory import AdapterFactory
    from infrastructure.mcp_client_adapter import McpClientFactory
except ImportError:
    from test.mock_adapters import (
        InMemoryDatabaseAdapter, InMemoryAuthAdapter,
        InMemoryStorageAdapter, InMemoryRealtimeAdapter
    )
    from test.mock_config import ServiceConfig
    from test.factory import AdapterFactory
    from test.mcp_client_adapter import McpClientFactory


@pytest.fixture(autouse=True)
def force_mock_mode(monkeypatch):
    """Force all services to use mock implementations in tests."""
    # Set all services to mock mode by default in tests
    monkeypatch.setenv("ATOMS_SERVICE_MODE", "mock")
    # Reset global config to pick up env changes
    try:
        from infrastructure.mock_config import reset_service_config
        reset_service_config()
    except ImportError:
        from test.mock_config import reset_service_config
        reset_service_config()


@pytest.fixture
def mock_database():
    """In-memory database adapter with optional seed data."""
    # Empty database by default
    return InMemoryDatabaseAdapter()


@pytest.fixture
def mock_database_with_data():
    """In-memory database seeded with test data."""
    import json
    import os

    # Load from JSON file if available
    mock_data_file = os.path.join(os.path.dirname(__file__), "supabase_mock_data.json")
    if os.path.exists(mock_data_file):
        with open(mock_data_file, "r") as f:
            seed_data = json.load(f)
    else:
        # Fallback data
        seed_data = {
            "workspaces": [
                {"id": "ws-123", "name": "Test Workspace", "owner_user_id": "mock-user-123"},
                {"id": "ws-456", "name": "Second Workspace", "owner_user_id": "mock-user-456"}
            ],
            "entities": [
                {"id": "entity-1", "type": "document", "name": "Test Document", "workspace_id": "ws-123"},
                {"id": "entity-2", "type": "requirement", "name": "Test Requirement", "workspace_id": "ws-123"},
                {"id": "entity-3", "type": "document", "name": "Another Document", "workspace_id": "ws-456"}
            ],
            "relationships": [
                {"id": "rel-1", "source_entity_id": "entity-2", "target_entity_id": "entity-1", "relationship_type": "implements", "workspace_id": "ws-123"}
            ],
            "properties": [
                {"id": "prop-1", "entity_id": "entity-1", "name": "status", "value": "draft", "type": "string", "workspace_id": "ws-123"}
            ]
        }

    return InMemoryDatabaseAdapter(seed_data=seed_data)

    # Fallback data
    seed_data = {
        "workspaces": [
            {"id": "ws-123", "name": "Test Workspace", "owner_user_id": "mock-user-123"},
            {"id": "ws-456", "name": "Second Workspace", "owner_user_id": "mock-user-456"}
        ],
        "entities": [
            {"id": "entity-1", "type": "document", "name": "Test Document", "workspace_id": "ws-123"},
            {"id": "entity-2", "type": "requirement", "name": "Test Requirement", "workspace_id": "ws-123"},
            {"id": "entity-3", "type": "document", "name": "Another Document", "workspace_id": "ws-456"}
        ],
        "relationships": [
            {"id": "rel-1", "source_entity_id": "entity-2", "target_entity_id": "entity-1", "relationship_type": "implements", "workspace_id": "ws-123"}
        ],
        "properties": [
            {"id": "prop-1", "entity_id": "entity-1", "name": "status", "value": "draft", "type": "string", "workspace_id": "ws-123"}
        ]
    }
    return InMemoryDatabaseAdapter(seed_data=seed_data)


@pytest.fixture
def mock_auth():
    """In-memory auth adapter with default mock user."""
    user = {"user_id": "mock-user-123", "username": "mock@example.com"}
    return InMemoryAuthAdapter(default_user=user)


@pytest.fixture
def mock_storage():
    """In-memory storage adapter."""
    return InMemoryStorageAdapter()


@pytest.fixture
def mock_realtime():
    """In-memory realtime adapter."""
    return InMemoryRealtimeAdapter()


@pytest.fixture
def mock_service_config():
    """Mock service config with everything in mock mode."""
    return ServiceConfig()


@pytest.fixture
def mock_mcp_client():
    """In-memory MCP client."""
    factory = McpClientFactory()
    return factory.get()


@pytest.fixture
def mock_adapters(mock_database, mock_auth, mock_storage, mock_realtime):
    """All mock adapters bundled together."""
    return {
        "database": mock_database,
        "auth": mock_auth,
        "storage": mock_storage,
        "realtime": mock_realtime
    }


@pytest.fixture
def mock_adapter_factory(mock_service_config, monkeypatch):
    """Mock adapter factory that uses in-memory adapters."""
    # Override config
    monkeypatch.setattr(mock_service_config, "service_modes", {
        "mcp_client": "mock",
        "supabase": "mock",
        "authkit": "mock",
    })

    # Create factory instance with the mocked config
    factory = AdapterFactory()
    factory._config = mock_service_config
    return factory


@pytest.fixture
def persistent_session_token(mock_auth):
    """Generate a valid session token for use in multiple test steps."""
    token = "mock-session-123"
    # Validate token to populate it in the auth adapter
    import asyncio
    user = asyncio.run(mock_auth.validate_token(token))
    return token
