"""Performance monitoring and optimization utilities.

This module provides comprehensive performance monitoring capabilities including:
- Real-time performance metrics collection
- Provider performance benchmarking
- Resource usage tracking (CPU, memory)
- Memory leak detection
- Performance decorators for automatic tracking
- Correlation ID support for distributed tracing

Basic usage:
    >>> from pydevkit.performance import get_performance_monitor, measure_performance
    >>>
    >>> # Using context manager
    >>> monitor = get_performance_monitor()
    >>> with monitor.measure_operation("my_operation") as metrics:
    ...     # perform operation
    ...     metrics.input_tokens = 100
    >>>
    >>> # Using decorator
    >>> @measure_performance("my_function")
    ... def my_function():
    ...     return "result"
"""

from pydevkit.performance.benchmarking import Benchmarker
from pydevkit.performance.decorators import measure_method, measure_performance
from pydevkit.performance.memory import MemoryLeakDetector
from pydevkit.performance.metrics import OperationStats, PerformanceMetrics, ProviderBenchmark
from pydevkit.performance.monitor import PerformanceMonitor, get_performance_monitor
from pydevkit.performance.optimizer import (
    CompressionResult,
    ContextManager,
    GarbageCollector,
    LargeFileHandler,
    MemoryMonitor,
    MemoryOptimizer,
    MemoryStats,
    TextCompressor,
    compress_large_context,
    get_compressed_context,
    get_memory_optimizer,
    get_memory_recommendations,
    optimize_memory_now,
)

__all__ = [
    # Core monitoring
    "PerformanceMonitor",
    "get_performance_monitor",
    # Metrics
    "PerformanceMetrics",
    "ProviderBenchmark",
    "OperationStats",
    # Decorators
    "measure_performance",
    "measure_method",
    # Benchmarking
    "Benchmarker",
    # Memory leak detection
    "MemoryLeakDetector",
    # Memory optimization (from optimizer.py)
    "MemoryMonitor",
    "MemoryStats",
    "CompressionResult",
    "TextCompressor",
    "ContextManager",
    "LargeFileHandler",
    "GarbageCollector",
    "MemoryOptimizer",
    "get_memory_optimizer",
    "optimize_memory_now",
    "get_memory_recommendations",
    "compress_large_context",
    "get_compressed_context",
]
