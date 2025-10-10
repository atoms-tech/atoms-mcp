"""Convenient decorators for automatic span creation.

Based on 2025 Python best practices:
- Support for both sync and async functions
- Automatic exception handling and recording
- Function metadata captured as span attributes
- Minimal performance overhead
- Type-safe with proper annotations
"""

import functools
import inspect
from typing import Any, Callable, Optional, TypeVar, cast

from observability.tracing.tracer import DistributedTracer, SpanKind


# Global tracer instance (can be set by application)
_default_tracer: Optional[DistributedTracer] = None


def set_default_tracer(tracer: DistributedTracer) -> None:
    """Set the default tracer for decorators.

    Example:
        >>> tracer = DistributedTracer("my-service")
        >>> set_default_tracer(tracer)
    """
    global _default_tracer
    _default_tracer = tracer


def get_default_tracer() -> Optional[DistributedTracer]:
    """Get the default tracer."""
    return _default_tracer


F = TypeVar("F", bound=Callable[..., Any])


def trace_function(
    name: Optional[str] = None,
    *,
    kind: SpanKind = SpanKind.INTERNAL,
    tracer: Optional[DistributedTracer] = None,
    capture_args: bool = False,
    capture_result: bool = False,
) -> Callable[[F], F]:
    """Decorator for tracing synchronous functions.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        tracer: Tracer to use (defaults to global tracer)
        capture_args: Whether to capture function arguments as span attributes
        capture_result: Whether to capture return value as span attribute

    Example:
        >>> @trace_function(capture_args=True)
        ... def fetch_user(user_id: str) -> dict:
        ...     return {"id": user_id, "name": "Alice"}
    """

    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get tracer
            active_tracer = tracer or _default_tracer
            if not active_tracer:
                # No tracer available, just call function
                return func(*args, **kwargs)

            # Start span
            with active_tracer.start_span(span_name, kind=kind) as span:
                # Capture function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Capture arguments if requested
                if capture_args:
                    # Get argument names
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    for arg_name, arg_value in bound_args.arguments.items():
                        # Only capture simple types
                        if isinstance(arg_value, (str, int, float, bool, type(None))):
                            span.set_attribute(f"function.arg.{arg_name}", arg_value)
                        else:
                            span.set_attribute(f"function.arg.{arg_name}", str(type(arg_value).__name__))

                try:
                    result = func(*args, **kwargs)

                    # Capture result if requested
                    if capture_result:
                        if isinstance(result, (str, int, float, bool, type(None))):
                            span.set_attribute("function.result", result)
                        else:
                            span.set_attribute("function.result.type", type(result).__name__)

                    return result

                except Exception:
                    # Exception is automatically recorded by span manager
                    raise

        return cast(F, wrapper)

    return decorator


def trace_async(
    name: Optional[str] = None,
    *,
    kind: SpanKind = SpanKind.INTERNAL,
    tracer: Optional[DistributedTracer] = None,
    capture_args: bool = False,
    capture_result: bool = False,
) -> Callable[[F], F]:
    """Decorator for tracing asynchronous functions.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        tracer: Tracer to use (defaults to global tracer)
        capture_args: Whether to capture function arguments as span attributes
        capture_result: Whether to capture return value as span attribute

    Example:
        >>> @trace_async(capture_args=True)
        ... async def fetch_user_async(user_id: str) -> dict:
        ...     return {"id": user_id, "name": "Alice"}
    """

    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get tracer
            active_tracer = tracer or _default_tracer
            if not active_tracer:
                # No tracer available, just call function
                return await func(*args, **kwargs)

            # Start span
            with active_tracer.start_span(span_name, kind=kind) as span:
                # Capture function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Capture arguments if requested
                if capture_args:
                    # Get argument names
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    for arg_name, arg_value in bound_args.arguments.items():
                        # Only capture simple types
                        if isinstance(arg_value, (str, int, float, bool, type(None))):
                            span.set_attribute(f"function.arg.{arg_name}", arg_value)
                        else:
                            span.set_attribute(f"function.arg.{arg_name}", str(type(arg_value).__name__))

                try:
                    result = await func(*args, **kwargs)

                    # Capture result if requested
                    if capture_result:
                        if isinstance(result, (str, int, float, bool, type(None))):
                            span.set_attribute("function.result", result)
                        else:
                            span.set_attribute("function.result.type", type(result).__name__)

                    return result

                except Exception:
                    # Exception is automatically recorded by span manager
                    raise

        return cast(F, wrapper)

    return decorator


# Convenience aliases
trace = trace_function  # For backward compatibility
