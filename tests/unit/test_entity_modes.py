"""
Entity Tool Tests with Test Mode Support

This file demonstrates comprehensive test mode implementation following FastMCP patterns:
- HOT: Integration tests with real dependencies (live server, actual database)
- COLD: Unit tests with mocked adapters (no network, fast execution)
- DRY: Fully simulated tests (everything mocked, testing logic only)

Each test operation is implemented in all three modes to show the progression
from real integration testing to pure unit testing.

Run with:
    pytest tests/unit/test_entity_modes.py -v --mode hot
    pytest tests/unit/test_entity_modes.py -v --mode cold
    pytest tests/unit/test_entity_modes.py -v --mode dry
"""


import pytest

# ============================================================================
# HOT Mode Tests - Real Integration Tests
# ============================================================================

@pytest.mark.hot
class TestEntityHOTMode:
    """HOT mode tests with real server and database integration."""

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_list_organizations_hot(self, authenticated_client):
        """Test listing organizations with real server integration."""
        result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        assert result.get("success"), f"Failed to list organizations: {result.get('error')}"
        assert "data" in result
        organizations = result["data"]
        assert isinstance(organizations, list)
        # In HOT mode, we expect real data from the database
        assert len(organizations) >= 0  # Could be empty or have data

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_create_organization_hot(self, authenticated_client, test_organization_data):
        """Test creating organization with real server integration."""
        result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": test_organization_data
            }
        )

        assert result.get("success"), f"Failed to create organization: {result.get('error')}"
        assert "data" in result
        created_org = result["data"]
        assert created_org["name"] == test_organization_data["name"]
        assert "id" in created_org
        assert "created_at" in created_org

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_read_organization_hot(self, authenticated_client):
        """Test reading organization with real server integration."""
        # First create an organization
        create_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "Test Read Org", "type": "test"}
            }
        )

        assert create_result["success"]
        org_id = create_result["data"]["id"]

        # Then read it back
        result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": org_id
            }
        )

        assert result.get("success"), f"Failed to read organization: {result.get('error')}"
        assert "data" in result
        org = result["data"]
        assert org["id"] == org_id
        assert org["name"] == "Test Read Org"

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_update_organization_hot(self, authenticated_client):
        """Test updating organization with real server integration."""
        # First create an organization
        create_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "Original Name", "type": "test"}
            }
        )

        assert create_result["success"]
        org_id = create_result["data"]["id"]

        # Then update it
        update_data = {"name": "Updated Name", "description": "Updated description"}
        result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "id": org_id,
                "data": update_data
            }
        )

        assert result.get("success"), f"Failed to update organization: {result.get('error')}"
        assert "data" in result
        updated_org = result["data"]
        assert updated_org["name"] == "Updated Name"
        assert updated_org["description"] == "Updated description"

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_delete_organization_hot(self, authenticated_client):
        """Test deleting organization with real server integration."""
        # First create an organization
        create_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "To Be Deleted", "type": "test"}
            }
        )

        assert create_result["success"]
        org_id = create_result["data"]["id"]

        # Then delete it
        result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "delete",
                "id": org_id
            }
        )

        assert result.get("success"), f"Failed to delete organization: {result.get('error')}"

        # Verify it's deleted
        read_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": org_id
            }
        )
        assert not read_result.get("success")  # Should fail to read deleted org


# ============================================================================
# COLD Mode Tests - Unit Tests with Mocked Dependencies
# ============================================================================

