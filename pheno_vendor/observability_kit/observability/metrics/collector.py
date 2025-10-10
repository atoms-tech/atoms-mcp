"""Metrics collection with Prometheus-compatible format.

Based on 2025 Python best practices:
- Prometheus exposition format support
- Thread-safe metric collection
- In-memory aggregation with minimal overhead
- Type-safe metric definitions
- Support for labels/dimensions
- Histogram with configurable buckets
"""

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


class MetricType(str, Enum):
    """Prometheus metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricMetadata:
    """Metadata for a metric."""
    name: str
    help_text: str
    metric_type: MetricType
    labels: List[str] = field(default_factory=list)


class Counter:
    """Thread-safe counter metric.

    Counters only go up and are reset to zero on restart.
    Use for: request counts, error counts, completed tasks.

    Example:
        >>> counter = Counter("http_requests_total", "Total HTTP requests", labels=["method", "status"])
        >>> counter.inc({"method": "GET", "status": "200"})
        >>> counter.inc({"method": "POST", "status": "201"}, value=5)
    """

    def __init__(self, name: str, help_text: str, labels: Optional[List[str]] = None):
        self.metadata = MetricMetadata(
            name=name,
            help_text=help_text,
            metric_type=MetricType.COUNTER,
            labels=labels or [],
        )
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, labels: Optional[Dict[str, str]] = None, value: float = 1.0) -> None:
        """Increment counter by value (default 1.0)."""
        if value < 0:
            raise ValueError("Counter can only increment by non-negative values")

        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += value

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> tuple:
        """Create a hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values[label_key]

    def collect(self) -> List[tuple[Dict[str, str], float]]:
        """Collect all counter values with their labels."""
        with self._lock:
            return [(dict(k), v) for k, v in self._values.items()]


class Gauge:
    """Thread-safe gauge metric.

    Gauges can go up and down.
    Use for: current memory usage, active connections, queue depth.

    Example:
        >>> gauge = Gauge("memory_usage_bytes", "Current memory usage")
        >>> gauge.set(1024 * 1024 * 100)  # 100 MB
        >>> gauge.inc()  # Increment by 1
        >>> gauge.dec(50)  # Decrement by 50
    """

    def __init__(self, name: str, help_text: str, labels: Optional[List[str]] = None):
        self.metadata = MetricMetadata(
            name=name,
            help_text=help_text,
            metric_type=MetricType.GAUGE,
            labels=labels or [],
        )
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge to specific value."""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = value

    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment gauge by value (default 1.0)."""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += value

    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement gauge by value (default 1.0)."""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] -= value

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> tuple:
        """Create a hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values[label_key]

    def collect(self) -> List[tuple[Dict[str, str], float]]:
        """Collect all gauge values with their labels."""
        with self._lock:
            return [(dict(k), v) for k, v in self._values.items()]


@dataclass
class HistogramBucket:
    """Histogram bucket for a specific upper bound."""
    le: float  # Less than or equal to
    count: int = 0


class Histogram:
    """Thread-safe histogram metric.

    Histograms track the distribution of observations.
    Use for: request duration, response size, query latency.

    Example:
        >>> hist = Histogram("http_request_duration_seconds", "HTTP request latency",
        ...                  buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        >>> hist.observe(0.042, {"method": "GET", "endpoint": "/api/users"})
    """

    # Default buckets for latency in seconds (Prometheus standard)
    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(
        self,
        name: str,
        help_text: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[Sequence[float]] = None,
    ):
        self.metadata = MetricMetadata(
            name=name,
            help_text=help_text,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or [],
        )
        self.buckets = sorted(buckets) if buckets else self.DEFAULT_BUCKETS

        # Storage: label_key -> {bucket_le -> count}
        self._bucket_counts: Dict[tuple, Dict[float, int]] = defaultdict(
            lambda: {bucket: 0 for bucket in self.buckets}
        )
        # Storage: label_key -> sum
        self._sums: Dict[tuple, float] = defaultdict(float)
        # Storage: label_key -> count
        self._counts: Dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value and update histogram buckets."""
        label_key = self._make_label_key(labels)

        with self._lock:
            # Update buckets
            for bucket in self.buckets:
                if value <= bucket:
                    self._bucket_counts[label_key][bucket] += 1

            # Update sum and count
            self._sums[label_key] += value
            self._counts[label_key] += 1

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> tuple:
        """Create a hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def collect(self) -> List[Dict[str, Any]]:
        """Collect histogram data with buckets, sum, and count."""
        with self._lock:
            results = []
            for label_key in self._bucket_counts.keys():
                labels_dict = dict(label_key)
                results.append({
                    "labels": labels_dict,
                    "buckets": dict(self._bucket_counts[label_key]),
                    "sum": self._sums[label_key],
                    "count": self._counts[label_key],
                })
            return results


