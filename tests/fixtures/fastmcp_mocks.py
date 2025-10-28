"""
FastMCP Server Mocking Fixtures

This module provides fixtures for mocking FastMCP servers in different test modes:
- HOT: Real FastMCP server instances
- COLD: Mocked FastMCP server with predictable responses
- DRY: Fully simulated FastMCP server with in-memory storage

These fixtures follow the FastMCP testing patterns for in-memory testing.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
from fastmcp import Client, FastMCP

from ..framework.test_modes import TestMode, TestModeConfig

logger = logging.getLogger(__name__)


# ============================================================================
# FastMCP Server Implementations
# ============================================================================

def create_real_fastmcp_server() -> FastMCP:
    """Create a real FastMCP server for HOT mode testing."""
    server = FastMCP("atoms-test-server")

    @server.tool
    def entity_tool(entity_type: str, operation: str, id: str | None = None, data: dict | None = None) -> dict[str, Any]:
        """Entity management tool."""
        # This would normally connect to real database
        # For HOT mode, we use real server but with test data
        if operation == "list":
            return {
                "success": True,
                "data": [
                    {"id": f"{entity_type}_1", "name": f"Test {entity_type.title()} 1"},
                    {"id": f"{entity_type}_2", "name": f"Test {entity_type.title()} 2"},
                ],
                "count": 2
            }
        if operation == "create":
            return {
                "success": True,
                "data": {
                    "id": f"{entity_type}_new",
                    **(data or {}),
                    "created_at": datetime.now().isoformat() + "Z"
                }
            }
        if operation == "read":
            return {
                "success": True,
                "data": {"id": id, "name": f"Test {entity_type.title()}"}
            }
        if operation == "update":
            return {
                "success": True,
                "data": {"id": id, **(data or {})}
            }
        if operation == "delete":
            return {"success": True}
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def workspace_tool(operation: str, context_type: str | None = None, entity_id: str | None = None,
                      entity_type: str | None = None, data: dict | None = None,
                      limit: int | None = None, offset: int | None = None,
                      format_type: str = "detailed", organization_id: str | None = None,
                      project_id: str | None = None, type: str | None = None, id: str | None = None) -> dict[str, Any]:
        """Workspace management tool."""
        # Support backward compatibility: type -> context_type, id -> entity_id
        final_context_type = context_type or type
        final_entity_id = entity_id or id

        if operation == "create":
            return {
                "success": True,
                "data": {
                    "id": f"workspace_{entity_type}_new",
                    **(data or {}),
                    "created_at": datetime.now().isoformat() + "Z"
                }
            }
        if operation in {"list", "list_workspaces"}:
            return {
                "success": True,
                "data": [
                    {"id": f"workspace_{entity_type}_1", "name": "Test Workspace 1"},
                    {"id": f"workspace_{entity_type}_2", "name": "Test Workspace 2"},
                ]
            }
        if operation == "get_context":
            return {
                "success": True,
                "data": {
                    "organization": None,
                    "project": None,
                    "document": None
                }
            }
        if operation == "set_context":
            # Validate context_type - only allow valid types
            valid_context_types = ["organization", "project", "document"]
            if not final_context_type:
                return {"success": False, "error": "context_type is required for set_context"}
            if final_context_type not in valid_context_types:
                return {"success": False, "error": f"Invalid context_type '{final_context_type}'. Must be one of: {', '.join(valid_context_types)}"}
            if not final_entity_id:
                return {"success": False, "error": "entity_id is required for set_context"}

            return {
                "success": True,
                "data": {
                    "type": final_context_type,
                    "id": final_entity_id,
                    "organization_id": organization_id,
                    "project_id": project_id
                }
            }
        if operation == "get_defaults":
            return {
                "success": True,
                "data": {
                    "organization_id": None,
                    "project_id": None,
                    "document_id": None
                }
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def query_tool(operation: str, query: str, filters: dict | None = None) -> dict[str, Any]:
        """Query tool."""
        if operation == "search":
            return {
                "success": True,
                "data": {
                    "results": [
                        {"id": "result_1", "title": "Search Result 1", "score": 0.95},
                        {"id": "result_2", "title": "Search Result 2", "score": 0.87},
                    ],
                    "total": 2,
                    "query": query,
                    "filters": filters or {}
                }
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def workflow_tool(operation: str, name: str, steps: list[str] | None = None) -> dict[str, Any]:
        """Workflow management tool."""
        if operation == "create":
            return {
                "success": True,
                "data": {
                    "id": f"workflow_{name.lower().replace(' ', '_')}",
                    "name": name,
                    "steps": steps or [],
                    "status": "created",
                    "created_at": datetime.now().isoformat() + "Z"
                }
            }
        if operation == "execute":
            return {
                "success": True,
                "data": {
                    "workflow_id": f"workflow_{name.lower().replace(' ', '_')}",
                    "execution_id": f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "status": "completed",
                    "steps_completed": len(steps or [])
                }
            }
        return {"success": False, "error": "unknown_operation"}

    return server


def create_mock_fastmcp_server() -> FastMCP:
    """Create a mocked FastMCP server for COLD mode testing."""
    server = FastMCP("atoms-mock-server")

    # Mock tool implementations
    @server.tool
    def entity_tool(entity_type: str, operation: str, id: str | None = None, data: dict | None = None) -> dict[str, Any]:
        """Mock entity management tool."""
        if operation == "list":
            return {
                "success": True,
                "data": [
                    {"id": f"mock_{entity_type}_1", "name": f"Mock {entity_type.title()} 1"},
                    {"id": f"mock_{entity_type}_2", "name": f"Mock {entity_type.title()} 2"},
                ],
                "count": 2
            }
        if operation == "create":
            return {
                "success": True,
                "data": {
                    "id": f"mock_{entity_type}_new",
                    **(data or {}),
                    "created_at": datetime.now().isoformat() + "Z"
                }
            }
        if operation == "read":
            return {
                "success": True,
                "data": {"id": id, "name": f"Mock {entity_type.title()}"}
            }
        if operation == "update":
            return {
                "success": True,
                "data": {"id": id, **(data or {})}
            }
        if operation == "delete":
            return {"success": True}
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def workspace_tool(operation: str, context_type: str | None = None, entity_id: str | None = None,
                      entity_type: str | None = None, data: dict | None = None,
                      limit: int | None = None, offset: int | None = None,
                      format_type: str = "detailed", organization_id: str | None = None,
                      project_id: str | None = None, type: str | None = None, id: str | None = None) -> dict[str, Any]:
        """Mock workspace management tool."""
        # Support backward compatibility: type -> context_type, id -> entity_id
        final_context_type = context_type or type
        final_entity_id = entity_id or id

        if operation == "create":
            return {
                "success": True,
                "data": {
                    "id": f"mock_workspace_{entity_type}_new",
                    **(data or {}),
                    "created_at": datetime.now().isoformat() + "Z"
                }
            }
        if operation in {"list", "list_workspaces"}:
            return {
                "success": True,
                "data": [
                    {"id": f"mock_workspace_{entity_type}_1", "name": "Mock Workspace 1"},
                    {"id": f"mock_workspace_{entity_type}_2", "name": "Mock Workspace 2"},
                ]
            }
        if operation == "get_context":
            return {
                "success": True,
                "data": {
                    "organization": None,
                    "project": None,
                    "document": None
                }
            }
        if operation == "set_context":
            # Validate context_type - only allow valid types
            valid_context_types = ["organization", "project", "document"]
            if not final_context_type:
                return {"success": False, "error": "context_type is required for set_context"}
            if final_context_type not in valid_context_types:
                return {"success": False, "error": f"Invalid context_type '{final_context_type}'. Must be one of: {', '.join(valid_context_types)}"}
            if not final_entity_id:
                return {"success": False, "error": "entity_id is required for set_context"}

            return {
                "success": True,
                "data": {
                    "type": final_context_type,
                    "id": final_entity_id,
                    "organization_id": organization_id,
                    "project_id": project_id
                }
            }
        if operation == "get_defaults":
            return {
                "success": True,
                "data": {
                    "organization_id": None,
                    "project_id": None,
                    "document_id": None
                }
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def query_tool(operation: str, query: str, filters: dict | None = None) -> dict[str, Any]:
        """Mock query tool."""
        if operation == "search":
            return {
                "success": True,
                "data": {
                    "results": [
                        {"id": "mock_result_1", "title": "Mock Search Result 1", "score": 0.95},
                        {"id": "mock_result_2", "title": "Mock Search Result 2", "score": 0.87},
                    ],
                    "total": 2,
                    "query": query,
                    "filters": filters or {}
                }
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def workflow_tool(operation: str, name: str, steps: list[str] | None = None) -> dict[str, Any]:
        """Mock workflow management tool."""
        if operation == "create":
            return {
                "success": True,
                "data": {
                    "id": f"mock_workflow_{name.lower().replace(' ', '_')}",
                    "name": name,
                    "steps": steps or [],
                    "status": "created",
                    "created_at": datetime.now().isoformat() + "Z"
                }
            }
        if operation == "execute":
            return {
                "success": True,
                "data": {
                    "workflow_id": f"mock_workflow_{name.lower().replace(' ', '_')}",
                    "execution_id": f"mock_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "status": "completed",
                    "steps_completed": len(steps or [])
                }
            }
        return {"success": False, "error": "unknown_operation"}

    return server


def create_simulated_fastmcp_server() -> FastMCP
    """Create a fully simulated FastMCP server for DRY mode testing."""
    server = FastMCP("atoms-simulated-server")

    # Simulated in-memory storage
    simulated_data: dict[str, dict[str, Any]] = {
        "entities": {},
        "workspaces": {},
        "queries": {},
        "workflows": {},
        "relationships": {}
    }

    @server.tool
    def entity_tool(entity_type: str, operation: str, id: str | None = None, data: dict | None = None) -> dict[str, Any]
        """Simulated entity management tool."""
        if operation == "create":
            entity_id = f"sim_{entity_type}_{len(simulated_data['entities']) + 1}"
            entity_data = {
                "id": entity_id,
                "type": entity_type,
                **(data or {}),
                "created_at": datetime.now().isoformat() + "Z",
                "updated_at": datetime.now().isoformat() + "Z"
            }
            simulated_data["entities"][entity_id] = entity_data
            return {
                "success": True,
                "data": entity_data
            }
        if operation == "read":
            if not id:
                return {"success": False, "error": "missing_id"}
            entity = simulated_data["entities"].get(id)
            if entity:
                return {"success": True, "data": entity}
            return {"success": False, "error": "not_found"}
        if operation == "update":
            if not id:
                return {"success": False, "error": "missing_id"}
            entity = simulated_data["entities"].get(id)
            if entity:
                entity.update(data or {})
                entity["updated_at"] = datetime.now().isoformat() + "Z"
                return {"success": True, "data": entity}
            return {"success": False, "error": "not_found"}
        if operation == "delete":
            if id in simulated_data["entities"]:
                del simulated_data["entities"][id]
                return {"success": True}
            return {"success": False, "error": "not_found"}
        if operation == "list":
            entities = [e for e in simulated_data["entities"].values() if e.get("type") == entity_type]
            return {
                "success": True,
                "data": entities,
                "count": len(entities)
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def workspace_tool(operation: str, context_type: str | None = None, entity_id: str | None = None,
                      entity_type: str | None = None, data: dict | None = None,
                      limit: int | None = None, offset: int | None = None,
                      format_type: str = "detailed", organization_id: str | None = None,
                      project_id: str | None = None, type: str | None = None, id: str | None = None) -> dict[str, Any]:
        """Simulated workspace management tool."""
        # Support backward compatibility: type -> context_type, id -> entity_id
        final_context_type = context_type or type
        final_entity_id = entity_id or id

        if operation == "create":
            workspace_id = f"sim_workspace_{entity_type}_{len(simulated_data['workspaces']) + 1}"
            workspace_data = {
                "id": workspace_id,
                "entity_type": entity_type,
                **(data or {}),
                "created_at": datetime.now().isoformat() + "Z"
            }
            simulated_data["workspaces"][workspace_id] = workspace_data
            return {
                "success": True,
                "data": workspace_data
            }
        if operation in {"list", "list_workspaces"}:
            workspaces = [w for w in simulated_data["workspaces"].values() if w.get("entity_type") == entity_type]
            return {
                "success": True,
                "data": workspaces
            }
        if operation == "get_context":
            return {
                "success": True,
                "data": {
                    "organization": None,
                    "project": None,
                    "document": None
                }
            }
        if operation == "set_context":
            # Validate context_type - only allow valid types
            valid_context_types = ["organization", "project", "document"]
            if not final_context_type:
                return {"success": False, "error": "context_type is required for set_context"}
            if final_context_type not in valid_context_types:
                return {"success": False, "error": f"Invalid context_type '{final_context_type}'. Must be one of: {', '.join(valid_context_types)}"}
            if not final_entity_id:
                return {"success": False, "error": "entity_id is required for set_context"}

            return {
                "success": True,
                "data": {
                    "type": final_context_type,
                    "id": final_entity_id,
                    "organization_id": organization_id,
                    "project_id": project_id
                }
            }
        if operation == "get_defaults":
            return {
                "success": True,
                "data": {
                    "organization_id": None,
                    "project_id": None,
                    "document_id": None
                }
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    def query_tool(operation: str, query: str, filters: dict | None = None) -> dict[str, Any]:
        """Simulated query tool."""
        if operation == "search":
            # Simulate search results based on query
            results = []
            for entity in simulated_data["entities"].values():
                if query.lower() in entity.get("name", "").lower():
                    results.append({
                        "id": entity["id"],
                        "title": entity.get("name", "Untitled"),
                        "score": 0.9,
                        "type": entity.get("type", "unknown")
                    })

            return {
                "success": True,
                "data": {
                    "results": results,
                    "total": len(results),
                    "query": query,
                    "filters": filters or {}
                }
            }
        return {"success": False, "error": "unknown_operation"}

    @server.tool
    async def workflow_tool(operation: str, name: str, steps: list[str] | None = None) -> dict[str, Any]:
        """Simulated workflow management tool."""
        if operation == "create":
            workflow_id = f"sim_workflow_{name.lower().replace(' ', '_')}"
            workflow_data = {
                "id": workflow_id,
                "name": name,
                "steps": steps or [],
                "status": "created",
                "created_at": datetime.now().isoformat() + "Z"
            }
            simulated_data["workflows"][workflow_id] = workflow_data
            return {
                "success": True,
                "data": workflow_data
            }
        if operation == "execute":
            workflow_id = f"sim_workflow_{name.lower().replace(' ', '_')}"
            execution_id = f"sim_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Simulate workflow execution
            await asyncio.sleep(0.001)  # Simulate processing time

            return {
                "success": True,
                "data": {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "status": "completed",
                    "steps_completed": len(steps or []),
                    "execution_time": 0.001
                }
            }
        return {"success": False, "error": "unknown_operation"}

    return server


# ============================================================================
# Conditional Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def fastmcp_server(atoms_mode_config: TestModeConfig) -> AsyncIterator[FastMCP]:
    """Mode-aware FastMCP server fixture.

    HOT: Real FastMCP server with test data
    COLD: Mocked FastMCP server with predictable responses
    DRY: Fully simulated FastMCP server with in-memory storage
    """

    if atoms_mode_config.mode == TestMode.HOT:
        server = create_real_fastmcp_server()
    elif atoms_mode_config.mode == TestMode.COLD:
        server = create_mock_fastmcp_server()
    elif atoms_mode_config.mode == TestMode.DRY:
        server = create_simulated_fastmcp_server()
    else:
        raise ValueError(f"Unsupported test mode: {atoms_mode_config.mode}")

    return server


@pytest.fixture
async def fastmcp_client(fastmcp_server: FastMCP, atoms_mode_config: TestModeConfig, request) -> AsyncIterator[Client]:
    """Mode-aware FastMCP client fixture.

    Uses FastHTTPClient for all modes with proper authentication flow.
    """
    import os

    from pheno.testing.mcp_qa.adapters.fast_http_client import FastHTTPClient
    from pheno.testing.mcp_qa.oauth.credential_broker import UnifiedCredentialBroker

    # Set different endpoints based on mode
    if atoms_mode_config.mode == TestMode.HOT:
        endpoint = "http://atomcp:8000/api/mcp"  # Real server for HOT mode
    else:
        endpoint = "http://mcp.atoms:8000/api/mcp"  # Mock endpoint for COLD/DRY modes

    # Get real authentication for all modes
    mcp_endpoint = os.getenv("MCP_ENDPOINT", "https://mcp.atoms.tech/api/mcp")

    # Use UnifiedCredentialBroker for OAuth (will use cache if available)
    broker = UnifiedCredentialBroker(
        mcp_endpoint=mcp_endpoint,
        provider="authkit",
    )

    client = None
    try:
        # Get authenticated client (uses cache if plugin provided credentials)
        _mcp_client, credentials = await broker.get_authenticated_client()
        access_token = credentials.access_token

        # Create re-authentication callback to handle token expiration
        async def reauthenticate():
            """Re-authenticate and return fresh access token when current token expires."""
            _mcp_client, new_creds = await broker.get_authenticated_client()
            return new_creds.access_token

        client = FastHTTPClient(
            mcp_endpoint=endpoint,
            access_token=access_token,
            debug=True,
            reauthenticate_callback=reauthenticate
        )
        await client.__aenter__()
        yield client

    except Exception as e:
        # Fallback to test token if authentication fails
        logger.warning(f"Authentication failed, using test token: {e}")
        client = FastHTTPClient(
            mcp_endpoint=endpoint,
            access_token="test-token",
            debug=True
        )
        await client.__aenter__()
        yield client

    finally:
        # Ensure client is properly closed
        if client:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing client: {e}")


@pytest.fixture(scope="session")
async def entity_client(fastmcp_client: Client) -> AsyncIterator[Client]:
    """Entity-specific client fixture."""
    return fastmcp_client


@pytest.fixture(scope="session")
async def workspace_client(fastmcp_client: Client) -> AsyncIterator[Client]:
    """Workspace-specific client fixture."""
    return fastmcp_client


@pytest.fixture(scope="session")
async def query_client(fastmcp_client: Client) -> AsyncIterator[Client]:
    """Query-specific client fixture."""
    return fastmcp_client


@pytest.fixture(scope="session")
async def workflow_client(fastmcp_client: Client) -> AsyncIterator[Client]:
    """Workflow-specific client fixture."""
    return fastmcp_client


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def test_organization_data():
    """Test data for organization entities."""
    return {
        "name": "Test Organization",
        "description": "A test organization for unit testing",
        "type": "enterprise",
        "status": "active"
    }


@pytest.fixture
def test_project_data():
    """Test data for project entities."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "organization_id": "org_123",
        "status": "active",
        "priority": "high"
    }


