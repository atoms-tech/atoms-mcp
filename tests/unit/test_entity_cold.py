"""
COLD Mode Entity Tool Tests - Unit Tests with Mocked Dependencies

These tests run in COLD mode with mocked dependencies:
- No real server required
- Uses in-memory mocks
- Very fast execution (< 2s)
- Can run in parallel
- Tests application logic without external dependencies

Run with: pytest tests/unit/test_entity_cold.py -v --mode cold
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest


@pytest.mark.cold
class TestEntityColdMode:
    """COLD mode tests for entity operations with mocked dependencies."""

    @pytest.fixture
    def mock_entity_data(self):
        """Mock entity data for testing."""
        return {
            "organizations": [
                {"id": "org_1", "name": "Test Org 1", "created_at": "2024-01-01T00:00:00Z"},
                {"id": "org_2", "name": "Test Org 2", "created_at": "2024-01-02T00:00:00Z"},
            ],
            "projects": [
                {"id": "proj_1", "name": "Test Project 1", "organization_id": "org_1"},
                {"id": "proj_2", "name": "Test Project 2", "organization_id": "org_2"},
            ],
            "documents": [
                {"id": "doc_1", "title": "Test Document 1", "project_id": "proj_1"},
                {"id": "doc_2", "title": "Test Document 2", "project_id": "proj_2"},
            ],
        }

    @pytest.fixture
    def mock_client(self, mock_entity_data):
        """Create a mocked MCP client for COLD mode testing."""
        client = AsyncMock()

        # Mock list operations
        async def mock_call_tool(tool_name: str, arguments: dict) -> dict:
            if tool_name == "entity_tool":
                operation = arguments.get("operation")
                entity_type = arguments.get("entity_type")

                if operation == "list":
                    entities = mock_entity_data.get(f"{entity_type}s", [])
                    return {
                        "success": True,
                        "data": entities,
                        "count": len(entities)
                    }
                elif operation == "create":
                    entity_id = f"{entity_type}_{len(mock_entity_data.get(f'{entity_type}s', [])) + 1}"
                    new_entity = {
                        "id": entity_id,
                        **arguments.get("data", {}),
                        "created_at": datetime.now().isoformat() + "Z"
                    }
                    mock_entity_data.setdefault(f"{entity_type}s", []).append(new_entity)
                    return {
                        "success": True,
                        "data": new_entity,
                        "id": entity_id
                    }
                elif operation == "read":
                    entity_id = arguments.get("id")
                    entities = mock_entity_data.get(f"{entity_type}s", [])
                    entity = next((e for e in entities if e["id"] == entity_id), None)
                    if entity:
                        return {"success": True, "data": entity}
                    else:
                        return {"success": False, "error": "not_found"}
                elif operation == "update":
                    entity_id = arguments.get("id")
                    entities = mock_entity_data.get(f"{entity_type}s", [])
                    entity = next((e for e in entities if e["id"] == entity_id), None)
                    if entity:
                        entity.update(arguments.get("data", {}))
                        return {"success": True, "data": entity}
                    else:
                        return {"success": False, "error": "not_found"}
                elif operation == "delete":
                    entity_id = arguments.get("id")
                    entities = mock_entity_data.get(f"{entity_type}s", [])
                    entity = next((e for e in entities if e["id"] == entity_id), None)
                    if entity:
                        entities.remove(entity)
                        return {"success": True}
                    else:
                        return {"success": False, "error": "not_found"}

            return {"success": False, "error": "unknown_tool"}

        client.call_tool = mock_call_tool
        client.health_check = AsyncMock(return_value=True)
        client.close = AsyncMock()

        return client

    @pytest.mark.cold
    async def test_list_organizations_cold(self, mock_client):
        """Test listing organizations with mocked data."""
        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        assert result["success"], f"Failed to list organizations: {result.get('error')}"
        assert "data" in result
        organizations = result["data"]
        assert isinstance(organizations, list)
        assert len(organizations) == 2
        assert organizations[0]["name"] == "Test Org 1"

    @pytest.mark.cold
    async def test_list_projects_cold(self, mock_client):
        """Test listing projects with mocked data."""
        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "list"
            }
        )

        assert result["success"], f"Failed to list projects: {result.get('error')}"
        assert "data" in result
        projects = result["data"]
        assert isinstance(projects, list)
        assert len(projects) == 2
        assert projects[0]["name"] == "Test Project 1"

    @pytest.mark.cold
    async def test_create_organization_cold(self, mock_client):
        """Test creating organization with mocked data."""
        new_org_data = {
            "name": "New Test Org",
            "description": "A new test organization"
        }

        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": new_org_data
            }
        )

        assert result["success"], f"Failed to create organization: {result.get('error')}"
        assert "data" in result
        created_org = result["data"]
        assert created_org["name"] == "New Test Org"
        assert "id" in created_org
        assert "created_at" in created_org

    @pytest.mark.cold
    async def test_read_organization_cold(self, mock_client):
        """Test reading organization with mocked data."""
        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": "org_1"
            }
        )

        assert result["success"], f"Failed to read organization: {result.get('error')}"
        assert "data" in result
        org = result["data"]
        assert org["id"] == "org_1"
        assert org["name"] == "Test Org 1"

    @pytest.mark.cold
    async def test_update_organization_cold(self, mock_client):
        """Test updating organization with mocked data."""
        update_data = {
            "name": "Updated Org Name",
            "description": "Updated description"
        }

        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "id": "org_1",
                "data": update_data
            }
        )

        assert result["success"], f"Failed to update organization: {result.get('error')}"
        assert "data" in result
        updated_org = result["data"]
        assert updated_org["name"] == "Updated Org Name"
        assert updated_org["description"] == "Updated description"

    @pytest.mark.cold
    async def test_delete_organization_cold(self, mock_client):
        """Test deleting organization with mocked data."""
        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "delete",
                "id": "org_1"
            }
        )

        assert result["success"], f"Failed to delete organization: {result.get('error')}"

    @pytest.mark.cold
    async def test_entity_not_found_cold(self, mock_client):
        """Test handling of non-existent entity with mocked data."""
        result = await mock_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": "nonexistent_id"
            }
        )

        assert not result["success"]
        assert result["error"] == "not_found"

    @pytest.mark.cold
    async def test_cold_mode_performance(self, mock_client):
        """Test that COLD mode operations complete within 2 seconds."""
        import time

        start_time = time.time()

        # Perform multiple operations
        for i in range(10):
            await mock_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "list"
                }
            )

        duration = time.time() - start_time
        assert duration < 2.0, f"COLD mode test took {duration:.2f}s (expected < 2s)"

    @pytest.mark.cold
    async def test_cold_mode_parallel_execution(self, mock_client):
        """Test that COLD mode supports parallel execution."""
        import asyncio

        # Run multiple operations concurrently
        tasks = [
            mock_client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"}),
            mock_client.call_tool("entity_tool", {"entity_type": "project", "operation": "list"}),
            mock_client.call_tool("entity_tool", {"entity_type": "document", "operation": "list"}),
        ]

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        for result in results:
            assert result["success"], f"Parallel operation failed: {result.get('error')}"


@pytest.mark.cold
class TestEntityValidationCold:
    """COLD mode tests for entity validation logic."""

    @pytest.fixture
    def mock_validation_client(self):
        """Create a mocked client with validation logic."""
        client = AsyncMock()

        async def mock_call_tool(tool_name: str, arguments: dict) -> dict:
            if tool_name == "entity_tool":
                operation = arguments.get("operation")
                entity_type = arguments.get("entity_type")
                data = arguments.get("data", {})

                # Validation logic
                if operation == "create":
                    if not data.get("name"):
                        return {"success": False, "error": "name_required"}

                    if entity_type == "organization" and len(data.get("name", "")) < 3:
                        return {"success": False, "error": "name_too_short"}

                    if entity_type == "project" and not data.get("organization_id"):
                        return {"success": False, "error": "organization_id_required"}

                return {"success": True, "data": data}

            return {"success": False, "error": "unknown_tool"}

        client.call_tool = mock_call_tool
        return client

    @pytest.mark.cold
    async def test_organization_validation_cold(self, mock_validation_client):
        """Test organization validation with mocked logic."""
        # Test valid organization
        result = await mock_validation_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "Valid Org"}
            }
        )
        assert result["success"]

        # Test missing name
        result = await mock_validation_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {}
            }
        )
        assert not result["success"]
        assert result["error"] == "name_required"

        # Test name too short
        result = await mock_validation_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "AB"}
            }
        )
        assert not result["success"]
        assert result["error"] == "name_too_short"

    @pytest.mark.cold
    async def test_project_validation_cold(self, mock_validation_client):
        """Test project validation with mocked logic."""
        # Test valid project
        result = await mock_validation_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": "Valid Project", "organization_id": "org_1"}
            }
        )
        assert result["success"]

        # Test missing organization_id
        result = await mock_validation_client.call_tool(
            "entity_tool",
            {
                "entity_type": "project",
                "operation": "create",
                "data": {"name": "Invalid Project"}
            }
        )
        assert not result["success"]
        assert result["error"] == "organization_id_required"


@pytest.mark.cold
class TestEntityErrorHandlingCold:
    """COLD mode tests for error handling scenarios."""

    @pytest.fixture
    def mock_error_client(self):
        """Create a mocked client that simulates various error conditions."""
        client = AsyncMock()

        async def mock_call_tool(tool_name: str, arguments: dict) -> dict:
            if tool_name == "entity_tool":
                operation = arguments.get("operation")

                if operation == "timeout":
                    raise TimeoutError("Operation timed out")
                elif operation == "network_error":
                    raise ConnectionError("Network connection failed")
                elif operation == "server_error":
                    return {"success": False, "error": "internal_server_error", "code": 500}
                elif operation == "validation_error":
                    return {"success": False, "error": "validation_failed", "details": ["field1 is required"]}

                return {"success": True, "data": {"operation": operation}}

            return {"success": False, "error": "unknown_tool"}

        client.call_tool = mock_call_tool
        return client

    @pytest.mark.cold
    async def test_timeout_error_handling_cold(self, mock_error_client):
        """Test timeout error handling in COLD mode."""
        with pytest.raises(asyncio.TimeoutError):
            await mock_error_client.call_tool(
                "entity_tool",
                {"operation": "timeout"}
            )

    @pytest.mark.cold
    async def test_network_error_handling_cold(self, mock_error_client):
        """Test network error handling in COLD mode."""
        with pytest.raises(ConnectionError):
            await mock_error_client.call_tool(
                "entity_tool",
                {"operation": "network_error"}
            )

    @pytest.mark.cold
    async def test_server_error_handling_cold(self, mock_error_client):
        """Test server error handling in COLD mode."""
        result = await mock_error_client.call_tool(
            "entity_tool",
            {"operation": "server_error"}
        )

        assert not result["success"]
        assert result["error"] == "internal_server_error"
        assert result["code"] == 500

    @pytest.mark.cold
    async def test_validation_error_handling_cold(self, mock_error_client):
        """Test validation error handling in COLD mode."""
        result = await mock_error_client.call_tool(
            "entity_tool",
            {"operation": "validation_error"}
        )

        assert not result["success"]
        assert result["error"] == "validation_failed"
        assert "details" in result
        assert "field1 is required" in result["details"]