@pytest.mark.cold
class TestEntityCOLDMode:
    """COLD mode tests with mocked dependencies for fast unit testing."""

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_list_organizations_cold(self, fastmcp_client):
        """Test listing organizations with mocked server."""
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        assert result.get("success"), f"Failed to list organizations: {result.get('error')}"
        assert "data" in result
        organizations = result["data"]
        assert isinstance(organizations, list)
        # In COLD mode, we get predictable mocked data
        assert len(organizations) == 2  # Mock returns exactly 2 organizations

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_create_organization_cold(self, fastmcp_client, test_organization_data):
        """Test creating organization with mocked server."""
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": test_organization_data
            }
        )

        assert result.get("success"), f"Failed to create organization: {result.get('error')}"
        assert "data" in result
        created_org = result["data"]
        assert created_org["name"] == test_organization_data["name"]
        assert "id" in created_org
        assert "created_at" in created_org

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_read_organization_cold(self, fastmcp_client):
        """Test reading organization with mocked server."""
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": "mock_org_1"
            }
        )

        assert result.get("success"), f"Failed to read organization: {result.get('error')}"
        assert "data" in result
        org = result["data"]
        assert org["id"] == "mock_org_1"
        assert "name" in org

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_update_organization_cold(self, fastmcp_client):
        """Test updating organization with mocked server."""
        update_data = {"name": "Updated Mock Org", "description": "Updated description"}
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "id": "mock_org_1",
                "data": update_data
            }
        )

        assert result.get("success"), f"Failed to update organization: {result.get('error')}"
        assert "data" in result
        updated_org = result["data"]
        assert updated_org["name"] == "Updated Mock Org"
        assert updated_org["description"] == "Updated description"

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_delete_organization_cold(self, fastmcp_client):
        """Test deleting organization with mocked server."""
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "delete",
                "id": "mock_org_1"
            }
        )

        assert result.get("success"), f"Failed to delete organization: {result.get('error')}"

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_performance(self, fastmcp_client):
        """Test that COLD mode operations complete within 2 seconds."""
        import time

        start_time = time.time()

        # Perform multiple operations
        for i in range(20):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "list"
                }
            )

        duration = time.time() - start_time
        assert duration < 2.0, f"COLD mode test took {duration:.2f}s (expected < 2s)"

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_parallel_execution(self, fastmcp_client):
        """Test that COLD mode supports parallel execution."""
        import asyncio

        # Run multiple operations concurrently
        tasks = [
            fastmcp_client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"}),
            fastmcp_client.call_tool("entity_tool", {"entity_type": "project", "operation": "list"}),
            fastmcp_client.call_tool("entity_tool", {"entity_type": "document", "operation": "list"}),
        ]

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        for result in results:
            assert result["success"], f"Parallel operation failed: {result.get('error')}"


# ============================================================================
# DRY Mode Tests - Fully Simulated Tests
# ============================================================================

@pytest.mark.dry
class TestEntityDRYMode:
    """DRY mode tests with full simulation for maximum speed and isolation."""

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_list_organizations_dry(self, fastmcp_client):
        """Test listing organizations with simulated server."""
        # First create some simulated organizations
        for i in range(5):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"Simulated Org {i}", "type": "test"}
                }
            )

        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        assert result.get("success"), f"Failed to list organizations: {result.get('error')}"
        assert "data" in result
        organizations = result["data"]
        assert isinstance(organizations, list)
        assert len(organizations) == 5  # We created 5 organizations

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_create_organization_dry(self, fastmcp_client, test_organization_data):
        """Test creating organization with simulated server."""
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": test_organization_data
            }
        )

        assert result.get("success"), f"Failed to create organization: {result.get('error')}"
        assert "data" in result
        created_org = result["data"]
        assert created_org["name"] == test_organization_data["name"]
        assert "id" in created_org
        assert "created_at" in created_org

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_crud_operations_dry(self, fastmcp_client):
        """Test full CRUD operations with simulation."""
        # Create
        create_result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {"name": "Test Org", "type": "enterprise"}
            }
        )
        assert create_result["success"]
        org_id = create_result["data"]["id"]

        # Read
        read_result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": org_id
            }
        )
        assert read_result["success"]
        assert read_result["data"]["name"] == "Test Org"

        # Update
        update_result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "update",
                "id": org_id,
                "data": {"name": "Updated Org", "status": "active"}
            }
        )
        assert update_result["success"]
        assert update_result["data"]["name"] == "Updated Org"
        assert update_result["data"]["status"] == "active"

        # Delete
        delete_result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "delete",
                "id": org_id
            }
        )
        assert delete_result["success"]

        # Verify deletion
        read_after_delete = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": org_id
            }
        )
        assert not read_after_delete["success"]
        assert read_after_delete["error"] == "not_found"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_performance(self, fastmcp_client):
        """Test that DRY mode operations complete within 1 second."""
        import time

        start_time = time.time()

        # Perform many operations
        for i in range(100):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"Perf Org {i}", "type": "test"}
                }
            )

        duration = time.time() - start_time
        assert duration < 1.0, f"DRY mode test took {duration:.2f}s (expected < 1s)"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_parallel_execution(self, fastmcp_client):
        """Test that DRY mode supports maximum parallelization."""
        import asyncio

        # Run many operations concurrently
        tasks = []
        for i in range(50):
            tasks.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "organization",
                        "operation": "create",
                        "data": {"name": f"Parallel Org {i}", "type": "test"}
                    }
                )
            )

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        for result in results:
            assert result["success"], f"Parallel operation failed: {result.get('error')}"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_simulated_workflow_dry(self, fastmcp_client):
        """Test simulated workflow operations."""
        # Create a workflow
        workflow_result = await fastmcp_client.call_tool(
            "workflow_tool",
            {
                "operation": "create",
                "name": "Test Workflow",
                "steps": ["validate", "process", "notify"]
            }
        )

        assert workflow_result["success"]
        assert workflow_result["data"]["name"] == "Test Workflow"
        assert len(workflow_result["data"]["steps"]) == 3

        # Execute the workflow
        execute_result = await fastmcp_client.call_tool(
            "workflow_tool",
            {
                "operation": "execute",
                "name": "Test Workflow",
                "steps": ["validate", "process", "notify"]
            }
        )

        assert execute_result["success"]
        assert execute_result["data"]["status"] == "completed"
        assert execute_result["data"]["steps_completed"] == 3

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_simulated_query_dry(self, fastmcp_client):
        """Test simulated query operations."""
        # Create some entities first
        for i in range(3):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {"title": f"Test Document {i}", "content": f"Content {i}"}
                }
            )

        # Search for documents
        query_result = await fastmcp_client.call_tool(
            "query_tool",
            {
                "operation": "search",
                "query": "Test Document",
                "filters": {"type": "document"}
            }
        )

        assert query_result["success"]
        assert "results" in query_result["data"]
        assert len(query_result["data"]["results"]) == 3


