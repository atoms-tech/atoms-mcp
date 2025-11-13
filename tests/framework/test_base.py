"""Base test infrastructure for 3-variant test coverage.

This module provides:
- ParametrizedTestSuite: Base class for tests running in unit/integration/e2e modes
- Client variations: In-memory, HTTP, and full deployment clients
- Mode-aware assertions and helpers
- Common test patterns and utilities

Usage:
    class MyTestSuite(ParametrizedTestSuite):
        @pytest.mark.asyncio
        async def test_entity_create(self):
            # Test runs in all 3 modes automatically
            result = await self.client.call_tool("entity_tool", {...})
            self.assert_success(result)
"""

import pytest
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager


class ParametrizedTestSuite:
    """Base class for tests that run in all 3 modes: unit, integration, e2e.
    
    Provides:
    - Unified client access across test variants
    - Mode-aware expectations (e.g., certain errors only in integration)
    - Common assertion patterns
    - Timing and performance helpers
    """

    @pytest.fixture
    def client_variants(self):
        """Parametrized client fixture for all 3 test modes.
        
        Returns:
            List of (fixture_name, marker) pairs for parametrization
        """
        return [
            pytest.param(
                "mcp_client_inmemory",
                marks=pytest.mark.unit,
                id="unit"
            ),
            pytest.param(
                "mcp_client_http",
                marks=pytest.mark.integration,
                id="integration"
            ),
            pytest.param(
                "end_to_end_client",
                marks=pytest.mark.e2e,
                id="e2e"
            ),
        ]

    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def client(self, request):
        """Get the appropriate client for current test variant.
        
        Test classes inherit this automatically when extending ParametrizedTestSuite.
        """
        return request.getfixturevalue(request.param)

    # Mode-aware assertions

    def assert_success(self, result: Dict[str, Any], timeout: Optional[float] = None):
        """Assert operation succeeded, with mode-aware expectations."""
        assert result is not None, "Result should not be None"
        assert result.get("success") is True, f"Operation failed: {result.get('error', 'Unknown error')}"

        # Unit tests should never have timing issues
        if timeout and hasattr(self, 'current_mode') and self.current_mode == "unit":
            # In unit mode, operations should be virtually instantaneous
            pass

    def assert_error(self, result: Dict[str, Any], expected_error: Optional[str] = None):
        """Assert operation failed with expected error pattern."""
        assert result is not None, "Result should not be None"
        assert result.get("success") is False, "Operation should have failed"

        if expected_error:
            error_msg = result.get("error", "")
            assert expected_error.lower() in error_msg.lower(), \
                f"Expected error '{expected_error}' in '{error_msg}'"

    def assert_has_id(self, result: Dict[str, Any], entity_data: Optional[Dict] = None):
        """Assert result contains valid entity ID."""
        self.assert_success(result)
        data = result.get("data", {})
        assert "id" in data, "Result should contain entity ID"
        assert data["id"], "Entity ID should not be empty"

        # For integration/e2e, validate ID format
        if hasattr(self, 'current_mode') and self.current_mode in ["integration", "e2e"]:
            assert len(data["id"]) > 10, "Entity ID should be substantial"

    def assert_has_timestamps(self, result: Dict[str, Any]):
        """Assert result contains created_at/updated_at timestamps."""
        self.assert_success(result)
        data = result.get("data", {})
        assert "created_at" in data, "Result should contain created_at timestamp"
        assert data["created_at"], "created_at should not be empty"

    def assert_list_response(self, result: Dict[str, Any], min_count: int = 0):
        """Assert list operation returns valid pagination structure."""
        self.assert_success(result)
        data = result.get("data", {})
        assert isinstance(data, list), "List should return array of items"
        assert len(data) >= min_count, f"Expected at least {min_count} items, got {len(data)}"

    # Entity-specific helpers

    def assert_entity_structure(self, entity_data: Dict[str, Any], entity_type: str):
        """Assert entity has expected structure for its type."""
        required_fields = ["id", "type", "name", "created_at"]
        for field in required_fields:
            assert field in entity_data, f"Entity missing required field: {field}"

        assert entity_data["type"] == entity_type, \
            f"Expected type {entity_type}, got {entity_data['type']}"

        # Type-specific validation
        if entity_type == "organization":
            # Organizations can exist independently
            pass
        elif entity_type == "project":
            # Projects typically belong to organizations
            if "organization_id" in entity_data:
                assert entity_data["organization_id"], "Project organization_id should not be empty"
        elif entity_type == "document":
            # Documents typically belong to projects
            if "project_id" in entity_data:
                assert entity_data["project_id"], "Document project_id should not be empty"

    def assert_relationship_structure(self, rel_data: Dict[str, Any]):
        """Assert relationship has expected structure."""
        required_fields = ["id", "source_id", "target_id", "relationship_type"]
        for field in required_fields:
            assert field in rel_data, f"Relationship missing required field: {field}"

        assert rel_data["source_id"] != rel_data["target_id"], \
            "Relationship should not be circular (source != target)"

    # Performance helpers

    def assert_timing(self, start_time: float, end_time: float, max_ms: float):
        """Assert operation completed within expected time bounds."""
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms <= max_ms, \
            f"Operation took {elapsed_ms:.2f}ms, expected < {max_ms}ms"

    @asynccontextmanager
    async def measure_timing(self):
        """Measure execution time of async operations."""
        import time
        start = time.perf_counter()
        yield
        self.last_timing = (time.perf_counter() - start) * 1000

    # Data creation helpers

    def create_test_entity(self, entity_type: str, **overrides) -> Dict[str, Any]:
        """Create test entity data with proper structure."""
        base_data = {
            "name": f"test-{entity_type}-{hash(overrides) % 10000}",
            "type": entity_type,
        }

        # Add type-specific defaults
        if entity_type == "organization":
            base_data.update({
                "description": "Test organization",
            })
        elif entity_type == "project":
            base_data.update({
                "description": "Test project",
                "status": "active",
            })
        elif entity_type == "document":
            base_data.update({
                "content": "Test document content",
                "version": "1.0.0",
            })
        elif entity_type == "requirement":
            base_data.update({
                "description": "Test requirement description",
                "priority": "medium",
                "status": "draft",
            })

        # Apply overrides
        base_data.update(overrides)
        return base_data

    def create_test_relationship(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relationship_type: str = "relates_to",
        **metadata
    ) -> Dict[str, Any]:
        """Create test relationship data."""
        return {
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "metadata": metadata,
        }


