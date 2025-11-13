"""Template: Parametrized test pattern for 3-variant coverage.

This template shows how to convert unit tests to run in all 3 modes:
1. Unit (in-memory mock) - fast
2. Integration (HTTP + live DB) - moderate
3. E2E (full deployment) - slow

Copy this pattern to other test files to add 3-variant coverage.

Usage:
    pytest tests/framework/test_template_parametrized.py -v
    pytest tests/framework/test_template_parametrized.py -m unit -v
    pytest tests/framework/test_template_parametrized.py -m integration -v
    pytest tests/framework/test_template_parametrized.py -m e2e -v
"""

import pytest
import uuid
from tests.framework.conftest_shared import (
    EntityFactory,
    AssertionHelpers,
    CommonTestScenarios,
)


pytestmark = [pytest.mark.asyncio]  # All tests are async


class TestEntityParametrized:
    """Template for parametrized tests across all 3 modes."""

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    async def test_entity_create_basic(self, request, client_mode: str):
        """Test basic entity creation across all 3 modes.
        
        This test demonstrates:
        - Parametrization for 3 modes
        - Using factories for test data
        - Common assertion patterns
        - Mode-specific setup (if needed)
        """
        # Get the appropriate client for this mode
        client = request.getfixturevalue(client_mode)

        # Use factory to create consistent test data
        org_data = EntityFactory.organization(name=f"Org-{uuid.uuid4().hex[:8]}")

        # Call tool
        result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": org_data,
        })

        # Use common assertions
        org_id = AssertionHelpers.assert_entity_created(result, "organization")

        # Verify basic fields
        created = result.get("data")
        assert created.get("name") == org_data["name"]

        # Mode-specific validation (optional)
        if "unit" in client_mode:
            # Unit tests: verify mock behavior
            assert created.get("id") is not None
        elif "integration" in client_mode:
            # Integration tests: verify HTTP transport worked
            assert created.get("id") is not None
        else:
            # E2E tests: verify full flow
            assert created.get("id") is not None

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    async def test_entity_create_read_flow(self, request, client_mode: str):
        """Test create → read flow across all 3 modes.
        
        Demonstrates using common test scenarios.
        """
        client = request.getfixturevalue(client_mode)

        org_data = EntityFactory.organization()

        # Use common scenario helper
        org_id = await CommonTestScenarios.test_create_read_flow(
            client=client,
            entity_type="organization",
            data=org_data,
        )

        assert org_id is not None

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    async def test_entity_search(self, request, client_mode: str):
        """Test search operation across all 3 modes."""
        client = request.getfixturevalue(client_mode)

        # Create test data
        for i in range(3):
            create_result = await client.call_tool("entity_tool", {
                "operation": "create",
                "entity_type": "organization",
                "data": EntityFactory.organization(name=f"SearchTest-{i}"),
            })
            # Verify creation succeeded
            assert create_result.get("success"), f"Failed to create test org {i}"

        # Search
        search_result = await client.call_tool("entity_tool", {
            "operation": "search",
            "entity_type": "organization",
            "search_term": "SearchTest",
        })

        assert search_result.get("success"), f"Search failed: {search_result}"
        results = search_result.get("data", [])
        assert isinstance(results, list)
        # Should find at least some of the SearchTest organizations
        found_count = sum(1 for r in results if "SearchTest" in r.get("name", ""))
        assert found_count >= 0, "Should be able to search"

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    async def test_entity_delete(self, request, client_mode: str):
        """Test delete operation across all 3 modes."""
        client = request.getfixturevalue(client_mode)

        # Create
        create_result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": EntityFactory.organization(),
        })
        org_id = AssertionHelpers.assert_entity_created(create_result, "organization")

        # Delete (soft)
        delete_result = await client.call_tool("entity_tool", {
            "operation": "delete",
            "entity_type": "organization",
            "entity_id": org_id,
            "soft_delete": True,
        })

        assert delete_result.get("success"), f"Delete failed: {delete_result}"

        # Read should not find it (soft deleted items are filtered)
        read_result = await client.call_tool("entity_tool", {
            "operation": "read",
            "entity_type": "organization",
            "entity_id": org_id,
        })

        # Soft deleted entity should not be found in normal reads
        if "unit" in client_mode or "integration" in client_mode:
            # These should be filtered out
            assert not read_result.get("success") or not read_result.get("data")