class MetricsCollector:
    """Central metrics collector with Prometheus-compatible format.

    Thread-safe collector for counters, gauges, and histograms.
    Supports labels for multi-dimensional metrics.

    Example:
        >>> collector = MetricsCollector()
        >>> requests = collector.counter("http_requests_total", "Total requests",
        ...                              labels=["method", "status"])
        >>> requests.inc({"method": "GET", "status": "200"})
        >>>
        >>> memory = collector.gauge("memory_usage_bytes", "Memory usage")
        >>> memory.set(1024 * 1024 * 500)  # 500 MB
        >>>
        >>> latency = collector.histogram("http_request_duration_seconds",
        ...                               "Request latency")
        >>> latency.observe(0.042)
    """

    def __init__(self):
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram]] = {}
        self._lock = threading.Lock()

    def counter(
        self, name: str, help_text: str, labels: Optional[List[str]] = None
    ) -> Counter:
        """Create or retrieve a counter metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Counter):
                    raise ValueError(f"Metric {name} already exists as {type(metric)}")
                return metric

            counter = Counter(name, help_text, labels)
            self._metrics[name] = counter
            return counter

    def gauge(
        self, name: str, help_text: str, labels: Optional[List[str]] = None
    ) -> Gauge:
        """Create or retrieve a gauge metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Gauge):
                    raise ValueError(f"Metric {name} already exists as {type(metric)}")
                return metric

            gauge = Gauge(name, help_text, labels)
            self._metrics[name] = gauge
            return gauge

    def histogram(
        self,
        name: str,
        help_text: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[Sequence[float]] = None,
    ) -> Histogram:
        """Create or retrieve a histogram metric."""
        with self._lock:
            if name in self._metrics:
                metric = self._metrics[name]
                if not isinstance(metric, Histogram):
                    raise ValueError(f"Metric {name} already exists as {type(metric)}")
                return metric

            histogram = Histogram(name, help_text, labels, buckets)
            self._metrics[name] = histogram
            return histogram

    def get_metric(self, name: str) -> Optional[Union[Counter, Gauge, Histogram]]:
        """Get a metric by name."""
        with self._lock:
            return self._metrics.get(name)

    def collect_all(self) -> Dict[str, Any]:
        """Collect all metrics data."""
        with self._lock:
            results = {}
            for name, metric in self._metrics.items():
                if isinstance(metric, (Counter, Gauge)):
                    results[name] = {
                        "type": metric.metadata.metric_type.value,
                        "help": metric.metadata.help_text,
                        "values": metric.collect(),
                    }
                elif isinstance(metric, Histogram):
                    results[name] = {
                        "type": metric.metadata.metric_type.value,
                        "help": metric.metadata.help_text,
                        "histograms": metric.collect(),
                    }
            return results

    def to_prometheus_text(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            String in Prometheus exposition format
        """
        lines = []

        with self._lock:
            for name, metric in self._metrics.items():
                # Add HELP and TYPE
                lines.append(f"# HELP {name} {metric.metadata.help_text}")
                lines.append(f"# TYPE {name} {metric.metadata.metric_type.value}")

                if isinstance(metric, (Counter, Gauge)):
                    # Simple counter/gauge format
                    for labels_dict, value in metric.collect():
                        if labels_dict:
                            labels_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                            lines.append(f"{name}{{{labels_str}}} {value}")
                        else:
                            lines.append(f"{name} {value}")

                elif isinstance(metric, Histogram):
                    # Histogram format with buckets, sum, count
                    for hist_data in metric.collect():
                        labels_dict = hist_data["labels"]
                        buckets = hist_data["buckets"]
                        total_sum = hist_data["sum"]
                        total_count = hist_data["count"]

                        # Base labels string
                        base_labels = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                        labels_prefix = f"{{{base_labels}," if base_labels else "{"

                        # Cumulative buckets
                        cumulative_count = 0
                        for le, count in sorted(buckets.items()):
                            cumulative_count = count  # Already cumulative from observe
                            lines.append(f'{name}_bucket{labels_prefix}le="{le}"}} {cumulative_count}')

                        # +Inf bucket
                        lines.append(f'{name}_bucket{labels_prefix}le="+Inf"}} {total_count}')

                        # Sum and count
                        labels_str = f"{{{base_labels}}}" if base_labels else ""
                        lines.append(f"{name}_sum{labels_str} {total_sum}")
                        lines.append(f"{name}_count{labels_str} {total_count}")

                lines.append("")  # Empty line between metrics

        return "\n".join(lines)

    def reset_all(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._metrics.clear()