class ThreeVariantTestMixin:
    """Mixin for adding 3-variant parametrization to existing test classes.
    
    Usage:
        class ExistingTestClass(ThreeVariantTestMixin):
            @pytest.mark.asyncio
            async def test_something(self):
                # Now runs in all 3 variants
                pass
    """

    @pytest.fixture(params=[
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit),
        pytest.param("mcp_client_http", marks=pytest.mark.integration),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e),
    ], ids=["unit", "integration", "e2e"])
    async def parametrized_client(self, request):
        """Parametrized client for mixed test classes."""
        return request.getfixturevalue(request.param)


# Common test patterns

class EntityTestPattern(ParametrizedTestSuite):
    """Base test pattern for entity CRUD operations."""

    async def test_create_basic(self):
        """Test basic entity creation."""
        entity_data = self.create_test_entity("organization")
        result = await self.client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_data["type"],
            "data": entity_data
        })
        self.assert_has_id(result)
        self.assert_entity_structure(result["data"], entity_data["type"])

    async def test_read_with_relations(self):
        """Test reading entity with relationships."""
        # First create an entity
        entity_data = self.create_test_entity("organization")
        create_result = await self.client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_data["type"],
            "data": entity_data
        })
        self.assert_success(create_result)
        entity_id = create_result["data"]["id"]

        # Then read it with relations
        result = await self.client.call_tool("entity_tool", {
            "operation": "read",
            "entity_type": entity_data["type"],
            "entity_id": entity_id,
            "include_relations": True
        })
        self.assert_success(result)
        self.assert_entity_structure(result["data"], entity_data["type"])

    async def test_update_basic(self):
        """Test basic entity update."""
        # Create entity first
        entity_data = self.create_test_entity("organization")
        create_result = await self.client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_data["type"],
            "data": entity_data
        })
        entity_id = create_result["data"]["id"]

        # Update it
        update_data = {"name": "Updated Organization Name"}
        result = await self.client.call_tool("entity_tool", {
            "operation": "update",
            "entity_type": entity_data["type"],
            "entity_id": entity_id,
            "data": update_data
        })
        self.assert_success(result)
        assert result["data"]["name"] == update_data["name"]

    async def test_delete_soft(self):
        """Test soft entity deletion."""
        # Create entity first
        entity_data = self.create_test_entity("organization")
        create_result = await self.client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_data["type"],
            "data": entity_data
        })
        entity_id = create_result["data"]["id"]

        # Soft delete it
        result = await self.client.call_tool("entity_tool", {
            "operation": "delete",
            "entity_type": entity_data["type"],
            "entity_id": entity_id,
            "soft_delete": True
        })
        self.assert_success(result)

        # Verify it's "deleted" (shouldn't appear in normal queries)
        list_result = await self.client.call_tool("entity_tool", {
            "operation": "list",
            "entity_type": entity_data["type"]
        })
        self.assert_success(list_result)
        # Should not contain our deleted entity (soft delete)
        assert not any(e["id"] == entity_id for e in list_result["data"])


