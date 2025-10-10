"""Performance metrics data structures.

This module provides data classes for storing and managing performance metrics
including timing, memory, token usage, and error tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class PerformanceMetrics:
    """Container for performance measurements.

    Tracks comprehensive metrics for operations including:
    - Timing metrics (duration, CPU time, wall time)
    - Memory usage (before, after, delta, peak)
    - Token usage (input, output, total)
    - Request/response sizes
    - Provider-specific information
    - Correlation tracking for distributed tracing
    - Success/error status
    """

    # Timing metrics (in seconds)
    duration: float = 0.0
    cpu_time: float = 0.0
    wall_time: float = 0.0

    # Memory metrics (in bytes)
    memory_before: int = 0
    memory_after: int = 0
    memory_peak: int = 0
    memory_delta: int = 0

    # Token usage metrics
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Request/response metrics
    request_size: int = 0
    response_size: int = 0

    # Provider-specific metrics
    provider_name: str = ""
    model_name: str = ""

    # Correlation tracking
    correlation_id: str = ""
    operation_name: str = ""

    # Success/error metrics
    success: bool = True
    error_type: str = ""
    error_message: str = ""

    # Timestamps
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    def finalize(self, success: bool = True, error: Exception | None = None) -> None:
        """Finalize metrics collection.

        Args:
            success: Whether the operation succeeded
            error: Optional exception if operation failed
        """
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = success

        if error:
            self.success = False
            self.error_type = type(error).__name__
            self.error_message = str(error)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary format.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "timing": {
                "duration": self.duration,
                "cpu_time": self.cpu_time,
                "wall_time": self.wall_time,
            },
            "memory": {
                "before": self.memory_before,
                "after": self.memory_after,
                "peak": self.memory_peak,
                "delta": self.memory_delta,
            },
            "tokens": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            },
            "request": {
                "size": self.request_size,
                "response_size": self.response_size,
            },
            "provider": {
                "name": self.provider_name,
                "model": self.model_name,
            },
            "tracking": {
                "correlation_id": self.correlation_id,
                "operation_name": self.operation_name,
            },
            "status": {
                "success": self.success,
                "error_type": self.error_type,
                "error_message": self.error_message,
            },
            "timestamps": {
                "start": self.start_time.isoformat() if self.start_time else None,
                "end": self.end_time.isoformat() if self.end_time else None,
            },
        }


@dataclass
class ProviderBenchmark:
    """Benchmark results for a provider/model combination.

    Stores comprehensive benchmarking data including:
    - Performance metrics (response time percentiles, throughput)
    - Reliability metrics (success rate, error rate, timeouts)
    - Cost metrics (tokens per second, cost per token)
    - Resource usage (memory, CPU efficiency)
    """

    provider_name: str
    model_name: str

    # Performance metrics
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0

    # Reliability metrics
    success_rate: float = 0.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0

    # Cost metrics (tokens per second, etc.)
    tokens_per_second: float = 0.0
    cost_per_token: float | None = None

    # Resource usage
    avg_memory_usage: float = 0.0
    cpu_efficiency: float = 0.0

    # Sample size
    total_requests: int = 0
    measurement_period: timedelta = field(default_factory=lambda: timedelta(minutes=1))

    def to_dict(self) -> dict[str, Any]:
        """Convert benchmark to dictionary format.

        Returns:
            Dictionary representation of benchmark
        """
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "performance": {
                "avg_response_time": self.avg_response_time,
                "p95_response_time": self.p95_response_time,
                "p99_response_time": self.p99_response_time,
                "requests_per_second": self.requests_per_second,
            },
            "reliability": {
                "success_rate": self.success_rate,
                "error_rate": self.error_rate,
                "timeout_rate": self.timeout_rate,
            },
            "cost": {
                "tokens_per_second": self.tokens_per_second,
                "cost_per_token": self.cost_per_token,
            },
            "resources": {
                "avg_memory_usage": self.avg_memory_usage,
                "cpu_efficiency": self.cpu_efficiency,
            },
            "sample": {
                "total_requests": self.total_requests,
                "measurement_period_seconds": self.measurement_period.total_seconds(),
            },
        }


@dataclass
class OperationStats:
    """Statistical analysis for operation timings.

    Provides statistical measures including:
    - Central tendency (mean, median)
    - Percentiles (p95, p99)
    - Range (min, max)
    - Sample count
    """

    operation_name: str
    count: int = 0
    mean: float = 0.0
    median: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    min: float = 0.0
    max: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary format.

        Returns:
            Dictionary representation of stats
        """
        return {
            "operation": self.operation_name,
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "p95": self.p95,
            "p99": self.p99,
            "min": self.min,
            "max": self.max,
        }
