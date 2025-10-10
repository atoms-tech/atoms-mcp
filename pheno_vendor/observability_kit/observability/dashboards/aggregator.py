"""
Metric aggregation for dashboard data collection.

Provides real-time aggregation of metrics from multiple sources for dashboard display.
"""

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Deque

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Individual metric data point."""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    tenant_id: Optional[str] = None  # For multi-tenant support


class MetricAggregator:
    """
    Aggregates metrics for dashboard display.

    Supports:
    - Time-series metric storage
    - Label-based filtering
    - Multi-tenant isolation
    - Redis persistence (optional)

    Example:
        aggregator = MetricAggregator()
        await aggregator.record_metric(
            "api_requests",
            1.0,
            MetricType.COUNTER,
            labels={"endpoint": "/users"}
        )
    """

    def __init__(
        self,
        redis_client=None,
        retention_hours: int = 24,
        max_memory_metrics: int = 10000,
    ):
        """
        Initialize metric aggregator.

        Args:
            redis_client: Optional Redis client for persistence
            retention_hours: How long to retain metrics
            max_memory_metrics: Max metrics to keep in memory per metric key
        """
        self.redis_client = redis_client
        self.retention_hours = retention_hours
        self.max_memory_metrics = max_memory_metrics

        # In-memory storage: metric_key -> deque of metrics
        self.metrics_store: Dict[str, Deque[Metric]] = defaultdict(
            lambda: deque(maxlen=max_memory_metrics)
        )

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType | str,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
        tenant_id: Optional[str] = None,
    ) -> None:
        """
        Record a metric data point.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Metric type (counter, gauge, histogram, timer)
            labels: Optional labels for filtering
            unit: Optional unit string
            tenant_id: Optional tenant ID for multi-tenant isolation
        """
        timestamp = datetime.now(timezone.utc)
        labels = labels or {}

        # Convert string metric_type to enum if needed
        if isinstance(metric_type, str):
            try:
                metric_type = MetricType(metric_type.lower())
            except ValueError:
                logger.warning(f"Invalid metric type '{metric_type}', defaulting to gauge")
                metric_type = MetricType.GAUGE

        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=timestamp,
            labels=labels,
            unit=unit,
            tenant_id=tenant_id,
        )

        # Create metric key for storage
        metric_key = self._create_metric_key(name, labels, tenant_id)

        # Store in memory
        self.metrics_store[metric_key].append(metric)

        # Persist to Redis if available
        if self.redis_client:
            await self._persist_to_redis(metric, metric_key)

    def _create_metric_key(
        self,
        name: str,
        labels: Dict[str, str],
        tenant_id: Optional[str] = None,
    ) -> str:
        """Create a unique key for metric storage."""
        label_str = json.dumps(labels, sort_keys=True)
        if tenant_id:
            return f"{tenant_id}:{name}:{label_str}"
        return f"{name}:{label_str}"

    async def _persist_to_redis(self, metric: Metric, metric_key: str) -> None:
        """Persist metric to Redis."""
        try:
            timestamp_key = int(metric.timestamp.timestamp())
            redis_key = f"metrics:{metric_key}:{timestamp_key}"

            metric_data = {
                "name": metric.name,
                "value": metric.value,
                "type": metric.metric_type.value,
                "labels": json.dumps(metric.labels),
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "tenant_id": metric.tenant_id or "",
            }

            # Store with TTL
            ttl_seconds = self.retention_hours * 3600
            self.redis_client.setex(redis_key, ttl_seconds, json.dumps(metric_data))

            # Maintain time-series index
            ts_key = f"metrics_ts:{metric.name}"
            if metric.tenant_id:
                ts_key = f"metrics_ts:{metric.tenant_id}:{metric.name}"

            self.redis_client.zadd(ts_key, {redis_key: metric.timestamp.timestamp()})
            self.redis_client.expire(ts_key, ttl_seconds)

        except Exception as e:
            logger.debug(f"Failed to persist metric to Redis: {e}")

    async def get_metrics(
        self,
        name_pattern: Optional[str] = None,
        time_range_minutes: int = 60,
        labels: Optional[Dict[str, str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Metric]:
        """
        Get metrics matching criteria.

        Args:
            name_pattern: Optional pattern to match metric names
            time_range_minutes: Time range to retrieve
            labels: Optional label filters
            tenant_id: Optional tenant filter

        Returns:
            List of matching metrics
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=time_range_minutes)

        matching_metrics = []

        for metric_key, metric_deque in self.metrics_store.items():
            # Parse metric key
            if ":" in metric_key:
                parts = metric_key.split(":")
                if tenant_id and not metric_key.startswith(f"{tenant_id}:"):
                    continue
                metric_name = parts[1] if tenant_id else parts[0]
            else:
                metric_name = metric_key

            # Check name pattern
            if name_pattern and name_pattern not in metric_name:
                continue

            # Get metrics in time range
            for metric in metric_deque:
                # Check tenant isolation
                if tenant_id and metric.tenant_id != tenant_id:
                    continue

                if start_time <= metric.timestamp <= end_time:
                    # Check label filters
                    if labels:
                        if not all(metric.labels.get(k) == v for k, v in labels.items()):
                            continue

                    matching_metrics.append(metric)

        return sorted(matching_metrics, key=lambda m: m.timestamp)

    def aggregate_by_label(
        self,
        metrics: List[Metric],
        label_key: str,
        aggregation_func: str = "sum",
    ) -> Dict[str, float]:
        """
        Aggregate metrics by a specific label.

        Args:
            metrics: List of metrics to aggregate
            label_key: Label key to group by
            aggregation_func: 'sum', 'avg', 'min', 'max', 'count'

        Returns:
            Dictionary of label_value -> aggregated_value
        """
        grouped = defaultdict(list)

        for metric in metrics:
            label_value = metric.labels.get(label_key, "unknown")
            grouped[label_value].append(metric.value)

        result = {}
        for label_value, values in grouped.items():
            if aggregation_func == "sum":
                result[label_value] = sum(values)
            elif aggregation_func == "avg":
                result[label_value] = sum(values) / len(values)
            elif aggregation_func == "min":
                result[label_value] = min(values)
            elif aggregation_func == "max":
                result[label_value] = max(values)
            elif aggregation_func == "count":
                result[label_value] = len(values)
            else:
                result[label_value] = sum(values)

        return result


