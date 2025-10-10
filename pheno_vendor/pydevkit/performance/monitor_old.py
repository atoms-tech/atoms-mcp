"""Performance monitoring and metrics collection for PyDevKit.

This module provides comprehensive performance monitoring capabilities including:
- Real-time performance metrics collection
- Provider performance benchmarking
- Resource usage tracking
- Memory optimization utilities
- Connection pooling management
- Correlation ID tracking for distributed tracing

Features:
- Async/sync performance measurement
- Provider comparison and optimization
- Memory leak detection
- Connection pool health monitoring
- Structured logging with correlation IDs
- Performance regression testing support
"""

import asyncio
import functools
import logging
import os
import threading
import time
import uuid
import weakref
from collections import defaultdict, deque
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, TypeVar

import psutil

# Import correlation ID utilities
from pydevkit.correlation_id import get_correlation_id

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class PerformanceMetrics:
    """Container for performance measurements."""

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

    def finalize(self, success: bool = True, error: Exception | None = None):
        """Finalize metrics collection."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = success

        if error:
            self.success = False
            self.error_type = type(error).__name__
            self.error_message = str(error)


@dataclass
class ProviderBenchmark:
    """Benchmark results for a provider."""

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


class PerformanceMonitor:
    """Central performance monitoring system."""

    def __init__(self, enable_detailed_metrics: bool = True):
        self.enable_detailed_metrics = enable_detailed_metrics
        self.metrics_buffer: deque = deque(maxlen=10000)  # Circular buffer
        self.provider_benchmarks: dict[str, ProviderBenchmark] = {}
        self.connection_pools: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._process = psutil.Process()

        # Performance tracking
        self._operation_timings: dict[str, list[float]] = defaultdict(list)
        self._memory_snapshots: list[tuple] = []
        self._start_time = time.time()

        # Weak references for resource cleanup
        self._tracked_objects: weakref.WeakSet = weakref.WeakSet()

        logger.info(f"PerformanceMonitor initialized (detailed_metrics={enable_detailed_metrics})")

    def get_system_metrics(self) -> dict[str, Any]:
        """Get current system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = self._process.cpu_percent()
            cpu_times = self._process.cpu_times()

            # Memory metrics
            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()

            # System-wide metrics
            system_cpu = psutil.cpu_percent(interval=None)
            system_memory = psutil.virtual_memory()

            return {
                # Process metrics
                "process_cpu_percent": cpu_percent,
                "process_cpu_time_user": cpu_times.user,
                "process_cpu_time_system": cpu_times.system,
                "process_memory_rss": memory_info.rss,
                "process_memory_vms": memory_info.vms,
                "process_memory_percent": memory_percent,
                # System metrics
                "system_cpu_percent": system_cpu,
                "system_memory_total": system_memory.total,
                "system_memory_available": system_memory.available,
                "system_memory_percent": system_memory.percent,
                # Runtime metrics
                "uptime_seconds": time.time() - self._start_time,
                "tracked_objects": len(self._tracked_objects),
                "metrics_buffer_size": len(self.metrics_buffer),
            }
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return {}

    @contextmanager
    def measure_operation(self, operation_name: str, provider_name: str = "", model_name: str = ""):
        """Context manager for measuring operation performance."""
        correlation_id = get_correlation_id() or str(uuid.uuid4())

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            provider_name=provider_name,
            model_name=model_name,
            correlation_id=correlation_id,
            start_time=datetime.now(),
        )

        # Capture initial state
        if self.enable_detailed_metrics:
            metrics.memory_before = self._process.memory_info().rss
            metrics.cpu_time = self._process.cpu_times().user + self._process.cpu_times().system

        start_time = time.perf_counter()

        try:
            logger.debug(f"Starting operation: {operation_name} (correlation_id={correlation_id})")
            yield metrics

            # Mark as successful if we reach here
            metrics.success = True

        except Exception as e:
            # Record error details
            metrics.finalize(success=False, error=e)
            logger.error(f"Operation failed: {operation_name} (correlation_id={correlation_id}): {e}")
            raise

        finally:
            # Calculate final metrics
            end_time = time.perf_counter()
            metrics.wall_time = end_time - start_time

            if self.enable_detailed_metrics:
                metrics.memory_after = self._process.memory_info().rss
                metrics.memory_delta = metrics.memory_after - metrics.memory_before
                final_cpu_time = self._process.cpu_times().user + self._process.cpu_times().system
                metrics.cpu_time = final_cpu_time - metrics.cpu_time

            metrics.finalize()

            # Store metrics
            with self._lock:
                self.metrics_buffer.append(metrics)
                self._operation_timings[operation_name].append(metrics.wall_time)

                # Keep only recent timings for each operation
                if len(self._operation_timings[operation_name]) > 1000:
                    self._operation_timings[operation_name] = self._operation_timings[operation_name][-500:]

            logger.debug(
                f"Completed operation: {operation_name} in {metrics.wall_time:.3f}s (correlation_id={correlation_id})"
            )

    @asynccontextmanager
    async def measure_async_operation(
        self, operation_name: str, provider_name: str = "", model_name: str = ""
    ) -> AsyncGenerator[PerformanceMetrics, None]:
        """Async context manager for measuring operation performance."""
        correlation_id = get_correlation_id() or str(uuid.uuid4())

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            provider_name=provider_name,
            model_name=model_name,
            correlation_id=correlation_id,
            start_time=datetime.now(),
        )

        # Capture initial state
        if self.enable_detailed_metrics:
            metrics.memory_before = self._process.memory_info().rss
            metrics.cpu_time = self._process.cpu_times().user + self._process.cpu_times().system

        start_time = time.perf_counter()

        try:
            logger.debug(f"Starting async operation: {operation_name} (correlation_id={correlation_id})")
            yield metrics

            # Mark as successful if we reach here
            metrics.success = True

        except Exception as e:
            # Record error details
            metrics.finalize(success=False, error=e)
            logger.error(f"Async operation failed: {operation_name} (correlation_id={correlation_id}): {e}")
            raise

        finally:
            # Calculate final metrics
            end_time = time.perf_counter()
            metrics.wall_time = end_time - start_time

            if self.enable_detailed_metrics:
                metrics.memory_after = self._process.memory_info().rss
                metrics.memory_delta = metrics.memory_after - metrics.memory_before
                final_cpu_time = self._process.cpu_times().user + self._process.cpu_times().system
                metrics.cpu_time = final_cpu_time - metrics.cpu_time

            metrics.finalize()

            # Store metrics
            with self._lock:
                self.metrics_buffer.append(metrics)
                self._operation_timings[operation_name].append(metrics.wall_time)

                # Keep only recent timings for each operation
                if len(self._operation_timings[operation_name]) > 1000:
                    self._operation_timings[operation_name] = self._operation_timings[operation_name][-500:]

            logger.debug(
                f"Completed async operation: {operation_name} in {metrics.wall_time:.3f}s (correlation_id={correlation_id})"
            )

    def get_operation_stats(self, operation_name: str) -> dict[str, float]:
        """Get statistical analysis for an operation."""
        with self._lock:
            timings = self._operation_timings.get(operation_name, [])

        if not timings:
            return {}

        timings_sorted = sorted(timings)
        count = len(timings_sorted)

        return {
            "count": count,
            "mean": sum(timings) / count,
            "median": timings_sorted[count // 2],
            "p95": timings_sorted[int(count * 0.95)] if count > 20 else timings_sorted[-1],
            "p99": timings_sorted[int(count * 0.99)] if count > 100 else timings_sorted[-1],
            "min": min(timings),
            "max": max(timings),
        }

    def benchmark_provider(
        self, provider_name: str, model_name: str, num_requests: int = 10, concurrent: bool = False
    ) -> ProviderBenchmark:
        """Benchmark a specific provider/model combination."""
        from providers.registry import ModelProviderRegistry

        registry = ModelProviderRegistry()
        provider = registry.get_provider_for_model(model_name)

        if not provider:
            raise ValueError(f"No provider found for model: {model_name}")

        benchmark = ProviderBenchmark(provider_name=provider_name, model_name=model_name)

        # Simple benchmark prompt
        test_prompt = "Explain the concept of artificial intelligence in one sentence."

        response_times = []
        successes = 0
        errors = 0
        timeouts = 0
        total_tokens = 0

        start_time = datetime.now()

        for i in range(num_requests):
            try:
                with self.measure_operation(f"benchmark_{provider_name}_{i}", provider_name, model_name) as metrics:
                    response = provider.generate_content(
                        prompt=test_prompt, model_name=model_name, temperature=0.3, max_output_tokens=100
                    )

                    # Track token usage
                    total_tokens += response.usage.get("total_tokens", 0)
                    metrics.input_tokens = response.usage.get("input_tokens", 0)
                    metrics.output_tokens = response.usage.get("output_tokens", 0)
                    metrics.total_tokens = response.usage.get("total_tokens", 0)

                response_times.append(metrics.wall_time)
                successes += 1

            except TimeoutError:
                timeouts += 1
            except Exception as e:
                errors += 1
                logger.debug(f"Benchmark error for {provider_name}/{model_name}: {e}")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # Calculate statistics
        if response_times:
            response_times_sorted = sorted(response_times)
            benchmark.avg_response_time = sum(response_times) / len(response_times)
            benchmark.p95_response_time = response_times_sorted[int(len(response_times) * 0.95)]
            benchmark.p99_response_time = response_times_sorted[int(len(response_times) * 0.99)]

        benchmark.success_rate = successes / num_requests
        benchmark.error_rate = errors / num_requests
        benchmark.timeout_rate = timeouts / num_requests
        benchmark.requests_per_second = num_requests / total_time if total_time > 0 else 0
        benchmark.tokens_per_second = total_tokens / total_time if total_time > 0 else 0
        benchmark.total_requests = num_requests
        benchmark.measurement_period = timedelta(seconds=total_time)

        # Store benchmark results
        with self._lock:
            benchmark_key = f"{provider_name}_{model_name}"
            self.provider_benchmarks[benchmark_key] = benchmark

        logger.info(
            f"Benchmark completed for {provider_name}/{model_name}: "
            f"{benchmark.avg_response_time:.3f}s avg, {benchmark.success_rate:.1%} success rate"
        )

        return benchmark

    def get_memory_usage_trend(self, window_minutes: int = 10) -> list[dict[str, Any]]:
        """Get memory usage trend over time."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)

        with self._lock:
            recent_metrics = [m for m in self.metrics_buffer if m.start_time >= cutoff_time]

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
        """Detect potential memory leaks."""
        trend_data = self.get_memory_usage_trend(window_minutes=30)

        if len(trend_data) < 5:
            return {"status": "insufficient_data", "message": "Need more data points"}

        # Calculate memory growth rate
        first_avg = trend_data[0]["avg_memory_mb"]
        last_avg = trend_data[-1]["avg_memory_mb"]
        memory_growth = last_avg - first_avg

        # Calculate trend slope
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
            "tracked_objects": len(self._tracked_objects),
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        system_metrics = self.get_system_metrics()
        memory_leak_status = self.detect_memory_leaks()

        # Operation performance summary
        operation_stats = {}
        for op_name in list(self._operation_timings.keys()):
            operation_stats[op_name] = self.get_operation_stats(op_name)

        # Provider benchmark summary
        benchmark_summary = {}
        with self._lock:
            for key, benchmark in self.provider_benchmarks.items():
                benchmark_summary[key] = {
                    "avg_response_time": benchmark.avg_response_time,
                    "success_rate": benchmark.success_rate,
                    "tokens_per_second": benchmark.tokens_per_second,
                    "total_requests": benchmark.total_requests,
                }

        return {
            "system": system_metrics,
            "memory_leak_detection": memory_leak_status,
            "operations": operation_stats,
            "provider_benchmarks": benchmark_summary,
            "metrics_collected": len(self.metrics_buffer),
            "monitoring_enabled": self.enable_detailed_metrics,
            "uptime_hours": (time.time() - self._start_time) / 3600,
        }

    def track_object(self, obj: Any, name: str = ""):
        """Track an object for memory leak detection."""
        self._tracked_objects.add(obj)
        if name:
            logger.debug(f"Tracking object: {name} (type={type(obj).__name__})")

    def clear_metrics(self, older_than_hours: int = 24):
        """Clear old metrics to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        with self._lock:
            # Clear old metrics from buffer
            self.metrics_buffer = deque(
                [m for m in self.metrics_buffer if m.start_time >= cutoff_time], maxlen=self.metrics_buffer.maxlen
            )

            # Clear old operation timings (keep recent ones)
            for op_name in list(self._operation_timings.keys()):
                if len(self._operation_timings[op_name]) > 100:
                    self._operation_timings[op_name] = self._operation_timings[op_name][-50:]

        logger.info(f"Cleared metrics older than {older_than_hours} hours")


# Global performance monitor instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        enable_detailed = os.getenv("ZEN_DETAILED_METRICS", "true").lower() in ("true", "1", "yes")
        _performance_monitor = PerformanceMonitor(enable_detailed_metrics=enable_detailed)
    return _performance_monitor


def measure_performance(operation_name: str = "", provider_name: str = "", model_name: str = ""):
    """Decorator for measuring function performance."""

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                op_name = operation_name or f"{func.__module__}.{func.__name__}"

                async with monitor.measure_async_operation(op_name, provider_name, model_name) as metrics:
                    result = await func(*args, **kwargs)

                    # Try to extract token usage from result if it's a response object
                    if hasattr(result, "usage") and isinstance(result.usage, dict):
                        metrics.input_tokens = result.usage.get("input_tokens", 0)
                        metrics.output_tokens = result.usage.get("output_tokens", 0)
                        metrics.total_tokens = result.usage.get("total_tokens", 0)

                    return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                op_name = operation_name or f"{func.__module__}.{func.__name__}"

                with monitor.measure_operation(op_name, provider_name, model_name) as metrics:
                    result = func(*args, **kwargs)

                    # Try to extract token usage from result if it's a response object
                    if hasattr(result, "usage") and isinstance(result.usage, dict):
                        metrics.input_tokens = result.usage.get("input_tokens", 0)
                        metrics.output_tokens = result.usage.get("output_tokens", 0)
                        metrics.total_tokens = result.usage.get("total_tokens", 0)

                    return result

            return sync_wrapper

    return decorator


# Convenience functions for common use cases
def benchmark_all_providers(models_to_test: list[str] = None, num_requests: int = 5) -> dict[str, ProviderBenchmark]:
    """Benchmark all available providers with specified models."""
    from providers.registry import ModelProviderRegistry

    monitor = get_performance_monitor()
    registry = ModelProviderRegistry()

    if not models_to_test:
        models_to_test = ["gemini-2.5-flash", "gpt-4o", "grok-beta"]  # Common fast models

    results = {}

    for model_name in models_to_test:
        provider = registry.get_provider_for_model(model_name)
        if provider:
            try:
                provider_name = provider.get_provider_type().value
                benchmark = monitor.benchmark_provider(provider_name, model_name, num_requests)
                results[f"{provider_name}_{model_name}"] = benchmark
            except Exception as e:
                logger.warning(f"Failed to benchmark {model_name}: {e}")

    return results


def get_fastest_provider_for_operation(operation_type: str = "generation") -> str | None:
    """Get the fastest provider for a specific operation type."""
    monitor = get_performance_monitor()

    best_provider = None
    best_time = float("inf")

    with monitor._lock:
        for _key, benchmark in monitor.provider_benchmarks.items():
            if benchmark.avg_response_time < best_time and benchmark.success_rate > 0.8:
                best_time = benchmark.avg_response_time
                best_provider = benchmark.provider_name

    return best_provider
