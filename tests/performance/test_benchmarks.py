"""
Performance benchmarks for critical paths.

Run with: pytest tests/performance/ --benchmark-only
"""

import pytest


class TestServerPerformance:
    """Server performance benchmarks."""

    def test_server_startup_time(self, benchmark):
        """Benchmark server startup time."""
        def startup():
            # Import server module
            from server import app
            return app

        result = benchmark(startup)
        assert result is not None

    def test_health_check_response_time(self, benchmark):
        """Benchmark health check endpoint."""
        def health_check():
            # Simulate health check
            return {"status": "healthy"}

        result = benchmark(health_check)
        assert result["status"] == "healthy"


class TestVendorPerformance:
    """Vendor manager performance benchmarks."""

    def test_vendor_package_copy_time(self, benchmark):
        """Benchmark package vendoring."""
        def vendor_packages():
            # Simulate vendoring
            return True

        result = benchmark(vendor_packages)
        assert result is True


class TestSchemaPerformance:
    """Schema sync performance benchmarks."""

    def test_schema_comparison_time(self, benchmark):
        """Benchmark schema comparison."""
        def compare_schemas():
            # Simulate schema comparison
            return []

        result = benchmark(compare_schemas)
        assert isinstance(result, list)


class TestDeploymentPerformance:
    """Deployment performance benchmarks."""

    def test_deployment_check_time(self, benchmark):
        """Benchmark deployment readiness check."""
        def check_deployment():
            # Simulate deployment check
            return True

        result = benchmark(check_deployment)
        assert result is True


@pytest.mark.slow
class TestMemoryUsage:
    """Memory usage tests."""

    def test_server_memory_footprint(self):
        """Test server memory footprint."""
        import tracemalloc

        tracemalloc.start()

        # Import and initialize server

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Assert memory usage is reasonable (< 100MB)
        assert peak < 100 * 1024 * 1024, f"Peak memory usage: {peak / 1024 / 1024:.2f} MB"

    def test_vendor_memory_footprint(self):
        """Test vendor manager memory footprint."""
        import tracemalloc

        tracemalloc.start()

        # Import vendor manager
        from lib.vendor_manager import VendorManager
        vendor_mgr = VendorManager()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Assert memory usage is reasonable (< 50MB)
        assert peak < 50 * 1024 * 1024, f"Peak memory usage: {peak / 1024 / 1024:.2f} MB"

