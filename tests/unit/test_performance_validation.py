"""
Performance Validation Tests for Test Modes

This module validates that test modes meet their performance requirements:
- HOT mode: Integration tests can take up to 30 seconds
- COLD mode: Unit tests must complete within 2 seconds
- DRY mode: Simulated tests must complete within 1 second

These tests ensure the test mode framework maintains performance guarantees.
"""

import asyncio
import time

import pytest


@pytest.mark.hot
class TestHOTModePerformance:
    """Performance validation for HOT mode (integration tests)."""

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_hot_mode_max_duration(self, authenticated_client):
        """Test that HOT mode operations complete within 30 seconds."""
        start_time = time.time()

        # Perform multiple real server operations
        operations = []
        for i in range(10):
            operations.append(
                authenticated_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "organization",
                        "operation": "list"
                    }
                )
            )

        # Execute all operations
        results = await asyncio.gather(*operations)

        duration = time.time() - start_time

        # HOT mode allows up to 30 seconds
        assert duration < 30.0, f"HOT mode test took {duration:.2f}s (expected < 30s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"Operation failed: {result.get('error')}"

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_hot_mode_real_integration(self, authenticated_client):
        """Test that HOT mode performs real integration operations."""
        # Create a real entity
        create_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "create",
                "data": {
                    "name": "Performance Test Org",
                    "type": "test",
                    "description": "Created for performance testing"
                }
            }
        )

        assert create_result.get("success"), f"Failed to create organization: {create_result.get('error')}"
        org_id = create_result["data"]["id"]

        # Read it back (real database operation)
        read_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "read",
                "id": org_id
            }
        )

        assert read_result.get("success"), f"Failed to read organization: {read_result.get('error')}"
        assert read_result["data"]["name"] == "Performance Test Org"

        # Clean up
        delete_result = await authenticated_client.call_tool(
            "entity_tool",
            {
                "entity_type": "organization",
                "operation": "delete",
                "id": org_id
            }
        )

        assert delete_result.get("success"), f"Failed to delete organization: {delete_result.get('error')}"


@pytest.mark.cold
class TestCOLDModePerformance:
    """Performance validation for COLD mode (unit tests with mocks)."""

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_max_duration(self, fastmcp_client):
        """Test that COLD mode operations complete within 2 seconds."""
        start_time = time.time()

        # Perform many mocked operations
        operations = []
        for i in range(100):
            operations.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "organization",
                        "operation": "list"
                    }
                )
            )

        # Execute all operations
        results = await asyncio.gather(*operations)

        duration = time.time() - start_time

        # COLD mode must complete within 2 seconds
        assert duration < 2.0, f"COLD mode test took {duration:.2f}s (expected < 2s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"Operation failed: {result.get('error')}"

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_parallel_execution(self, fastmcp_client):
        """Test that COLD mode supports parallel execution."""
        start_time = time.time()

        # Run many operations in parallel
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
        duration = time.time() - start_time

        # Should complete quickly due to mocking
        assert duration < 2.0, f"Parallel operations took {duration:.2f}s (expected < 2s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"Parallel operation failed: {result.get('error')}"

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_mock_consistency(self, fastmcp_client):
        """Test that COLD mode provides consistent mock responses."""
        # Multiple calls should return consistent results
        results = []
        for i in range(10):
            result = await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "list"
                }
            )
            results.append(result)

        # All results should be identical (mocked)
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result, "Mock responses should be consistent"


@pytest.mark.dry
class TestDRYModePerformance:
    """Performance validation for DRY mode (simulated tests)."""

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_max_duration(self, fastmcp_client):
        """Test that DRY mode operations complete within 1 second."""
        start_time = time.time()

        # Perform many simulated operations
        operations = []
        for i in range(500):
            operations.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "organization",
                        "operation": "create",
                        "data": {"name": f"Sim Org {i}", "type": "test"}
                    }
                )
            )

        # Execute all operations
        results = await asyncio.gather(*operations)

        duration = time.time() - start_time

        # DRY mode must complete within 1 second
        assert duration < 1.0, f"DRY mode test took {duration:.2f}s (expected < 1s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"Operation failed: {result.get('error')}"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_massive_parallel_execution(self, fastmcp_client):
        """Test that DRY mode supports massive parallel execution."""
        start_time = time.time()

        # Run massive parallel operations
        tasks = []
        for i in range(200):
            tasks.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "document",
                        "operation": "create",
                        "data": {"title": f"Massive Doc {i}", "content": f"Content {i}"}
                    }
                )
            )

        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # Should complete very quickly due to simulation
        assert duration < 1.0, f"Massive parallel operations took {duration:.2f}s (expected < 1s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"Massive parallel operation failed: {result.get('error')}"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_simulation_accuracy(self, fastmcp_client):
        """Test that DRY mode simulation maintains data accuracy."""
        # Create entities with specific data
        created_entities = []
        for i in range(10):
            result = await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {
                        "name": f"Accuracy Test Org {i}",
                        "type": "test",
                        "index": i,
                        "description": f"Test organization {i}"
                    }
                }
            )
            assert result.get("success")
            created_entities.append(result["data"]["id"])

        # Verify all entities exist and have correct data
        for i, entity_id in enumerate(created_entities):
            result = await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "read",
                    "id": entity_id
                }
            )
            assert result.get("success")
            entity = result["data"]
            assert entity["name"] == f"Accuracy Test Org {i}"
            assert entity["index"] == i
            assert entity["description"] == f"Test organization {i}"


