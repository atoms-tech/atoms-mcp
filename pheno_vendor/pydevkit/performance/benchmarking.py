"""Benchmarking utilities for performance testing.

This module provides tools for:
- Provider benchmarking
- Performance comparison
- Load testing utilities
- Statistical analysis of benchmark results
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Callable

from .metrics import ProviderBenchmark

logger = logging.getLogger(__name__)


class Benchmarker:
    """Performance benchmarking utilities."""

    def __init__(self, monitor):
        """Initialize benchmarker.

        Args:
            monitor: PerformanceMonitor instance
        """
        self.monitor = monitor
        self.provider_benchmarks: dict[str, ProviderBenchmark] = {}

    def benchmark_function(
        self,
        func: Callable,
        num_iterations: int = 10,
        operation_name: str = "",
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Benchmark a function or callable.

        Args:
            func: Function to benchmark
            num_iterations: Number of times to run the function
            operation_name: Name for the benchmark operation
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Dictionary with benchmark results
        """
        op_name = operation_name or f"benchmark_{func.__name__}"
        response_times = []
        successes = 0
        errors = 0

        start_time = datetime.now()

        for i in range(num_iterations):
            try:
                with self.monitor.measure_operation(f"{op_name}_{i}") as metrics:
                    result = func(*args, **kwargs)

                response_times.append(metrics.wall_time)
                successes += 1

            except Exception as e:
                errors += 1
                logger.debug(f"Benchmark error for {op_name}: {e}")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # Calculate statistics
        stats = {}
        if response_times:
            response_times_sorted = sorted(response_times)
            stats = {
                "avg_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": response_times_sorted[int(len(response_times) * 0.95)],
                "p99_response_time": response_times_sorted[int(len(response_times) * 0.99)],
            }

        return {
            "operation_name": op_name,
            "total_iterations": num_iterations,
            "successes": successes,
            "errors": errors,
            "success_rate": successes / num_iterations if num_iterations > 0 else 0,
            "error_rate": errors / num_iterations if num_iterations > 0 else 0,
            "total_time_seconds": total_time,
            "iterations_per_second": num_iterations / total_time if total_time > 0 else 0,
            **stats,
        }

    def benchmark_provider(
        self,
        provider_func: Callable,
        provider_name: str,
        model_name: str,
        num_requests: int = 10,
        **kwargs,
    ) -> ProviderBenchmark:
        """Benchmark a provider/model combination.

        Args:
            provider_func: Function that calls the provider
            provider_name: Name of the provider
            model_name: Name of the model
            num_requests: Number of requests to make
            **kwargs: Additional arguments for the provider function

        Returns:
            ProviderBenchmark object with results
        """
        benchmark = ProviderBenchmark(provider_name=provider_name, model_name=model_name)

        response_times = []
        successes = 0
        errors = 0
        timeouts = 0
        total_tokens = 0

        start_time = datetime.now()

        for i in range(num_requests):
            try:
                with self.monitor.measure_operation(
                    f"benchmark_{provider_name}_{i}", provider_name, model_name
                ) as metrics:
                    result = provider_func(**kwargs)

                    # Try to extract token usage from result
                    if hasattr(result, "usage") and isinstance(result.usage, dict):
                        total_tokens += result.usage.get("total_tokens", 0)
                        metrics.input_tokens = result.usage.get("input_tokens", 0)
                        metrics.output_tokens = result.usage.get("output_tokens", 0)
                        metrics.total_tokens = result.usage.get("total_tokens", 0)

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
        with self.monitor._lock:
            benchmark_key = f"{provider_name}_{model_name}"
            self.provider_benchmarks[benchmark_key] = benchmark

        logger.info(
            f"Benchmark completed for {provider_name}/{model_name}: "
            f"{benchmark.avg_response_time:.3f}s avg, {benchmark.success_rate:.1%} success rate"
        )

        return benchmark

    def compare_providers(self, benchmark_keys: list[str] = None) -> dict[str, Any]:
        """Compare benchmark results across providers.

        Args:
            benchmark_keys: Optional list of specific benchmarks to compare

        Returns:
            Dictionary with comparison results
        """
        if benchmark_keys is None:
            benchmarks_to_compare = self.provider_benchmarks
        else:
            benchmarks_to_compare = {
                k: v for k, v in self.provider_benchmarks.items() if k in benchmark_keys
            }

        if not benchmarks_to_compare:
            return {"status": "no_benchmarks", "message": "No benchmarks available for comparison"}

        # Find best performers
        best_response_time = min(
            benchmarks_to_compare.items(),
            key=lambda x: x[1].avg_response_time if x[1].avg_response_time > 0 else float("inf"),
        )

        best_success_rate = max(benchmarks_to_compare.items(), key=lambda x: x[1].success_rate)

        best_throughput = max(benchmarks_to_compare.items(), key=lambda x: x[1].requests_per_second)

        return {
            "total_benchmarks": len(benchmarks_to_compare),
            "best_response_time": {
                "provider": best_response_time[0],
                "avg_response_time": best_response_time[1].avg_response_time,
            },
            "best_success_rate": {
                "provider": best_success_rate[0],
                "success_rate": best_success_rate[1].success_rate,
            },
            "best_throughput": {
                "provider": best_throughput[0],
                "requests_per_second": best_throughput[1].requests_per_second,
            },
            "all_benchmarks": {k: v.to_dict() for k, v in benchmarks_to_compare.items()},
        }

    def get_fastest_provider(self, min_success_rate: float = 0.8) -> str | None:
        """Get the fastest provider based on benchmarks.

        Args:
            min_success_rate: Minimum success rate threshold

        Returns:
            Provider name or None if no suitable provider found
        """
        best_provider = None
        best_time = float("inf")

        with self.monitor._lock:
            for key, benchmark in self.provider_benchmarks.items():
                if benchmark.avg_response_time < best_time and benchmark.success_rate >= min_success_rate:
                    best_time = benchmark.avg_response_time
                    best_provider = benchmark.provider_name

        return best_provider

    def get_benchmark_summary(self) -> dict[str, Any]:
        """Get summary of all benchmarks.

        Returns:
            Dictionary with benchmark summary
        """
        benchmark_summary = {}
        with self.monitor._lock:
            for key, benchmark in self.provider_benchmarks.items():
                benchmark_summary[key] = {
                    "avg_response_time": benchmark.avg_response_time,
                    "success_rate": benchmark.success_rate,
                    "tokens_per_second": benchmark.tokens_per_second,
                    "total_requests": benchmark.total_requests,
                }

        return benchmark_summary
