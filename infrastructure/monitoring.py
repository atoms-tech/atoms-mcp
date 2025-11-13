"""Monitoring and Observability Infrastructure

Provides performance monitoring, error tracking, and analytics.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class QueryPerformanceMonitor:
    """Monitor and log database query performance"""

    def __init__(self):
        self.slow_query_threshold = 1000  # ms
        self.query_stats = {}
        self.total_queries = 0

    async def track_query(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        filters: Optional[Dict] = None
    ):
        """Track query performance"""
        key = f"{operation}:{table}"

        if key not in self.query_stats:
            self.query_stats[key] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "slow_queries": 0
            }

        stats = self.query_stats[key]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["min_time"] = min(stats["min_time"], duration_ms)
        stats["max_time"] = max(stats["max_time"], duration_ms)
        self.total_queries += 1

        if duration_ms > self.slow_query_threshold:
            stats["slow_queries"] += 1
            logger.warning(
                f"Slow query detected: {key} took {duration_ms:.2f}ms",
                extra={"filters": filters}
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "total_queries": self.total_queries,
            "query_breakdown": {
                key: {
                    **stats,
                    "avg_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0,
                    "slow_query_percentage": (stats["slow_queries"] / stats["count"] * 100) if stats["count"] > 0 else 0
                }
                for key, stats in self.query_stats.items()
            }
        }


# ============================================================================
# ERROR TRACKING
# ============================================================================

class ErrorTracker:
    """Track and categorize errors"""

    def __init__(self):
        self.error_counts = {}
        self.error_history = []
        self.max_history = 1000

    async def track_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        severity: str = "error"
    ):
        """Track an error occurrence"""
        key = f"{error_type}:{error_message[:50]}"

        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": error_type,
            "message": error_message,
            "context": context,
            "severity": severity,
            "count": self.error_counts[key]
        }

        self.error_history.append(error_entry)

        # Alert on critical errors or high frequency
        if severity == "critical" or self.error_counts[key] > 10:
            await self._send_alert(error_entry)

        # Limit history size: keep only the most recent entries up to max_history
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

        # Log the error
        if severity == "critical":
            logger.critical(f"{error_type}: {error_message}", extra=context)
        elif severity == "error":
            logger.error(f"{error_type}: {error_message}", extra=context)
        else:
            logger.warning(f"{error_type}: {error_message}", extra=context)

    async def _send_alert(self, error_entry: Dict[str, Any]):
        """Send alert for critical errors"""
        logger.critical(f"ALERT: {error_entry}")
        # TODO: Integrate with alerting service (email, Slack, PagerDuty)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": len(self.error_history),
            "unique_errors": len(self.error_counts),
            "error_counts": dict(sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]),  # Top 20 errors
            "recent_errors": self.error_history[-10:]
        }


# ============================================================================
# USAGE ANALYTICS
# ============================================================================

class UsageAnalytics:
    """Track usage metrics for analytics"""

    def __init__(self):
        self.metrics = {
            "tool_usage": {},
            "entity_operations": {},
            "search_queries": [],
            "user_activity": {}
        }

    async def track_tool_usage(self, tool_name: str, user_id: str):
        """Track tool usage"""
        key = f"{tool_name}:{user_id}"
        self.metrics["tool_usage"][key] = self.metrics["tool_usage"].get(key, 0) + 1

    async def track_entity_operation(
        self,
        entity_type: str,
        operation: str,
        user_id: str,
        duration_ms: float
    ):
        """Track entity operations"""
        key = f"{entity_type}:{operation}"
        if key not in self.metrics["entity_operations"]:
            self.metrics["entity_operations"][key] = {
                "count": 0,
                "total_time": 0,
                "users": set()
            }

        stats = self.metrics["entity_operations"][key]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["users"].add(user_id)

    async def track_search(self, search_term: str, results_count: int, user_id: str):
        """Track search queries"""
        self.metrics["search_queries"].append({
            "term": search_term,
            "results": results_count,
            "user": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Limit history
        if len(self.metrics["search_queries"]) > 1000:
            self.metrics["search_queries"] = self.metrics["search_queries"][-500:]

    def get_analytics_report(self) -> Dict[str, Any]:
        """Generate analytics report"""
        return {
            "most_used_tools": sorted(
                self.metrics["tool_usage"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "popular_operations": sorted(
                [
                    {
                        "operation": k,
                        "count": v["count"],
                        "avg_time": v["total_time"] / v["count"] if v["count"] > 0 else 0,
                        "unique_users": len(v["users"])
                    }
                    for k, v in self.metrics["entity_operations"].items()
                ],
                key=lambda x: x["count"],
                reverse=True
            )[:10],
            "search_analytics": {
                "total_searches": len(self.metrics["search_queries"]),
                "avg_results": sum(s["results"] for s in self.metrics["search_queries"]) /
                               len(self.metrics["search_queries"]) if self.metrics["search_queries"] else 0
            }
        }


# Global instances
_performance_monitor: Optional[QueryPerformanceMonitor] = None
_error_tracker: Optional[ErrorTracker] = None
_usage_analytics: Optional[UsageAnalytics] = None


def get_performance_monitor() -> QueryPerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = QueryPerformanceMonitor()
        logger.info("Performance monitor initialized")
    return _performance_monitor


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
        logger.info("Error tracker initialized")
    return _error_tracker


def get_usage_analytics() -> UsageAnalytics:
    """Get global usage analytics instance"""
    global _usage_analytics
    if _usage_analytics is None:
        _usage_analytics = UsageAnalytics()
        logger.info("Usage analytics initialized")
    return _usage_analytics