class DashboardDataCollector:
    """
    Collects and aggregates data for dashboard display.

    Integrates with health monitoring and metric aggregation to provide
    comprehensive dashboard data.
    """

    def __init__(
        self,
        metric_aggregator: Optional[MetricAggregator] = None,
        health_monitor=None,
    ):
        """
        Initialize dashboard data collector.

        Args:
            metric_aggregator: Optional MetricAggregator instance
            health_monitor: Optional HealthMonitor instance
        """
        self.metric_aggregator = metric_aggregator or MetricAggregator()
        self.health_monitor = health_monitor

    async def get_dashboard_data(
        self,
        time_range_minutes: int = 30,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.

        Args:
            time_range_minutes: Time range for metrics
            tenant_id: Optional tenant filter

        Returns:
            Dashboard data dictionary
        """
        # Get recent metrics
        recent_metrics = await self.metric_aggregator.get_metrics(
            time_range_minutes=time_range_minutes,
            tenant_id=tenant_id,
        )

        # Get health data if monitor available
        health_data = None
        if self.health_monitor:
            try:
                health_report = await self.health_monitor.check_all()
                health_data = {
                    "status": health_report.overall_status.value,
                    "components": {
                        name: {
                            "status": result.status.value,
                            "message": result.message,
                            "response_time_ms": result.response_time_ms,
                        }
                        for name, result in health_report.components.items()
                    },
                    "avg_response_time_ms": health_report.avg_response_time_ms,
                    "total_errors": health_report.total_errors,
                }
            except Exception as e:
                logger.error(f"Failed to get health data: {e}")

        # Aggregate task metrics
        task_metrics = self._aggregate_task_metrics(recent_metrics)

        # Calculate throughput
        throughput = self._calculate_throughput(recent_metrics, time_range_minutes)

        return {
            "health": health_data,
            "task_metrics": task_metrics,
            "throughput": throughput,
            "metric_count": len(recent_metrics),
            "time_range_minutes": time_range_minutes,
            "tenant_id": tenant_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def _aggregate_task_metrics(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Aggregate task-related metrics."""
        task_metrics = {
            "total_created": len([m for m in metrics if m.name == "tasks_created_total"]),
            "total_completed": len([m for m in metrics if m.name == "tasks_completed_total"]),
            "total_failed": len([m for m in metrics if m.name == "tasks_failed_total"]),
            "avg_execution_time": 0.0,
        }

        exec_times = [m.value for m in metrics if m.name == "task_execution_time"]
        if exec_times:
            task_metrics["avg_execution_time"] = sum(exec_times) / len(exec_times)

        return task_metrics

    def _calculate_throughput(
        self,
        metrics: List[Metric],
        time_range_minutes: int,
    ) -> float:
        """Calculate throughput (operations/second)."""
        if not metrics:
            return 0.0

        # Count relevant metrics
        operation_metrics = [
            m for m in metrics
            if m.name in ["tasks_created_total", "tasks_completed_total", "api_requests"]
        ]

        if not operation_metrics:
            return 0.0

        duration_seconds = time_range_minutes * 60
        return len(operation_metrics) / duration_seconds if duration_seconds > 0 else 0.0


# Global collector instance
_dashboard_collector: Optional[DashboardDataCollector] = None


def get_dashboard_collector() -> DashboardDataCollector:
    """Get the global dashboard data collector instance."""
    global _dashboard_collector
    if _dashboard_collector is None:
        _dashboard_collector = DashboardDataCollector()
    return _dashboard_collector
