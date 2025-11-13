"""Fixtures for performance tests.

Provides:
- load_generator: Generate concurrent load
- timing_tracker: Track and report timing metrics
- metrics_collector: Collect performance metrics
"""

import pytest
import time
import statistics
from typing import Dict, List, Callable, Any
from contextlib import contextmanager


@pytest.fixture
def load_generator():
    """Generate load for performance testing."""
    async def generate_requests(count: int, request_func: Callable) -> List[Any]:
        """Generate 'count' concurrent requests using request_func."""
        import asyncio
        tasks = [request_func() for _ in range(count)]
        return await asyncio.gather(*tasks)

    return generate_requests


@pytest.fixture
def timing_tracker():
    """Track and report timing metrics.
    
    Usage:
        async def test_performance(timing_tracker):
            with timing_tracker.measure("entity_creation"):
                result = await client.call_tool(...)
            
            timing_tracker.report()  # Prints timing stats
    """
    class TimingTracker:
        def __init__(self):
            self.timings: Dict[str, List[float]] = {}

        @contextmanager
        def measure(self, name: str):
            """Context manager to measure execution time."""
            start = time.perf_counter()
            try:
                yield
            finally:
                elapsed = time.perf_counter() - start
                if name not in self.timings:
                    self.timings[name] = []
                self.timings[name].append(elapsed)

        def report(self) -> Dict[str, Dict[str, float]]:
            """Generate timing report with statistics."""
            results = {}
            for name, times in self.timings.items():
                if times:
                    results[name] = {
                        "min": min(times),
                        "max": max(times),
                        "avg": statistics.mean(times),
                        "median": statistics.median(times),
                        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                        "count": len(times),
                    }
            return results

        def get_stats(self, name: str) -> Dict[str, float]:
            """Get stats for a specific measurement."""
            times = self.timings.get(name, [])
            if not times:
                return {}
            return {
                "min": min(times),
                "max": max(times),
                "avg": statistics.mean(times),
                "median": statistics.median(times),
                "count": len(times),
            }

    return TimingTracker()


@pytest.fixture
def metrics_collector():
    """Collect performance metrics.
    
    Usage:
        def test_performance(metrics_collector):
            start = time.time()
            # Do work
            metrics_collector.record("response_time", time.time() - start)
    """
    class MetricsCollector:
        def __init__(self):
            self.metrics: Dict[str, List[float]] = {}
            self.counters: Dict[str, int] = {}

        def record(self, name: str, value: float):
            """Record a metric value."""
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)

        def increment(self, counter_name: str, amount: int = 1):
            """Increment a counter."""
            if counter_name not in self.counters:
                self.counters[counter_name] = 0
            self.counters[counter_name] += amount

        def get_stats(self, name: str) -> Dict[str, Any]:
            """Get statistics for a metric."""
            values = self.metrics.get(name, [])
            if not values:
                return {}

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "median": statistics.median(values),
                "sum": sum(values),
            }

        def get_counter(self, name: str) -> int:
            """Get counter value."""
            return self.counters.get(name, 0)

        def report(self) -> Dict[str, Any]:
            """Generate full metrics report."""
            return {
                "metrics": {name: self.get_stats(name) for name in self.metrics},
                "counters": self.counters,
            }

    return MetricsCollector()


@pytest.fixture
def performance_baseline() -> Dict[str, Dict[str, float]]:
    """Performance baseline thresholds."""
    return {
        "entity_create": {"max_ms": 100, "avg_ms": 50},
        "entity_read": {"max_ms": 50, "avg_ms": 25},
        "entity_update": {"max_ms": 100, "avg_ms": 50},
        "entity_delete": {"max_ms": 50, "avg_ms": 25},
        "entity_list": {"max_ms": 200, "avg_ms": 100},
        "entity_search": {"max_ms": 500, "avg_ms": 300},
        "workflow_execute": {"max_ms": 1000, "avg_ms": 500},
        "query_search": {"max_ms": 500, "avg_ms": 300},
    }


@pytest.fixture
def load_test_scenarios() -> List[Dict[str, Any]]:
    """Load testing scenarios."""
    return [
        {"name": "normal", "requests": 10, "concurrent": 1, "duration_seconds": 10},
        {"name": "moderate", "requests": 100, "concurrent": 5, "duration_seconds": 30},
        {"name": "high", "requests": 1000, "concurrent": 20, "duration_seconds": 60},
        {"name": "stress", "requests": 5000, "concurrent": 50, "duration_seconds": 120},
    ]


@pytest.fixture
def concurrent_access_scenarios() -> List[Dict[str, Any]]:
    """Concurrent access test scenarios."""
    return [
        {"name": "read_heavy", "read_ratio": 0.9, "write_ratio": 0.1, "concurrency": 10},
        {"name": "write_heavy", "read_ratio": 0.3, "write_ratio": 0.7, "concurrency": 5},
        {"name": "balanced", "read_ratio": 0.5, "write_ratio": 0.5, "concurrency": 10},
    ]
