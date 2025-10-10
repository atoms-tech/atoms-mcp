"""Function decorators for automatic logging with timing.

Provides decorators for both synchronous and asynchronous functions with
automatic performance tracking and error logging.
"""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar, cast

from observability.logging.structured import StructuredLogger

# Type variables for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


def log_function_call(
    logger: Optional[StructuredLogger] = None,
    *,
    log_args: bool = False,
    log_result: bool = False,
    log_errors: bool = True,
    level: str = "DEBUG",
) -> Callable[[F], F]:
    """Decorator to log synchronous function calls with timing.

    Args:
        logger: StructuredLogger instance (creates default if not provided)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_errors: Whether to log errors
        level: Log level for entry/exit logs (default: DEBUG)

    Returns:
        Decorated function

    Example:
        >>> from observability.logging import StructuredLogger
        >>> from observability.logging.decorators import log_function_call
        >>>
        >>> logger = StructuredLogger("my-service")
        >>>
        >>> @log_function_call(logger, log_args=True, log_result=True)
        ... def calculate(x: int, y: int) -> int:
        ...     return x + y
        >>>
        >>> result = calculate(5, 3)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get or create logger
            func_logger = logger
            if func_logger is None:
                func_logger = StructuredLogger(func.__module__)

            start_time = time.perf_counter()

            # Prepare log data
            log_data = {
                "function": func.__name__,
                "module": func.__module__,
                "qualname": func.__qualname__,
            }

            if log_args:
                log_data["args"] = str(args) if args else None
                log_data["kwargs"] = {k: str(v) for k, v in kwargs.items()} if kwargs else None

            # Log function entry
            getattr(func_logger, level.lower())(
                f"Function called: {func.__qualname__}",
                **log_data,
            )

            try:
                result = func(*args, **kwargs)

                # Calculate duration
                duration = time.perf_counter() - start_time

                # Log successful completion
                func_logger.performance(
                    func.__qualname__,
                    duration,
                    success=True,
                    **log_data,
                )

                if log_result:
                    result_str = str(result)
                    # Limit result size to prevent log bloat
                    if len(result_str) > 1000:
                        result_str = result_str[:1000] + "... (truncated)"

                    getattr(func_logger, level.lower())(
                        f"Function completed: {func.__qualname__}",
                        result=result_str,
                        duration=duration,
                        **log_data,
                    )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                if log_errors:
                    func_logger.error(
                        f"Function failed: {func.__qualname__}",
                        exc_info=e,
                        error=str(e),
                        error_type=type(e).__name__,
                        duration=duration,
                        **log_data,
                    )

                raise

        return cast(F, wrapper)

    return decorator


def log_async_function_call(
    logger: Optional[StructuredLogger] = None,
    *,
    log_args: bool = False,
    log_result: bool = False,
    log_errors: bool = True,
    level: str = "DEBUG",
) -> Callable[[F], F]:
    """Decorator to log asynchronous function calls with timing.

    Args:
        logger: StructuredLogger instance (creates default if not provided)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_errors: Whether to log errors
        level: Log level for entry/exit logs (default: DEBUG)

    Returns:
        Decorated async function

    Example:
        >>> from observability.logging import StructuredLogger
        >>> from observability.logging.decorators import log_async_function_call
        >>>
        >>> logger = StructuredLogger("my-service")
        >>>
        >>> @log_async_function_call(logger, log_args=True)
        ... async def fetch_data(user_id: str) -> dict:
        ...     # async operation
        ...     return {"user_id": user_id, "name": "Alice"}
        >>>
        >>> result = await fetch_data("123")
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get or create logger
            func_logger = logger
            if func_logger is None:
                func_logger = StructuredLogger(func.__module__)

            start_time = time.perf_counter()

            # Prepare log data
            log_data = {
                "function": func.__name__,
                "module": func.__module__,
                "qualname": func.__qualname__,
                "async": True,
            }

            if log_args:
                log_data["args"] = str(args) if args else None
                log_data["kwargs"] = {k: str(v) for k, v in kwargs.items()} if kwargs else None

            # Log function entry
            getattr(func_logger, level.lower())(
                f"Async function called: {func.__qualname__}",
                **log_data,
            )

            try:
                result = await func(*args, **kwargs)

                # Calculate duration
                duration = time.perf_counter() - start_time

                # Log successful completion
                func_logger.performance(
                    func.__qualname__,
                    duration,
                    success=True,
                    async_operation=True,
                    **log_data,
                )

                if log_result:
                    result_str = str(result)
                    # Limit result size to prevent log bloat
                    if len(result_str) > 1000:
                        result_str = result_str[:1000] + "... (truncated)"

                    getattr(func_logger, level.lower())(
                        f"Async function completed: {func.__qualname__}",
                        result=result_str,
                        duration=duration,
                        **log_data,
                    )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                if log_errors:
                    func_logger.error(
                        f"Async function failed: {func.__qualname__}",
                        exc_info=e,
                        error=str(e),
                        error_type=type(e).__name__,
                        duration=duration,
                        async_operation=True,
                        **log_data,
                    )

                raise

        return cast(F, wrapper)

    return decorator


