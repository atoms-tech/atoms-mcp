"""Unit tests for Phase 3 Week 2: Performance Metrics.

Tests performance tracking, metrics collection, and analytics.
"""

import pytest
import time
from services.performance_metrics import get_performance_metrics


class TestPerformanceMetricsPhase3:
    """Test Phase 3 performance metrics."""

    @pytest.fixture
    def metrics(self):
        """Get performance metrics instance."""
        m = get_performance_metrics()
        m.clear_metrics()
        return m

    # ========== Operation Timing Tests ==========

    def test_start_operation(self, metrics):
        """Test starting operation timing."""
        metrics.start_operation("op-1")
        assert "op-1" in metrics.operation_timings

    def test_end_operation(self, metrics):
        """Test ending operation timing."""
        metrics.start_operation("op-1")
        time.sleep(0.01)  # 10ms

        result = metrics.end_operation("op-1", "create_entity")

        assert result["operation_id"] == "op-1"
        assert result["operation_type"] == "create_entity"
        assert result["duration_ms"] >= 10
        assert result["success"] is True

    def test_end_operation_not_started(self, metrics):
        """Test ending operation that wasn't started."""
        result = metrics.end_operation("op-999", "create_entity")

        assert "error" in result

    def test_end_operation_with_metadata(self, metrics):
        """Test ending operation with metadata."""
        metrics.start_operation("op-1")
        metadata = {"entity_type": "requirement", "count": 5}

        result = metrics.end_operation(
            "op-1",
            "create_entity",
            metadata=metadata
        )

        assert result["metadata"] == metadata

    def test_end_operation_failure(self, metrics):
        """Test recording failed operation."""
        metrics.start_operation("op-1")

        result = metrics.end_operation(
            "op-1",
            "create_entity",
            success=False
        )

        assert result["success"] is False

    # ========== Metrics Recording Tests ==========

    def test_record_metric(self, metrics):
        """Test recording metric directly."""
        metrics.record_metric("search_entity", 45.5, success=True)

        recorded = metrics.get_metrics("search_entity")
        assert len(recorded) == 1
        assert recorded[0]["duration_ms"] == 45.5

    def test_get_metrics(self, metrics):
        """Test getting recorded metrics."""
        metrics.record_metric("create_entity", 10.0)
        metrics.record_metric("create_entity", 15.0)
        metrics.record_metric("search_entity", 20.0)

        create_metrics = metrics.get_metrics("create_entity")
        assert len(create_metrics) == 2

    def test_get_metrics_all(self, metrics):
        """Test getting all metrics."""
        metrics.record_metric("create_entity", 10.0)
        metrics.record_metric("search_entity", 20.0)
        metrics.record_metric("update_entity", 15.0)

        all_metrics = metrics.get_metrics()
        assert len(all_metrics) == 3

    def test_get_metrics_limit(self, metrics):
        """Test metrics limit."""
        for i in range(10):
            metrics.record_metric("create_entity", float(i))

        limited = metrics.get_metrics("create_entity", limit=5)
        assert len(limited) == 5

    # ========== Statistics Tests ==========

    def test_get_statistics(self, metrics):
        """Test getting statistics."""
        metrics.record_metric("create_entity", 10.0, success=True)
        metrics.record_metric("create_entity", 20.0, success=True)
        metrics.record_metric("create_entity", 30.0, success=False)

        stats = metrics.get_statistics("create_entity")

        assert stats["count"] == 3
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 1
        assert stats["success_rate"] == 2/3
        assert stats["avg_duration_ms"] == 20.0
        assert stats["min_duration_ms"] == 10.0
        assert stats["max_duration_ms"] == 30.0

    def test_get_statistics_percentiles(self, metrics):
        """Test statistics percentiles."""
        for i in range(1, 101):
            metrics.record_metric("search_entity", float(i))

        stats = metrics.get_statistics("search_entity")

        assert "p50_duration_ms" in stats
        assert "p95_duration_ms" in stats
        assert "p99_duration_ms" in stats

    def test_get_statistics_empty(self, metrics):
        """Test statistics for empty metrics."""
        stats = metrics.get_statistics("nonexistent")

        assert stats["count"] == 0
        assert stats["success_count"] == 0
        assert stats["failure_count"] == 0
        assert stats["avg_duration_ms"] == 0

    # ========== Operation Types Tests ==========

    def test_get_operation_types(self, metrics):
        """Test getting operation types."""
        metrics.record_metric("create_entity", 10.0)
        metrics.record_metric("search_entity", 20.0)
        metrics.record_metric("update_entity", 15.0)

        types = metrics.get_operation_types()

        assert len(types) == 3
        assert "create_entity" in types
        assert "search_entity" in types
        assert "update_entity" in types

    # ========== Summary Tests ==========

    def test_get_summary(self, metrics):
        """Test getting metrics summary."""
        metrics.record_metric("create_entity", 10.0)
        metrics.record_metric("search_entity", 20.0)

        summary = metrics.get_summary()

        assert "timestamp" in summary
        assert "operation_types" in summary
        assert "total_operations" in summary
        assert "operations" in summary
        assert summary["operation_types"] == 2
        assert summary["total_operations"] == 2

    # ========== Cleanup Tests ==========

    def test_clear_metrics(self, metrics):
        """Test clearing metrics."""
        metrics.record_metric("create_entity", 10.0)
        metrics.record_metric("search_entity", 20.0)

        assert len(metrics.get_operation_types()) == 2

        metrics.clear_metrics()

        assert len(metrics.get_operation_types()) == 0
        assert len(metrics.get_metrics()) == 0