class WorkflowTestPattern(ParametrizedTestSuite):
    """Base test pattern for workflow execution."""

    async def test_execute_basic_workflow(self):
        """Test basic workflow execution."""
        workflow_data = {
            "name": "Basic Test Workflow",
            "description": "A simple test workflow",
            "steps": [
                {
                    "name": "create_org",
                    "tool": "entity_tool",
                    "parameters": {"operation": "create", "entity_type": "organization"}
                }
            ]
        }

        result = await self.client.call_tool("workflow_tool", {
            "operation": "execute",
            "workflow_name": workflow_data["name"],
            "data": workflow_data
        })
        self.assert_success(result)
        assert "execution_id" in result["data"]


class RelationshipTestPattern(ParametrizedTestSuite):
    """Base test pattern for relationship operations."""

    async def test_create_relationship(self):
        """Test relationship creation."""
        # Create source entity
        source_data = self.create_test_entity("organization")
        source_result = await self.client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": source_data
        })
        source_id = source_result["data"]["id"]

        # Create target entity
        target_data = self.create_test_entity("project")
        target_result = await self.client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "project",
            "data": target_data
        })
        target_id = target_result["data"]["id"]

        # Create relationship
        rel_data = self.create_test_relationship(
            "organization", source_id,
            "project", target_id,
            "parent_of"
        )
        result = await self.client.call_tool("relationship_tool", {
            "operation": "create",
            **rel_data
        })
        self.assert_has_id(result)
        self.assert_relationship_structure(result["data"])


# Pytest markers for easy selection
pytest_plugins = []

def pytest_configure(config):
    """Add custom markers for test patterns."""
    config.addinivalue_line(
        "markers", "three_variant: marks tests that run in unit/integration/e2e modes"
    )
    config.addinivalue_line(
        "markers", "entity_pattern: marks tests using EntityTestPattern"
    )
    config.addinivalue_line(
        "markers", "workflow_pattern: marks tests using WorkflowTestPattern"
    )
    config.addinivalue_line(
        "markers", "relationship_pattern: marks tests using RelationshipTestPattern"
    )
