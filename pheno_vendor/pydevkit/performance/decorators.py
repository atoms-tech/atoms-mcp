"""Performance measurement decorators.

This module provides decorators for automatic performance tracking:
- @measure_performance: Track sync/async function execution
- Automatic token usage extraction
- Integration with PerformanceMonitor
"""

import asyncio
import functools
from typing import Any, Callable, TypeVar

from .monitor import get_performance_monitor

F = TypeVar("F", bound=Callable[..., Any])


def measure_performance(operation_name: str = "", provider_name: str = "", model_name: str = "") -> Callable[[F], F]:
    """Decorator for measuring function performance.

    Automatically measures execution time, memory usage, and other metrics
    for both synchronous and asynchronous functions.

    Args:
        operation_name: Optional custom operation name (defaults to function name)
        provider_name: Optional provider name (for LLM operations)
        model_name: Optional model name (for LLM operations)

    Returns:
        Decorated function that measures performance

    Example:
        >>> @measure_performance("api_call")
        ... def call_api():
        ...     # perform API call
        ...     return result

        >>> @measure_performance("llm_call", provider_name="openai", model_name="gpt-4")
        ... async def call_llm():
        ...     # perform LLM call
        ...     return response
    """

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

            return async_wrapper  # type: ignore
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

            return sync_wrapper  # type: ignore

    return decorator


def measure_method(operation_name: str = "", provider_name: str = "", model_name: str = "") -> Callable[[F], F]:
    """Decorator for measuring class method performance.

    Similar to measure_performance but designed for class methods.
    Automatically includes class name in operation name.

    Args:
        operation_name: Optional custom operation name
        provider_name: Optional provider name (for LLM operations)
        model_name: Optional model name (for LLM operations)

    Returns:
        Decorated method that measures performance

    Example:
        >>> class MyService:
        ...     @measure_method("process_data")
        ...     def process(self, data):
        ...         # process data
        ...         return result
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                monitor = get_performance_monitor()
                class_name = self.__class__.__name__
                op_name = operation_name or f"{class_name}.{func.__name__}"

                async with monitor.measure_async_operation(op_name, provider_name, model_name) as metrics:
                    result = await func(self, *args, **kwargs)

                    # Try to extract token usage from result
                    if hasattr(result, "usage") and isinstance(result.usage, dict):
                        metrics.input_tokens = result.usage.get("input_tokens", 0)
                        metrics.output_tokens = result.usage.get("output_tokens", 0)
                        metrics.total_tokens = result.usage.get("total_tokens", 0)

                    return result

            return async_wrapper  # type: ignore
        else:

            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                monitor = get_performance_monitor()
                class_name = self.__class__.__name__
                op_name = operation_name or f"{class_name}.{func.__name__}"

                with monitor.measure_operation(op_name, provider_name, model_name) as metrics:
                    result = func(self, *args, **kwargs)

                    # Try to extract token usage from result
                    if hasattr(result, "usage") and isinstance(result.usage, dict):
                        metrics.input_tokens = result.usage.get("input_tokens", 0)
                        metrics.output_tokens = result.usage.get("output_tokens", 0)
                        metrics.total_tokens = result.usage.get("total_tokens", 0)

                    return result

            return sync_wrapper  # type: ignore

    return decorator
