"""Performance Metrics for Atoms MCP - Track and analyze performance.

Provides performance tracking, metrics collection, and analytics.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Track and analyze performance metrics."""

    def __init__(self, retention_hours: int = 24):
        """Initialize performance metrics.
        
        Args:
            retention_hours: Hours to retain metrics
        """
        self.retention_hours = retention_hours
        self.metrics = defaultdict(list)
        self.operation_timings = {}

    def start_operation(self, operation_id: str) -> None:
        """Start timing an operation.
        
        Args:
            operation_id: Unique operation ID
        """
        self.operation_timings[operation_id] = time.time()

    def end_operation(
        self,
        operation_id: str,
        operation_type: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """End timing an operation and record metrics.
        
        Args:
            operation_id: Unique operation ID
            operation_type: Type of operation
            success: Whether operation succeeded
            metadata: Additional metadata
            
        Returns:
            Timing info dict
        """
        if operation_id not in self.operation_timings:
            return {"error": "Operation not started"}

        start_time = self.operation_timings.pop(operation_id)
        duration_ms = (time.time() - start_time) * 1000

        metric = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.metrics[operation_type].append(metric)
        logger.info(f"Operation {operation_type}: {duration_ms:.2f}ms")

        return metric

    def get_metrics(
        self,
        operation_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recorded metrics.
        
        Args:
            operation_type: Filter by operation type
            limit: Maximum number of metrics to return
            
        Returns:
            List of metrics
        """
        if operation_type:
            metrics = self.metrics.get(operation_type, [])
        else:
            metrics = []
            for ops in self.metrics.values():
                metrics.extend(ops)

        # Sort by timestamp descending
        metrics.sort(key=lambda m: m["timestamp"], reverse=True)
        return metrics[:limit]

    def get_statistics(
        self,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics for operations.
        
        Args:
            operation_type: Filter by operation type
            
        Returns:
            Statistics dict
        """
        if operation_type:
            metrics = self.metrics.get(operation_type, [])
        else:
            metrics = []
            for ops in self.metrics.values():
                metrics.extend(ops)

        if not metrics:
            return {
                "count": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0
            }

        durations = [m["duration_ms"] for m in metrics]
        successes = sum(1 for m in metrics if m["success"])

        return {
            "count": len(metrics),
            "success_count": successes,
            "failure_count": len(metrics) - successes,
            "success_rate": successes / len(metrics) if metrics else 0,
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p50_duration_ms": sorted(durations)[len(durations) // 2],
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)],
            "p99_duration_ms": sorted(durations)[int(len(durations) * 0.99)]
        }

    def get_operation_types(self) -> List[str]:
        """Get all operation types.
        
        Returns:
            List of operation types
        """
        return list(self.metrics.keys())

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.operation_timings.clear()
        logger.info("Metrics cleared")

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary.
        
        Returns:
            Summary dict
        """
        summary = {}
        for op_type in self.get_operation_types():
            summary[op_type] = self.get_statistics(op_type)

        return {
            "timestamp": datetime.now().isoformat(),
            "operation_types": len(summary),
            "total_operations": sum(s["count"] for s in summary.values()),
            "operations": summary
        }

    def record_metric(
        self,
        operation_type: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric directly.
        
        Args:
            operation_type: Type of operation
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        metric = {
            "operation_type": operation_type,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.metrics[operation_type].append(metric)


# Global performance metrics instance
_performance_metrics = None


def get_performance_metrics() -> PerformanceMetrics:
    """Get global performance metrics instance."""
    global _performance_metrics
    if _performance_metrics is None:
        _performance_metrics = PerformanceMetrics()
    return _performance_metrics