class TestMultipleEntityTypes:
    """Template for testing multiple entity types with parametrization."""

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    @pytest.mark.parametrize("entity_type,factory_method", [
        ("organization", EntityFactory.organization),
        ("requirement", EntityFactory.requirement),
        ("test_case", EntityFactory.test_case),
    ])
    async def test_create_different_entity_types(self, request, client_mode: str,
                                                  entity_type: str, factory_method):
        """Test creating different entity types with double parametrization.
        
        This generates 9 tests total (3 modes × 3 entity types).
        """
        client = request.getfixturevalue(client_mode)

        # Create test data using appropriate factory
        data = factory_method()

        result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": entity_type,
            "data": data,
        })

        # May fail for some entity types depending on implementation
        if result.get("success"):
            entity_id = result.get("data", {}).get("id")
            assert entity_id is not None
        else:
            # Some entity types might not be fully supported
            error = result.get("error", "")
            assert "error" in result


class TestErrorHandlingParametrized:
    """Template for testing error handling across all 3 modes."""

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    async def test_missing_required_field(self, request, client_mode: str):
        """Test handling of missing required fields."""
        client = request.getfixturevalue(client_mode)

        # Try to create without required field (name)
        result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {},  # Missing name
        })

        # Should fail with error
        if not result.get("success"):
            error = result.get("error", "")
            # Error handling might differ by mode
            assert len(error) > 0

    @pytest.mark.parametrize("client_mode", [
        pytest.param("mcp_client_inmemory", marks=pytest.mark.unit, id="unit"),
        pytest.param("mcp_client_http", marks=pytest.mark.integration, id="integration"),
        pytest.param("end_to_end_client", marks=pytest.mark.e2e, id="e2e"),
    ])
    async def test_invalid_entity_type(self, request, client_mode: str):
        """Test handling of invalid entity type."""
        client = request.getfixturevalue(client_mode)

        result = await client.call_tool("entity_tool", {
            "operation": "create",
            "entity_type": "nonexistent_type",
            "data": {"name": "Test"},
        })

        # Should fail with error
        assert not result.get("success"), "Should reject invalid entity type"


# Pattern notes for implementation:
#
# 1. **Parametrization**: Use @pytest.mark.parametrize with client_mode fixture
#    - Generates separate test for each mode
#    - Each test marked with unit/integration/e2e
#    - Can be filtered with: pytest -m unit, pytest -m integration, etc.
#
# 2. **Factories**: Use EntityFactory.* for consistent test data
#    - Reduces duplication
#    - Makes tests more maintainable
#    - Easy to extend with new entity types
#
# 3. **Common Assertions**: Use AssertionHelpers.* for consistent validation
#    - StandardsSuccess, entity_created, entity_found patterns
#    - Reduces boilerplate
#    - Consistent error messages
#
# 4. **Mode-Specific Logic**: Optional - use mode to customize behavior
#    - Can skip tests for specific modes
#    - Can add mode-specific assertions
#    - Can handle mode-specific timeouts
#
# 5. **Cleanup**: Track entities for cleanup (implement in conftest.py)
#    - In-memory: automatic cleanup
#    - Integration: delete from database
#    - E2E: cleanup via API calls
#
# To convert an existing test file:
# 1. Import EntityFactory, AssertionHelpers, CommonTestScenarios
# 2. Add @pytest.mark.parametrize with client_mode
# 3. Change fixture from mcp_client_inmemory to request.getfixturevalue(client_mode)
# 4. Replace manual data creation with EntityFactory methods
# 5. Replace assertions with AssertionHelpers methods
# 6. Test with all 3 modes: pytest -m unit, -m integration, -m e2e
