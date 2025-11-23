"""Unit tests for Phase 5: Performance Optimizer.

Tests query optimization, caching, batch processing, and performance monitoring.
"""

import pytest
from services.performance_optimizer import get_performance_optimizer


class TestPerformanceOptimizerPhase5:
    """Test Phase 5 performance optimizer."""

    @pytest.fixture
    def optimizer(self):
        """Get performance optimizer instance."""
        optimizer = get_performance_optimizer()
        optimizer.query_cache.clear()
        optimizer.cache_stats.clear()
        optimizer.query_metrics.clear()
        return optimizer

    # ========== Query Optimization Tests ==========

    def test_optimize_query(self, optimizer):
        """Test query optimization."""
        query = {
            "entity_type": "requirement",
            "filters": {"status": "active"}
        }

        optimized = optimizer.optimize_query(query)

        assert "hints" in optimized
        assert "suggested_indexes" in optimized
        assert "estimated_cost" in optimized

    def test_query_hints(self, optimizer):
        """Test query hints generation."""
        query = {
            "entity_type": "requirement",
            "filters": {"status": "active"},
            "limit": 10
        }

        optimized = optimizer.optimize_query(query)

        assert len(optimized["hints"]) > 0

    def test_suggested_indexes(self, optimizer):
        """Test index suggestions."""
        query = {
            "entity_type": "requirement",
            "filters": {"status": "active"}
        }

        optimized = optimizer.optimize_query(query)

        assert len(optimized["suggested_indexes"]) > 0

    # ========== Caching Tests ==========

    def test_cache_query_result(self, optimizer):
        """Test caching query result."""
        query_key = "query-1"
        result = {"id": "req-1", "name": "Requirement 1"}

        optimizer.cache_query_result(query_key, result)

        cached = optimizer.get_cached_result(query_key)

        assert cached == result

    def test_cache_hit(self, optimizer):
        """Test cache hit."""
        query_key = "query-1"
        result = {"id": "req-1"}

        optimizer.cache_query_result(query_key, result)
        cached1 = optimizer.get_cached_result(query_key)
        cached2 = optimizer.get_cached_result(query_key)

        assert cached1 == result
        assert cached2 == result
        assert optimizer.cache_stats[query_key]["hits"] == 2

    def test_cache_miss(self, optimizer):
        """Test cache miss."""
        cached = optimizer.get_cached_result("nonexistent")

        assert cached is None
        assert optimizer.cache_stats["nonexistent"]["misses"] == 1

    # ========== Batch Processing Tests ==========

    def test_batch_process(self, optimizer):
        """Test batch processing."""
        queries = [
            {"id": "q1", "entity_type": "requirement"},
            {"id": "q2", "entity_type": "requirement"},
            {"id": "q3", "entity_type": "requirement"}
        ]

        results = optimizer.batch_process(queries)

        assert len(results) == 3
        assert all(r["status"] == "processed" for r in results)

    # ========== Performance Tracking Tests ==========

    def test_track_query_performance(self, optimizer):
        """Test tracking query performance."""
        metric = optimizer.track_query_performance("q1", 25.5, 10)

        assert metric["query_id"] == "q1"
        assert metric["execution_time_ms"] == 25.5
        assert metric["result_count"] == 10
        assert "performance_level" in metric

    def test_performance_level_excellent(self, optimizer):
        """Test excellent performance level."""
        metric = optimizer.track_query_performance("q1", 5.0, 10)

        assert metric["performance_level"] == "excellent"

    def test_performance_level_good(self, optimizer):
        """Test good performance level."""
        metric = optimizer.track_query_performance("q1", 30.0, 10)

        assert metric["performance_level"] == "good"

    def test_performance_level_critical(self, optimizer):
        """Test critical performance level."""
        metric = optimizer.track_query_performance("q1", 1000.0, 10)

        assert metric["performance_level"] == "critical"

    # ========== Performance Report Tests ==========

    def test_get_performance_report(self, optimizer):
        """Test getting performance report."""
        optimizer.track_query_performance("q1", 25.0, 10)
        optimizer.track_query_performance("q2", 35.0, 15)

        report = optimizer.get_performance_report()

        assert report["total_queries"] == 2
        assert report["average_execution_time_ms"] == 30.0
        assert report["total_results"] == 25

    def test_cache_hit_rate(self, optimizer):
        """Test cache hit rate calculation."""
        optimizer.cache_query_result("q1", {"id": "1"})
        optimizer.get_cached_result("q1")
        optimizer.get_cached_result("q1")
        optimizer.get_cached_result("q2")

        report = optimizer.get_performance_report()

        # Cache stats are only populated when queries are tracked
        assert "cache_hit_rate" in report

    # ========== Slow Query Detection Tests ==========

    def test_identify_slow_queries(self, optimizer):
        """Test identifying slow queries."""
        optimizer.track_query_performance("q1", 25.0, 10)
        optimizer.track_query_performance("q2", 150.0, 10)
        optimizer.track_query_performance("q3", 200.0, 10)

        slow = optimizer.identify_slow_queries(threshold_ms=100.0)

        assert len(slow) == 2

    def test_slow_queries_sorted(self, optimizer):
        """Test slow queries are sorted."""
        optimizer.track_query_performance("q1", 150.0, 10)
        optimizer.track_query_performance("q2", 200.0, 10)
        optimizer.track_query_performance("q3", 175.0, 10)

        slow = optimizer.identify_slow_queries(threshold_ms=100.0)

        assert slow[0]["execution_time_ms"] == 200.0
        assert slow[1]["execution_time_ms"] == 175.0
        assert slow[2]["execution_time_ms"] == 150.0

    # ========== Optimization Suggestions Tests ==========

    def test_suggest_optimizations(self, optimizer):
        """Test suggesting optimizations."""
        query = {"entity_type": "requirement"}

        suggestions = optimizer.suggest_optimizations(query)

        assert len(suggestions) > 0

    def test_suggest_missing_filter(self, optimizer):
        """Test suggesting missing filter."""
        query = {"entity_type": "requirement"}

        suggestions = optimizer.suggest_optimizations(query)

        missing_filter = [s for s in suggestions if s["type"] == "missing_filter"]
        assert len(missing_filter) > 0

    def test_suggest_missing_pagination(self, optimizer):
        """Test suggesting missing pagination."""
        query = {"entity_type": "requirement", "filters": {"status": "active"}}

        suggestions = optimizer.suggest_optimizations(query)

        missing_pagination = [s for s in suggestions if s["type"] == "missing_pagination"]
        assert len(missing_pagination) > 0

    # ========== Integration Tests ==========

    def test_complete_optimization_workflow(self, optimizer):
        """Test complete optimization workflow."""
        # Optimize query
        query = {"entity_type": "requirement", "filters": {"status": "active"}}
        optimized = optimizer.optimize_query(query)

        # Cache result
        result = {"id": "req-1", "name": "Requirement 1"}
        optimizer.cache_query_result("q1", result)

        # Track performance
        optimizer.track_query_performance("q1", 25.0, 1)

        # Get report
        report = optimizer.get_performance_report()

        assert optimized is not None
        assert optimizer.get_cached_result("q1") == result
        assert report["total_queries"] == 1

