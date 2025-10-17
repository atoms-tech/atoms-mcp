"""Example tests demonstrating test mode usage.

This file shows how to use test modes (HOT/COLD/DRY) for
different levels of test isolation and speed.

Run with:
    pytest tests/examples/test_modes_example.py -v --mode hot
    pytest tests/examples/test_modes_example.py -v --mode cold
    pytest tests/examples/test_modes_example.py -v --mode dry
"""

import pytest


@pytest.mark.hot
class TestIntegrationHOT:
    """Tests that run in HOT mode (real dependencies)."""

    @pytest.mark.hot
    async def test_real_server_integration(self, mcp_client):
        """Test with real MCP server and database.

        This test runs only in HOT mode and requires:
        - Real MCP server running
        - Real database (Supabase)
        - Network connectivity
        """
        # Use real client
        result = await mcp_client.list_tools()
        assert result.get("result") is not None

    @pytest.mark.hot
    async def test_entity_creation_hot(self, fast_http_client):
        """Test real entity creation in HOT mode."""
        result = await fast_http_client.call_tool("entity_tool", {
            "operation": "list",
            "entity_type": "document"
        })
        assert result.get("success")


@pytest.mark.cold
class TestUnitCOLD:
    """Tests that run in COLD mode (mocked dependencies)."""

    @pytest.mark.cold
    async def test_mock_client(self, conditional_mcp_client):
        """Test with mocked MCP client.

        In COLD mode:
        - No real server required
        - Uses in-memory mocks
        - Very fast execution (< 2s)
        - Can run in parallel
        """
        # Mock client responds predictably
        result = await conditional_mcp_client.list_tools()
        assert result.get("result") is not None

    @pytest.mark.cold
    async def test_logic_only(self, conditional_http_client):
        """Test application logic without external dependencies."""
        # Mocked HTTP client
        result = await conditional_http_client.call_tool("workspace_tool", {
            "operation": "create",
            "entity_type": "organization",
            "data": {"name": "Test Org"}
        })
        assert result["success"]


@pytest.mark.dry
class TestSimulatedDRY:
    """Tests that run in DRY mode (fully simulated)."""

    @pytest.mark.dry
    async def test_simulated_flow(self, conditional_mcp_client):
        """Test with fully simulated client.

        In DRY mode:
        - Everything is simulated
        - No external dependencies at all
        - Fastest execution (< 1s)
        - Maximum parallelization
        - Best for CI/CD pipelines
        """
        # Simulated client with in-memory storage
        result = await conditional_mcp_client.list_tools()
        assert result.get("result") is not None

        # Perform CRUD operations on simulated data
        create_result = await conditional_mcp_client.call_tool(
            "entity_tool", {"operation": "create", "entity_type": "document"}
        )
        assert create_result["success"]

        # Read from simulated storage
        read_result = await conditional_mcp_client.call_tool(
            "entity_tool", {"operation": "read", "id": create_result["id"]}
        )
        assert read_result["success"]


# Tests without explicit mode markers (defaults)
class TestDefaultMode:
    """Tests without explicit mode markers use default mode."""

    async def test_default_creates_org(self, atoms_test_mode):
        """Test with default mode (HOT by default)."""
        # This test will run in HOT mode by default
        # unless --mode flag is specified
        assert atoms_test_mode.value in ["hot", "cold", "dry"]

    async def test_mode_aware_fixtures(self, atoms_mode_config):
        """Test demonstrating mode-aware fixture behavior."""
        # Fixture adapts based on current mode
        if atoms_mode_config.mode.value == "hot":
            # Real dependencies
            assert atoms_mode_config.use_real_server
            assert atoms_mode_config.use_real_database
        elif atoms_mode_config.mode.value == "cold":
            # Mocked dependencies
            assert atoms_mode_config.use_mocks
            assert not atoms_mode_config.use_real_server
        elif atoms_mode_config.mode.value == "dry":
            # Simulated only
            assert atoms_mode_config.use_simulation
            assert not atoms_mode_config.use_real_server


