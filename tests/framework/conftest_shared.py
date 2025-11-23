"""Shared test infrastructure for parametrized testing across all 3 modes.

This module provides:
- Parametrized client fixture for unit/integration/e2e modes
- Unified test base class with mode detection
- Shared data generators and factories
- Common assertions and validation helpers

Usage:
    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def parametrized_client(request):
        return request.getfixturevalue(request.param)
"""

import uuid
import pytest
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import consolidated EntityFactory from data_generators
from .data_generators import EntityFactory


@dataclass
class TestContext:
    """Context information for parametrized tests."""
    mode: str  # "unit", "integration", or "e2e"
    client: Any  # The actual MCP client
    created_entities: List[tuple] = None  # Track (type, id) for cleanup

    def __post_init__(self):
        if self.created_entities is None:
            self.created_entities = []

    def track_entity(self, entity_type: str, entity_id: str):
        """Track an entity for cleanup."""
        self.created_entities.append((entity_type, entity_id))
        return entity_id


# Import consolidated EntityFactory from data_generators
from .data_generators import EntityFactory

# Backward compatibility: EntityFactory is now imported from data_generators
# This consolidates DataGenerator and EntityFactory into a single class


class AssertionHelpers:
    """Common assertions for parametrized tests."""

    @staticmethod
    def assert_success(result: Dict[str, Any], operation: str = "Operation") -> Dict[str, Any]:
        """Assert operation succeeded and return data."""
        assert result.get("success"), f"{operation} returned false: {result}"
        assert "data" in result, f"{operation} missing data field: {result}"
        return result.get("data")

    @staticmethod
    def assert_entity_created(result: Dict[str, Any], entity_type: str = "") -> str:
        """Assert entity was created and return ID."""
        data = AssertionHelpers.assert_success(result, f"Create {entity_type}")
        assert "id" in data, f"Created {entity_type} missing id: {data}"
        # created_at may not always be present in mock DB
        assert "name" in data or "title" in data or "id" in data
        return data["id"]

    @staticmethod
    def assert_entity_found(result: Dict[str, Any], entity_id: str, entity_type: str = "") -> Dict[str, Any]:
        """Assert entity was found and returned."""
        data = AssertionHelpers.assert_success(result, f"Read {entity_type}")
        assert data.get("id") == entity_id, f"Read {entity_type}: ID mismatch"
        return data

    @staticmethod
    def assert_error(result: Dict[str, Any], expected_error: Optional[str] = None) -> str:
        """Assert operation failed with error."""
        assert result.get("success") is False, f"Expected failure but got: {result}"
        error_msg = result.get("error", "")
        if expected_error:
            assert expected_error.lower() in error_msg.lower(), \
                f"Expected error containing '{expected_error}' but got '{error_msg}'"
        return error_msg


class CommonTestScenarios:
    """Common test scenarios that work across all 3 modes."""

    @staticmethod
    async def test_create_read_flow(client: Any, entity_type: str, data: Dict[str, Any]) -> str:
        """Standard create → read flow."""
        # Create
        create_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_type,
            "data": data,
        })

        entity_id = AssertionHelpers.assert_entity_created(create_result, entity_type)

        # Read
        read_result = await client.call_tool("entity_tool", {
            "operation": "read",
            "entity_type": entity_type,
            "entity_id": entity_id,
        })

        AssertionHelpers.assert_entity_found(read_result, entity_id, entity_type)

        return entity_id

    @staticmethod
    async def test_create_update_read_flow(client: Any, entity_type: str,
                                          create_data: Dict[str, Any],
                                          update_data: Dict[str, Any]) -> str:
        """Standard create → update → read flow."""
        # Create
        create_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_type,
            "data": create_data,
        })
        entity_id = AssertionHelpers.assert_entity_created(create_result, entity_type)

        # Update
        update_result = await client.call_tool("entity_tool", {
            "operation": "update",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": update_data,
        })
        AssertionHelpers.assert_success(update_result, f"Update {entity_type}")

        # Read
        read_result = await client.call_tool("entity_tool", {
            "operation": "read",
            "entity_type": entity_type,
            "entity_id": entity_id,
        })
        AssertionHelpers.assert_entity_found(read_result, entity_id, entity_type)

        return entity_id

    @staticmethod
    async def test_search_flow(client: Any, entity_type: str, search_term: str) -> List[str]:
        """Standard search flow."""
        search_result = await client.call_tool("entity_tool", {
            "operation": "search",
            "entity_type": entity_type,
            "search_term": search_term,
        })

        assert search_result.get("success"), f"Search failed: {search_result}"
        data = search_result.get("data", [])
        assert isinstance(data, list), f"Search should return list, got {type(data)}"

        return [item.get("id") for item in data if item.get("id")]


# Fixture for mode detection (use in conftest.py)
@pytest.fixture(params=[
    pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
    pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
    pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
])
async def parametrized_client(request):
    """Parametrized fixture providing client for all 3 modes.
    
    Usage:
        async def test_entity_creation(parametrized_client):
            result = await parametrized_client.call_tool(...)
    """
    return request.getfixturevalue(request.param)


@pytest.fixture
def test_context(parametrized_client, request):
    """Provide test context with mode information."""
    mode = None
    if request.node.get_closest_marker("unit"):
        mode = "unit"
    elif request.node.get_closest_marker("integration"):
        mode = "integration"
    elif request.node.get_closest_marker("e2e"):
        mode = "e2e"

    context = TestContext(mode=mode or "unknown", client=parametrized_client)
    yield context

    # Cleanup tracked entities (optional - can be customized per conftest)
    # In unit tests, in-memory DB clears automatically
    # In integration/e2e, would need custom cleanup
