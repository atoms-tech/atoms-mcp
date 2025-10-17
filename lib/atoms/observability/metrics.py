"""
Production-ready Prometheus-compatible metrics collection.

This module provides comprehensive metrics collection including:
- Request duration histograms
- Tool execution metrics
- Error rate monitoring
- Active connection gauging
- Custom metric registration
- Thread-safe metric collection
- Prometheus exposition format

Author: Atoms MCP Platform
Version: 1.0.0
"""

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple

from .logging import get_logger

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Container for metric values with timestamp."""
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution tracking."""
    le: float  # Upper bound (less than or equal)
    count: int = 0


class Counter:
    """
    Thread-safe counter metric.

    Counters only increase and are typically used for counting requests,
    errors, etc. They reset to 0 on process restart.
    """

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[Tuple[str, ...], float] = defaultdict(float)
        self._lock = Lock()

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment counter by amount."""
        if amount < 0:
            raise ValueError("Counter can only be incremented by non-negative values")

        label_values = self._get_label_values(labels)
        with self._lock:
            self._values[label_values] += amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        label_values = self._get_label_values(labels)
        with self._lock:
            return self._values[label_values]

    def _get_label_values(self, labels: Optional[Dict[str, str]]) -> Tuple[str, ...]:
        """Convert label dict to tuple for indexing."""
        if not labels:
            return tuple()
        return tuple(labels.get(name, "") for name in self.label_names)

    def collect(self) -> List[Tuple[Dict[str, str], float]]:
        """Collect all metric values with labels."""
        with self._lock:
            result = []
            for label_tuple, value in self._values.items():
                label_dict = dict(zip(self.label_names, label_tuple))
                result.append((label_dict, value))
            return result


class Gauge:
    """
    Thread-safe gauge metric.

    Gauges can go up and down and represent a current value
    (e.g., active connections, memory usage).
    """

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[Tuple[str, ...], float] = defaultdict(float)
        self._lock = Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge to specific value."""
        label_values = self._get_label_values(labels)
        with self._lock:
            self._values[label_values] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment gauge by amount."""
        label_values = self._get_label_values(labels)
        with self._lock:
            self._values[label_values] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement gauge by amount."""
        label_values = self._get_label_values(labels)
        with self._lock:
            self._values[label_values] -= amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        label_values = self._get_label_values(labels)
        with self._lock:
            return self._values[label_values]

    def _get_label_values(self, labels: Optional[Dict[str, str]]) -> Tuple[str, ...]:
        """Convert label dict to tuple for indexing."""
        if not labels:
            return tuple()
        return tuple(labels.get(name, "") for name in self.label_names)

    def collect(self) -> List[Tuple[Dict[str, str], float]]:
        """Collect all metric values with labels."""
        with self._lock:
            result = []
            for label_tuple, value in self._values.items():
                label_dict = dict(zip(self.label_names, label_tuple))
                result.append((label_dict, value))
            return result


class Histogram:
    """
    Thread-safe histogram metric for distribution tracking.

    Histograms sample observations and count them in configurable buckets.
    Useful for request durations, response sizes, etc.
    """

    # Default buckets for HTTP request durations (in seconds)
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)

        # Storage: label_values -> bucket_index -> count
        self._bucket_counts: Dict[Tuple[str, ...], List[int]] = defaultdict(
            lambda: [0] * len(self.buckets)
        )
        self._sums: Dict[Tuple[str, ...], float] = defaultdict(float)
        self._counts: Dict[Tuple[str, ...], int] = defaultdict(int)
        self._lock = Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an observation."""
        label_values = self._get_label_values(labels)

        with self._lock:
            # Update buckets
            for i, bucket_le in enumerate(self.buckets):
                if value <= bucket_le:
                    self._bucket_counts[label_values][i] += 1

            # Update sum and count
            self._sums[label_values] += value
            self._counts[label_values] += 1

    @contextmanager
    def time(self, labels: Optional[Dict[str, str]] = None):
        """Context manager to time code blocks."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.observe(duration, labels)

    def get_buckets(self, labels: Optional[Dict[str, str]] = None) -> List[Tuple[float, int]]:
        """Get bucket counts for given labels."""
        label_values = self._get_label_values(labels)
        with self._lock:
            counts = self._bucket_counts[label_values]
            return list(zip(self.buckets, counts))

    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of all observations."""
        label_values = self._get_label_values(labels)
        with self._lock:
            return self._sums[label_values]

    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get count of all observations."""
        label_values = self._get_label_values(labels)
        with self._lock:
            return self._counts[label_values]

    def _get_label_values(self, labels: Optional[Dict[str, str]]) -> Tuple[str, ...]:
        """Convert label dict to tuple for indexing."""
        if not labels:
            return tuple()
        return tuple(labels.get(name, "") for name in self.label_names)

    def collect(self) -> List[Tuple[Dict[str, str], List[Tuple[float, int]], float, int]]:
        """Collect all metric values with labels."""
        with self._lock:
            result = []
            for label_tuple in self._bucket_counts.keys():
                label_dict = dict(zip(self.label_names, label_tuple))
                buckets = list(zip(self.buckets, self._bucket_counts[label_tuple]))
                sum_value = self._sums[label_tuple]
                count_value = self._counts[label_tuple]
                result.append((label_dict, buckets, sum_value, count_value))
            return result


