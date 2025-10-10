"""Memory leak detection and analysis utilities.

This module provides tools for:
- Memory usage trend analysis
- Leak detection using linear regression
- Memory growth tracking
- Recommendations for memory optimization
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryLeakDetector:
    """Detect potential memory leaks by analyzing memory trends."""

    def __init__(self, monitor):
        """Initialize leak detector.

        Args:
            monitor: PerformanceMonitor instance to analyze
        """
        self.monitor = monitor

    def get_memory_usage_trend(self, window_minutes: int = 10) -> list[dict[str, Any]]:
        """Get memory usage trend over time.

        Args:
            window_minutes: Time window to analyze

        Returns:
            List of memory usage data points grouped by minute
        """
        if not PSUTIL_AVAILABLE:
            return []

        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        with self.monitor._lock:
            recent_metrics = [m for m in self.monitor.metrics_buffer if m.start_time >= cutoff_time]

        # Group by minute
        memory_by_minute = defaultdict(list)
        for metric in recent_metrics:
            minute_key = metric.start_time.strftime("%Y-%m-%d %H:%M")
            if metric.memory_after > 0:
                memory_by_minute[minute_key].append(metric.memory_after)

        trend_data = []
        for minute, memory_values in sorted(memory_by_minute.items()):
            trend_data.append(
                {
                    "timestamp": minute,
                    "avg_memory_mb": sum(memory_values) / len(memory_values) / 1024 / 1024,
                    "max_memory_mb": max(memory_values) / 1024 / 1024,
                    "sample_count": len(memory_values),
                }
            )

        return trend_data

    def detect_memory_leaks(self, threshold_mb: float = 50.0) -> dict[str, Any]:
        """Detect potential memory leaks using linear regression.

        Args:
            threshold_mb: Memory growth threshold in MB to trigger leak detection

        Returns:
            Dictionary with leak detection results and diagnostics
        """
        if not PSUTIL_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "psutil not available - install with: pip install psutil",
            }

        trend_data = self.get_memory_usage_trend(window_minutes=30)

        if len(trend_data) < 5:
            return {"status": "insufficient_data", "message": "Need more data points"}

        # Calculate memory growth rate
        first_avg = trend_data[0]["avg_memory_mb"]
        last_avg = trend_data[-1]["avg_memory_mb"]
        memory_growth = last_avg - first_avg

        # Calculate trend slope using simple linear regression
        x_values = list(range(len(trend_data)))
        y_values = [point["avg_memory_mb"] for point in trend_data]

        # Simple linear regression for trend
        n = len(x_values)
        slope = (n * sum(x * y for x, y in zip(x_values, y_values, strict=False)) - sum(x_values) * sum(y_values)) / (
            n * sum(x * x for x in x_values) - sum(x_values) ** 2
        )

        leak_detected = memory_growth > threshold_mb or slope > 1.0  # 1MB/minute slope threshold

        return {
            "status": "leak_detected" if leak_detected else "normal",
            "memory_growth_mb": memory_growth,
            "growth_rate_mb_per_minute": slope,
            "threshold_mb": threshold_mb,
            "data_points": len(trend_data),
            "current_memory_mb": trend_data[-1]["avg_memory_mb"] if trend_data else 0,
            "tracked_objects": len(self.monitor._tracked_objects),
            "trend_data": trend_data,
        }

    def get_leak_recommendations(self) -> list[str]:
        """Get recommendations for addressing potential memory leaks.

        Returns:
            List of recommendation strings
        """
        leak_status = self.detect_memory_leaks()
        recommendations = []

        if leak_status["status"] == "leak_detected":
            recommendations.extend(
                [
                    "Memory leak detected - investigate recent code changes",
                    "Check for circular references in tracked objects",
                    "Review context managers for proper cleanup",
                    "Consider forcing garbage collection",
                ]
            )

            if leak_status["growth_rate_mb_per_minute"] > 5.0:
                recommendations.append("High memory growth rate - immediate attention required")

            if leak_status["tracked_objects"] > 1000:
                recommendations.append("Large number of tracked objects - review object lifecycle")

        elif leak_status["status"] == "normal":
            recommendations.append("Memory usage is stable")

        return recommendations