@pytest.mark.hot
@pytest.mark.integration
class TestCascadeAcrossModes:
    """Example showing cascade patterns across modes."""

    async def test_hot_create(self, store_result):
        """Create in HOT mode."""
        result = {"id": "hot_org_123", "success": True}
        store_result("test_hot_create", True, result)

    @pytest.mark.depends_on("test_hot_create")
    async def test_hot_read(self, store_result, test_results):
        """Read in HOT mode."""
        create_result = test_results.get_result("test_hot_create")
        assert create_result.passed
        store_result("test_hot_read", True)


@pytest.mark.cold
class TestModeIsolation:
    """Tests demonstrating mode isolation and independence."""

    async def test_cold_independent_1(self):
        """COLD test 1 - can run independently."""
        # This test doesn't depend on others
        assert True

    async def test_cold_independent_2(self):
        """COLD test 2 - can run independently."""
        # This test doesn't depend on others
        assert True

    async def test_cold_independent_3(self):
        """COLD test 3 - can run independently."""
        # In COLD mode, all these can run in parallel
        assert True


@pytest.mark.dry
class TestDryModePerformance:
    """Tests demonstrating DRY mode performance characteristics."""

    async def test_dry_very_fast(self, conditional_mcp_client):
        """DRY mode test should complete in < 1 second."""
        import time
        start = time.time()

        # Simulate multiple operations
        for i in range(10):
            await conditional_mcp_client.call_tool(
                "entity_tool",
                {"operation": "create", "entity_type": "document"}
            )

        duration = time.time() - start
        # In DRY mode, this should be very fast
        assert duration < 1.0, f"DRY test took {duration:.2f}s (expected < 1s)"

    async def test_dry_many_items(self, conditional_mcp_client):
        """DRY mode can handle large datasets efficiently."""
        # Create many simulated entities
        for i in range(100):
            result = await conditional_mcp_client.call_tool(
                "entity_tool",
                {"operation": "create", "entity_type": "document", "index": i}
            )
            assert result["success"]


# Configuration examples
@pytest.mark.skip(reason="Configuration example only")
class TestModeConfiguration:
    """Examples of how different modes are configured."""

    def test_hot_mode_config(self, atoms_mode_config):
        """HOT mode configuration."""
        if atoms_mode_config.mode.value == "hot":
            # HOT mode settings
            assert atoms_mode_config.use_real_server
            assert atoms_mode_config.use_real_database
            assert not atoms_mode_config.use_mocks
            assert not atoms_mode_config.use_simulation
            assert atoms_mode_config.max_duration_seconds == 30.0
            assert atoms_mode_config.parallel_execution is False

    def test_cold_mode_config(self, atoms_mode_config):
        """COLD mode configuration."""
        if atoms_mode_config.mode.value == "cold":
            # COLD mode settings
            assert not atoms_mode_config.use_real_server
            assert not atoms_mode_config.use_real_database
            assert atoms_mode_config.use_mocks
            assert not atoms_mode_config.use_simulation
            assert atoms_mode_config.max_duration_seconds == 2.0
            assert atoms_mode_config.parallel_execution is True

    def test_dry_mode_config(self, atoms_mode_config):
        """DRY mode configuration."""
        if atoms_mode_config.mode.value == "dry":
            # DRY mode settings
            assert not atoms_mode_config.use_real_server
            assert not atoms_mode_config.use_real_database
            assert not atoms_mode_config.use_mocks
            assert atoms_mode_config.use_simulation
            assert atoms_mode_config.max_duration_seconds == 1.0
            assert atoms_mode_config.parallel_execution is True


__all__ = [
    "TestIntegrationHOT",
    "TestUnitCOLD",
    "TestSimulatedDRY",
    "TestDefaultMode",
    "TestCascadeAcrossModes",
    "TestModeIsolation",
    "TestDryModePerformance",
    "TestModeConfiguration",
]