# ============================================================================
# Cross-Mode Performance Comparison
# ============================================================================

class TestPerformanceComparison:
    """Compare performance characteristics across test modes."""

    @pytest.mark.hot
    @pytest.mark.asyncio
    async def test_hot_mode_realistic_timing(self, authenticated_client):
        """Test that HOT mode has realistic timing for integration tests."""
        start_time = time.time()

        # Perform realistic integration operations
        operations = [
            authenticated_client.call_tool("entity_tool", {"entity_type": "organization", "operation": "list"}),
            authenticated_client.call_tool("entity_tool", {"entity_type": "project", "operation": "list"}),
            authenticated_client.call_tool("entity_tool", {"entity_type": "document", "operation": "list"}),
        ]

        results = await asyncio.gather(*operations)
        duration = time.time() - start_time

        # HOT mode should take some time due to real network/database operations
        # But not too long (under 30s as per config)
        assert 0.1 < duration < 30.0, f"HOT mode took {duration:.2f}s (expected 0.1s < duration < 30s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"HOT operation failed: {result.get('error')}"

    @pytest.mark.cold
    @pytest.mark.asyncio
    async def test_cold_mode_fast_timing(self, fastmcp_client):
        """Test that COLD mode is fast due to mocking."""
        start_time = time.time()

        # Perform many mocked operations
        operations = []
        for i in range(50):
            operations.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {"entity_type": "organization", "operation": "list"}
                )
            )

        results = await asyncio.gather(*operations)
        duration = time.time() - start_time

        # COLD mode should be fast due to mocking
        assert duration < 2.0, f"COLD mode took {duration:.2f}s (expected < 2s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"COLD operation failed: {result.get('error')}"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_ultra_fast_timing(self, fastmcp_client):
        """Test that DRY mode is ultra-fast due to simulation."""
        start_time = time.time()

        # Perform many simulated operations
        operations = []
        for i in range(200):
            operations.append(
                fastmcp_client.call_tool(
                    "entity_tool",
                    {
                        "entity_type": "organization",
                        "operation": "create",
                        "data": {"name": f"Ultra Fast Org {i}", "type": "test"}
                    }
                )
            )

        results = await asyncio.gather(*operations)
        duration = time.time() - start_time

        # DRY mode should be ultra-fast due to simulation
        assert duration < 1.0, f"DRY mode took {duration:.2f}s (expected < 1s)"

        # All operations should succeed
        for result in results:
            assert result.get("success"), f"DRY operation failed: {result.get('error')}"


# ============================================================================
# Memory and Resource Usage Tests
# ============================================================================

@pytest.mark.dry
class TestResourceUsageDRY:
    """Test resource usage in DRY mode (should be minimal)."""

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_memory_efficiency(self, fastmcp_client):
        """Test that DRY mode is memory efficient."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform many simulated operations
        for i in range(1000):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "document",
                    "operation": "create",
                    "data": {
                        "title": f"Memory Test Doc {i}",
                        "content": f"Content {i}" * 100  # Large content
                    }
                }
            )

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (under 100MB)
        assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB (expected < 100MB)"

    @pytest.mark.dry
    @pytest.mark.asyncio
    async def test_dry_mode_cpu_efficiency(self, fastmcp_client):
        """Test that DRY mode is CPU efficient."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Perform many operations while monitoring CPU
        start_time = time.time()
        cpu_times = []

        for i in range(500):
            await fastmcp_client.call_tool(
                "entity_tool",
                {
                    "entity_type": "organization",
                    "operation": "create",
                    "data": {"name": f"CPU Test Org {i}", "type": "test"}
                }
            )

            # Sample CPU usage every 50 operations
            if i % 50 == 0:
                cpu_times.append(process.cpu_percent())

        duration = time.time() - start_time

        # Should complete quickly
        assert duration < 1.0, f"CPU test took {duration:.2f}s (expected < 1s)"

        # Average CPU usage should be reasonable
        avg_cpu = sum(cpu_times) / len(cpu_times) if cpu_times else 0
        assert avg_cpu < 50.0, f"Average CPU usage was {avg_cpu:.1f}% (expected < 50%)"