class MetricsRegistry:
    """
    Central registry for all metrics.

    Provides thread-safe metric registration and collection.
    Supports Prometheus exposition format.
    """

    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = Lock()

    def register_counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Counter:
        """Register a counter metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Counter):
                    raise ValueError(f"Metric {name} already registered as different type")
                return metric

            counter = Counter(name, description, labels)
            self._metrics[name] = counter
            return counter

    def register_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Gauge:
        """Register a gauge metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Gauge):
                    raise ValueError(f"Metric {name} already registered as different type")
                return metric

            gauge = Gauge(name, description, labels)
            self._metrics[name] = gauge
            return gauge

    def register_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Register a histogram metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Histogram):
                    raise ValueError(f"Metric {name} already registered as different type")
                return metric

            histogram = Histogram(name, description, labels, buckets)
            self._metrics[name] = histogram
            return histogram

    def get_metric(self, name: str) -> Optional[Any]:
        """Get registered metric by name."""
        with self._lock:
            return self._metrics.get(name)

    def collect_all(self) -> Dict[str, Any]:
        """Collect all metrics for exposition."""
        with self._lock:
            result = {}
            for name, metric in self._metrics.items():
                result[name] = {
                    "type": self._get_metric_type(metric),
                    "description": metric.description,
                    "values": metric.collect()
                }
            return result

    def _get_metric_type(self, metric: Any) -> str:
        """Get metric type string."""
        if isinstance(metric, Counter):
            return "counter"
        elif isinstance(metric, Gauge):
            return "gauge"
        elif isinstance(metric, Histogram):
            return "histogram"
        return "unknown"

    def to_prometheus_format(self) -> str:
        """Convert all metrics to Prometheus exposition format."""
        lines = []

        with self._lock:
            for name, metric in self._metrics.items():
                metric_type = self._get_metric_type(metric)

                # Add HELP line
                lines.append(f"# HELP {name} {metric.description}")

                # Add TYPE line
                lines.append(f"# TYPE {name} {metric_type}")

                # Add metric values
                if isinstance(metric, (Counter, Gauge)):
                    for labels, value in metric.collect():
                        label_str = self._format_labels(labels)
                        lines.append(f"{name}{label_str} {value}")

                elif isinstance(metric, Histogram):
                    for labels, buckets, sum_value, count in metric.collect():
                        label_str = self._format_labels(labels)

                        # Add bucket values
                        for le, bucket_count in buckets:
                            bucket_labels = {**labels, "le": str(le)}
                            bucket_label_str = self._format_labels(bucket_labels)
                            lines.append(f"{name}_bucket{bucket_label_str} {bucket_count}")

                        # Add +Inf bucket
                        inf_labels = {**labels, "le": "+Inf"}
                        inf_label_str = self._format_labels(inf_labels)
                        lines.append(f"{name}_bucket{inf_label_str} {count}")

                        # Add sum and count
                        lines.append(f"{name}_sum{label_str} {sum_value}")
                        lines.append(f"{name}_count{label_str} {count}")

                lines.append("")  # Empty line between metrics

        return "\n".join(lines)

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus exposition."""
        if not labels:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(label_pairs) + "}"


# Global metrics registry
registry = MetricsRegistry()

# Standard HTTP metrics
http_requests_total = registry.register_counter(
    "http_requests_total",
    "Total HTTP requests",
    labels=["method", "path", "status"]
)

http_request_duration_seconds = registry.register_histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labels=["method", "path", "status"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Tool execution metrics
tool_executions_total = registry.register_counter(
    "tool_executions_total",
    "Total tool executions",
    labels=["tool_name", "status"]
)

tool_execution_duration_seconds = registry.register_histogram(
    "tool_execution_duration_seconds",
    "Tool execution duration in seconds",
    labels=["tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

# Error metrics
errors_total = registry.register_counter(
    "errors_total",
    "Total errors",
    labels=["type", "source"]
)

# Connection metrics
active_connections = registry.register_gauge(
    "active_connections",
    "Number of active connections",
    labels=["type"]
)

# Database metrics
database_queries_total = registry.register_counter(
    "database_queries_total",
    "Total database queries",
    labels=["operation", "status"]
)

database_query_duration_seconds = registry.register_histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    labels=["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Cache metrics
cache_operations_total = registry.register_counter(
    "cache_operations_total",
    "Total cache operations",
    labels=["operation", "status"]
)

cache_hit_ratio = registry.register_gauge(
    "cache_hit_ratio",
    "Cache hit ratio (0-1)",
    labels=["cache_name"]
)


def record_http_request(
    method: str,
    path: str,
    status: int,
    duration: float
) -> None:
    """Record HTTP request metrics."""
    labels = {
        "method": method,
        "path": path,
        "status": str(status)
    }

    http_requests_total.inc(labels=labels)
    http_request_duration_seconds.observe(duration, labels=labels)


def record_tool_execution(
    tool_name: str,
    duration: float,
    success: bool = True
) -> None:
    """Record tool execution metrics."""
    status = "success" if success else "error"

    tool_executions_total.inc(labels={"tool_name": tool_name, "status": status})
    tool_execution_duration_seconds.observe(duration, labels={"tool_name": tool_name})


def record_error(error_type: str, source: str) -> None:
    """Record error occurrence."""
    errors_total.inc(labels={"type": error_type, "source": source})


def record_database_query(
    operation: str,
    duration: float,
    success: bool = True
) -> None:
    """Record database query metrics."""
    status = "success" if success else "error"

    database_queries_total.inc(labels={"operation": operation, "status": status})
    database_query_duration_seconds.observe(duration, labels={"operation": operation})


def get_metrics_snapshot() -> Dict[str, Any]:
    """Get current snapshot of all metrics."""
    return registry.collect_all()


def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus exposition format."""
    return registry.to_prometheus_format()