@pytest.fixture
def test_document_data():
    """Test data for document entities."""
    return {
        "title": "Test Document",
        "content": "This is test content for unit testing",
        "project_id": "proj_123",
        "status": "draft",
        "author": "test_user"
    }


@pytest.fixture
def test_workspace_data():
    """Test data for workspace entities."""
    return {
        "name": "Test Workspace",
        "description": "A test workspace for unit testing",
        "entity_type": "project",
        "permissions": ["read", "write"],
        "owner": "test_user"
    }


@pytest.fixture
def test_query_data():
    """Test data for query operations."""
    return {
        "query": "test search query",
        "filters": {
            "type": "document",
            "status": "published"
        },
        "limit": 10,
        "offset": 0
    }


@pytest.fixture
def test_workflow_data():
    """Test data for workflow operations."""
    return {
        "name": "Test Workflow",
        "description": "A test workflow for unit testing",
        "steps": [
            "validate_input",
            "process_data",
            "generate_output",
            "send_notification"
        ],
        "trigger": "manual",
        "timeout": 300
    }


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Fixture for measuring test performance."""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def duration(self) -> float:
            if self.start_time is None or self.end_time is None:
                return 0.0
            return self.end_time - self.start_time

        def assert_under(self, max_duration: float):
            """Assert that the operation completed under the specified duration."""
            assert self.duration < max_duration, f"Operation took {self.duration:.3f}s (expected < {max_duration}s)"

    return PerformanceTimer()


# ============================================================================
# Error Simulation Fixtures
# ============================================================================

@pytest.fixture
def error_simulator():
    """Fixture for simulating various error conditions."""
    class ErrorSimulator:
        def __init__(self):
            self.error_count = 0
            self.max_errors = 3

        def should_fail(self) -> bool:
            """Determine if the next operation should fail."""
            self.error_count += 1
            return self.error_count <= self.max_errors

        def simulate_timeout(self):
            """Simulate a timeout error."""
            raise TimeoutError("Operation timed out")

        def simulate_network_error(self):
            """Simulate a network error."""
            raise ConnectionError("Network connection failed")

        def simulate_server_error(self):
            """Simulate a server error."""
            return {
                "success": False,
                "error": "internal_server_error",
                "code": 500,
                "message": "Internal server error"
            }

        def simulate_validation_error(self):
            """Simulate a validation error."""
            return {
                "success": False,
                "error": "validation_failed",
                "details": [
                    "Field 'name' is required",
                    "Field 'type' must be one of: organization, project, document"
                ]
            }

    return ErrorSimulator()