def log_call(
    logger: Optional[StructuredLogger] = None,
    *,
    log_args: bool = False,
    log_result: bool = False,
    log_errors: bool = True,
    level: str = "DEBUG",
) -> Callable[[F], F]:
    """Universal decorator that works for both sync and async functions.

    This decorator automatically detects if the function is async or sync
    and applies the appropriate logging decorator.

    Args:
        logger: StructuredLogger instance (creates default if not provided)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_errors: Whether to log errors
        level: Log level for entry/exit logs (default: DEBUG)

    Returns:
        Decorated function (preserves sync/async nature)

    Example:
        >>> @log_call(log_args=True)
        ... def sync_func(x: int) -> int:
        ...     return x * 2
        >>>
        >>> @log_call(log_args=True)
        ... async def async_func(x: int) -> int:
        ...     return x * 2
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            return log_async_function_call(
                logger,
                log_args=log_args,
                log_result=log_result,
                log_errors=log_errors,
                level=level,
            )(func)
        else:
            return log_function_call(
                logger,
                log_args=log_args,
                log_result=log_result,
                log_errors=log_errors,
                level=level,
            )(func)

    return decorator


def trace_method(
    logger: Optional[StructuredLogger] = None,
    *,
    include_class: bool = True,
) -> Callable[[F], F]:
    """Decorator specifically for class methods with automatic class name logging.

    Args:
        logger: StructuredLogger instance (creates default if not provided)
        include_class: Whether to include class name in logs

    Returns:
        Decorated method

    Example:
        >>> class UserService:
        ...     @trace_method()
        ...     def get_user(self, user_id: str) -> dict:
        ...         return {"id": user_id, "name": "Alice"}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            # Get or create logger
            func_logger = logger
            if func_logger is None:
                func_logger = StructuredLogger(func.__module__)

            start_time = time.perf_counter()

            # Prepare log data
            log_data = {
                "method": func.__name__,
                "module": func.__module__,
            }

            if include_class:
                log_data["class"] = self.__class__.__name__
                method_name = f"{self.__class__.__name__}.{func.__name__}"
            else:
                method_name = func.__name__

            # Log method entry
            func_logger.debug(f"Method called: {method_name}", **log_data)

            try:
                result = func(self, *args, **kwargs)
                duration = time.perf_counter() - start_time

                func_logger.performance(method_name, duration, **log_data)

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                func_logger.error(
                    f"Method failed: {method_name}",
                    exc_info=e,
                    error=str(e),
                    error_type=type(e).__name__,
                    duration=duration,
                    **log_data,
                )

                raise

        return cast(F, wrapper)

    return decorator


__all__ = [
    "log_function_call",
    "log_async_function_call",
    "log_call",
    "trace_method",
]
