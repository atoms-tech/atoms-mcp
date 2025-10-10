"""Performance monitoring system for operations and resource usage.

This module provides the core PerformanceMonitor class for tracking:
- Operation timing and resource usage
- System metrics (CPU, memory)
- Performance trends over time
- Automatic metrics collection with context managers
"""

import logging
import os
import threading
import time
import uuid
import weakref
from collections import defaultdict, deque
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from typing import Any

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from pydevkit.tracing import get_correlation_id

from .metrics import OperationStats, PerformanceMetrics

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Central performance monitoring system.

    Features:
    - Real-time performance metrics collection
    - Resource usage tracking (CPU, memory)
    - Operation timing statistics
    - Context manager support (sync & async)
    - Correlation ID integration for distributed tracing
    - Weak references for tracked objects
    """

    def __init__(self, enable_detailed_metrics: bool = True):
        """Initialize performance monitor.

        Args:
            enable_detailed_metrics: Whether to collect detailed system metrics (requires psutil)
        """
        self.enable_detailed_metrics = enable_detailed_metrics and PSUTIL_AVAILABLE
        self.metrics_buffer: deque = deque(maxlen=10000)  # Circular buffer
        self._lock = threading.RLock()
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None

        # Performance tracking
        self._operation_timings: dict[str, list[float]] = defaultdict(list)
        self._memory_snapshots: list[tuple] = []
        self._start_time = time.time()

        # Weak references for resource cleanup
        self._tracked_objects: weakref.WeakSet = weakref.WeakSet()

        if not PSUTIL_AVAILABLE and enable_detailed_metrics:
            logger.warning(
                "psutil not available - detailed metrics disabled. " "Install with: pip install psutil"
            )

        logger.info(f"PerformanceMonitor initialized (detailed_metrics={self.enable_detailed_metrics})")

    def get_system_metrics(self) -> dict[str, Any]:
        """Get current system performance metrics.

        Returns:
            Dictionary containing process and system metrics, or empty dict if psutil unavailable
        """
        if not PSUTIL_AVAILABLE or not self._process:
            return {}

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
        """Context manager for measuring operation performance.

        Args:
            operation_name: Name of the operation being measured
            provider_name: Optional provider name (for LLM operations)
            model_name: Optional model name (for LLM operations)

        Yields:
            PerformanceMetrics object that can be updated during operation

        Example:
            >>> monitor = PerformanceMonitor()
            >>> with monitor.measure_operation("api_call") as metrics:
            ...     # perform operation
            ...     metrics.input_tokens = 100
        """
        correlation_id = get_correlation_id() or str(uuid.uuid4())

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            provider_name=provider_name,
            model_name=model_name,
            correlation_id=correlation_id,
            start_time=datetime.now(),
        )

        # Capture initial state
        if self.enable_detailed_metrics and self._process:
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

            if self.enable_detailed_metrics and self._process:
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
                f"Completed operation: {operation_name} in {metrics.wall_time:.3f}s "
                f"(correlation_id={correlation_id})"
            )

    @asynccontextmanager
    async def measure_async_operation(
        self, operation_name: str, provider_name: str = "", model_name: str = ""
    ) -> AsyncGenerator[PerformanceMetrics, None]:
        """Async context manager for measuring operation performance.

        Args:
            operation_name: Name of the operation being measured
            provider_name: Optional provider name (for LLM operations)
            model_name: Optional model name (for LLM operations)

        Yields:
            PerformanceMetrics object that can be updated during operation

        Example:
            >>> monitor = PerformanceMonitor()
            >>> async with monitor.measure_async_operation("async_api_call") as metrics:
            ...     # perform async operation
            ...     metrics.output_tokens = 200
        """
        correlation_id = get_correlation_id() or str(uuid.uuid4())

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            provider_name=provider_name,
            model_name=model_name,
            correlation_id=correlation_id,
            start_time=datetime.now(),
        )

        # Capture initial state
        if self.enable_detailed_metrics and self._process:
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

            if self.enable_detailed_metrics and self._process:
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
                f"Completed async operation: {operation_name} in {metrics.wall_time:.3f}s "
                f"(correlation_id={correlation_id})"
            )

    def get_operation_stats(self, operation_name: str) -> OperationStats:
        """Get statistical analysis for an operation.

        Args:
            operation_name: Name of the operation to analyze

        Returns:
            OperationStats object with statistical measures
        """
        with self._lock:
            timings = self._operation_timings.get(operation_name, [])

        if not timings:
            return OperationStats(operation_name=operation_name)

        timings_sorted = sorted(timings)
        count = len(timings_sorted)

        return OperationStats(
            operation_name=operation_name,
            count=count,
            mean=sum(timings) / count,
            median=timings_sorted[count // 2],
            p95=timings_sorted[int(count * 0.95)] if count > 20 else timings_sorted[-1],
            p99=timings_sorted[int(count * 0.99)] if count > 100 else timings_sorted[-1],
            min=min(timings),
            max=max(timings),
        )

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary.

        Returns:
            Dictionary containing system metrics, operation stats, and overall status
        """
        system_metrics = self.get_system_metrics()

        # Operation performance summary
        operation_stats = {}
        for op_name in list(self._operation_timings.keys()):
            stats = self.get_operation_stats(op_name)
            operation_stats[op_name] = stats.to_dict()

        return {
            "system": system_metrics,
            "operations": operation_stats,
            "metrics_collected": len(self.metrics_buffer),
            "monitoring_enabled": self.enable_detailed_metrics,
            "uptime_hours": (time.time() - self._start_time) / 3600,
        }

    def track_object(self, obj: Any, name: str = "") -> None:
        """Track an object for memory leak detection using weak references.

        Args:
            obj: Object to track
            name: Optional name for logging
        """
        self._tracked_objects.add(obj)
        if name:
            logger.debug(f"Tracking object: {name} (type={type(obj).__name__})")

    def clear_metrics(self, older_than_hours: int = 24) -> None:
        """Clear old metrics to prevent memory bloat.

        Args:
            older_than_hours: Clear metrics older than this many hours
        """
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
    """Get the global performance monitor instance.

    Returns:
        Shared PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        enable_detailed = os.getenv("PYDEVKIT_DETAILED_METRICS", "true").lower() in ("true", "1", "yes")
        _performance_monitor = PerformanceMonitor(enable_detailed_metrics=enable_detailed)
    return _performance_monitor