# ============================================================================
# Cross-Mode Validation Tests
# ============================================================================

class TestCrossModeValidation:
    """Tests that validate behavior consistency across modes."""

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_hot_mode_real_data_validation(self, authenticated_client):
        """Validate that HOT mode uses real data."""
        result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        # In HOT mode, we should get real data structure
        assert result.get("success")
        assert "data" in result
        # Real data might be empty or populated, but structure should be consistent
        assert isinstance(result["data"], list)

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_mock_data_validation(self, fastmcp_client):
        """Validate that COLD mode uses predictable mock data."""
        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        # In COLD mode, we should get predictable mock data
        assert result.get("success")
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2  # Mock always returns 2 items

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_simulation_validation(self, fastmcp_client):
        """Validate that DRY mode uses full simulation."""
        # Create entities in simulation
        for i in range(3):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"Sim Org {i}"}
                }
            )

        result = await fastmcp_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "list"
            }
        )

        # In DRY mode, we should get simulated data that we created
        assert result.get("success")
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 3  # We created exactly 3 entities


# ============================================================================
# Performance and Reliability Tests
# ============================================================================

@pytest.mark.cold
class TestPerformanceCOLD:
    """Performance tests for COLD mode."""

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_batch_operations(self, fastmcp_client):
        """Test batch operations in COLD mode."""
        import time

        start_time = time.time()

        # Perform batch operations
        for i in range(50):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"Batch Org {i}", "type": "test"}
                }
            )

        duration = time.time() - start_time
        assert duration < 2.0, f"Batch operations took {duration:.2f}s (expected < 2s)"


@pytest.mark.dry
class TestPerformanceDRY:
    """Performance tests for DRY mode."""

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_massive_operations(self, fastmcp_client):
        """Test massive operations in DRY mode."""
        import time

        start_time = time.time()

        # Perform massive operations
        for i in range(500):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {"title": f"Massive Doc {i}", "content": f"Content {i}"}
                }
            )

        duration = time.time() - start_time
        assert duration < 1.0, f"Massive operations took {duration:.2f}s (expected < 1s)"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_concurrent_operations(self, fastmcp_client):
        """Test concurrent operations in DRY mode."""
        import asyncio
        import time

        start_time = time.time()

        # Run 100 concurrent operations
        tasks = []
        for i in range(100):
            tasks.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "organization",
                        "operation": "create",
                        "data": {"name": f"Concurrent Org {i}", "type": "test"}
                    }
                )
            )

        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # All operations should succeed
        for result in results:
            assert result["success"]

        # Should complete very quickly due to simulation
        assert duration < 1.0, f"Concurrent operations took {duration:.2f}s (expected < 1s)"
