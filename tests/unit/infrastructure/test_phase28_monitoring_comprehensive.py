"""Phase 28: Comprehensive tests for monitoring infrastructure to reach 85%+ coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestQueryPerformanceMonitor:
    """Comprehensive tests for QueryPerformanceMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create QueryPerformanceMonitor instance."""
        from infrastructure.monitoring import QueryPerformanceMonitor
        return QueryPerformanceMonitor()

    @pytest.mark.asyncio
    async def test_track_query_basic(self, monitor):
        """Test basic query tracking."""
        await monitor.track_query("select", "documents", 50.0)
        
        stats = monitor.get_stats()
        assert stats["total_queries"] == 1

    @pytest.mark.asyncio
    async def test_track_query_slow_query(self, monitor):
        """Test tracking slow query."""
        await monitor.track_query("select", "documents", 1500.0)
        
        stats = monitor.get_stats()
        assert stats["query_breakdown"]["select:documents"]["slow_queries"] == 1

    @pytest.mark.asyncio
    async def test_track_query_multiple_operations(self, monitor):
        """Test tracking multiple operations."""
        await monitor.track_query("select", "documents", 50.0)
        await monitor.track_query("insert", "documents", 100.0)
        await monitor.track_query("update", "requirements", 75.0)
        
        stats = monitor.get_stats()
        assert stats["total_queries"] == 3
        assert len(stats["query_breakdown"]) == 3

    @pytest.mark.asyncio
    async def test_track_query_with_filters(self, monitor):
        """Test tracking query with filters."""
        await monitor.track_query("select", "documents", 50.0, filters={"status": "active"})
        
        stats = monitor.get_stats()
        assert stats["total_queries"] == 1

    @pytest.mark.asyncio
    async def test_get_stats_averages(self, monitor):
        """Test getting stats with averages."""
        await monitor.track_query("select", "documents", 50.0)
        await monitor.track_query("select", "documents", 100.0)
        await monitor.track_query("select", "documents", 150.0)
        
        stats = monitor.get_stats()
        breakdown = stats["query_breakdown"]["select:documents"]
        assert breakdown["avg_time"] == 100.0
        assert breakdown["min_time"] == 50.0
        assert breakdown["max_time"] == 150.0

    @pytest.mark.asyncio
    async def test_get_stats_slow_query_percentage(self, monitor):
        """Test slow query percentage calculation."""
        await monitor.track_query("select", "documents", 500.0)  # Normal
        await monitor.track_query("select", "documents", 1500.0)  # Slow
        await monitor.track_query("select", "documents", 2000.0)  # Slow
        
        stats = monitor.get_stats()
        breakdown = stats["query_breakdown"]["select:documents"]
        assert breakdown["slow_query_percentage"] == 66.67  # 2 out of 3


class TestErrorTracker:
    """Comprehensive tests for ErrorTracker."""

    @pytest.fixture
    def tracker(self):
        """Create ErrorTracker instance."""
        from infrastructure.monitoring import ErrorTracker
        return ErrorTracker()

    @pytest.mark.asyncio
    async def test_track_error_basic(self, tracker):
        """Test basic error tracking."""
        await tracker.track_error("ValueError", "Invalid input", {"field": "name"})
        
        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_track_error_critical(self, tracker):
        """Test tracking critical error."""
        await tracker.track_error("CriticalError", "System failure", {}, severity="critical")
        
        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_track_error_high_frequency(self, tracker):
        """Test tracking high frequency errors."""
        for i in range(15):
            await tracker.track_error("FrequentError", "Same error", {})
        
        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 15

    @pytest.mark.asyncio
    async def test_track_error_different_types(self, tracker):
        """Test tracking different error types."""
        await tracker.track_error("TypeError", "Type error", {})
        await tracker.track_error("ValueError", "Value error", {})
        await tracker.track_error("KeyError", "Key error", {})
        
        summary = tracker.get_error_summary()
        assert summary["unique_errors"] == 3

    @pytest.mark.asyncio
    async def test_track_error_history_limit(self, tracker):
        """Test error history limit."""
        tracker.max_history = 10
        for i in range(15):
            await tracker.track_error("Error", f"Error {i}", {})
        
        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 10  # Limited to max_history

    @pytest.mark.asyncio
    async def test_get_error_summary_top_errors(self, tracker):
        """Test getting top errors in summary."""
        for i in range(5):
            await tracker.track_error("Error1", "Message1", {})
        for i in range(3):
            await tracker.track_error("Error2", "Message2", {})
        
        summary = tracker.get_error_summary()
        assert len(summary["error_counts"]) <= 20  # Top 20

    @pytest.mark.asyncio
    async def test_get_error_summary_recent_errors(self, tracker):
        """Test getting recent errors."""
        for i in range(15):
            await tracker.track_error("Error", f"Message {i}", {})
        
        summary = tracker.get_error_summary()
        assert len(summary["recent_errors"]) == 10


class TestUsageAnalytics:
    """Comprehensive tests for UsageAnalytics."""

    @pytest.fixture
    def analytics(self):
        """Create UsageAnalytics instance."""
        from infrastructure.monitoring import UsageAnalytics
        return UsageAnalytics()

    @pytest.mark.asyncio
    async def test_track_tool_usage(self, analytics):
        """Test tracking tool usage."""
        await analytics.track_tool_usage("entity_tool", "user1")
        await analytics.track_tool_usage("entity_tool", "user1")
        await analytics.track_tool_usage("query_tool", "user2")
        
        report = analytics.get_analytics_report()
        assert len(report["most_used_tools"]) > 0

    @pytest.mark.asyncio
    async def test_track_entity_operation(self, analytics):
        """Test tracking entity operations."""
        await analytics.track_entity_operation("requirement", "create", "user1", 50.0)
        await analytics.track_entity_operation("requirement", "create", "user2", 75.0)
        
        report = analytics.get_analytics_report()
        assert len(report["popular_operations"]) > 0

    @pytest.mark.asyncio
    async def test_track_entity_operation_multiple_users(self, analytics):
        """Test tracking operations from multiple users."""
        await analytics.track_entity_operation("requirement", "create", "user1", 50.0)
        await analytics.track_entity_operation("requirement", "create", "user2", 75.0)
        await analytics.track_entity_operation("requirement", "create", "user3", 100.0)
        
        report = analytics.get_analytics_report()
        op = next((o for o in report["popular_operations"] if o["operation"] == "requirement:create"), None)
        assert op is not None
        assert op["unique_users"] == 3

    @pytest.mark.asyncio
    async def test_track_search(self, analytics):
        """Test tracking search queries."""
        await analytics.track_search("test query", 10, "user1")
        await analytics.track_search("another query", 5, "user2")
        
        report = analytics.get_analytics_report()
        assert report["search_analytics"]["total_searches"] == 2

    @pytest.mark.asyncio
    async def test_track_search_history_limit(self, analytics):
        """Test search history limit."""
        for i in range(1200):
            await analytics.track_search(f"query {i}", 10, "user1")
        
        report = analytics.get_analytics_report()
        assert report["search_analytics"]["total_searches"] == 500  # Limited

    @pytest.mark.asyncio
    async def test_get_analytics_report_most_used_tools(self, analytics):
        """Test getting most used tools."""
        for i in range(10):
            await analytics.track_tool_usage("tool1", "user1")
        for i in range(5):
            await analytics.track_tool_usage("tool2", "user1")
        
        report = analytics.get_analytics_report()
        assert len(report["most_used_tools"]) <= 10
        assert report["most_used_tools"][0][0] == "tool1:user1"

    @pytest.mark.asyncio
    async def test_get_analytics_report_avg_results(self, analytics):
        """Test average results calculation."""
        await analytics.track_search("query1", 10, "user1")
        await analytics.track_search("query2", 20, "user1")
        await analytics.track_search("query3", 30, "user1")
        
        report = analytics.get_analytics_report()
        assert report["search_analytics"]["avg_results"] == 20.0


class TestMonitoringSingletons:
    """Tests for singleton functions."""

    def test_get_performance_monitor(self):
        """Test getting performance monitor singleton."""
        from infrastructure.monitoring import get_performance_monitor
        
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        assert monitor1 is monitor2

    def test_get_error_tracker(self):
        """Test getting error tracker singleton."""
        from infrastructure.monitoring import get_error_tracker
        
        tracker1 = get_error_tracker()
        tracker2 = get_error_tracker()
        
        assert tracker1 is tracker2

    def test_get_usage_analytics(self):
        """Test getting usage analytics singleton."""
        from infrastructure.monitoring import get_usage_analytics
        
        analytics1 = get_usage_analytics()
        analytics2 = get_usage_analytics()
        
        assert analytics1 is analytics2
