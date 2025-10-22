"""
Production-ready observability decorators.

This module provides decorators for:
- Tool execution observation
- Operation logging
- Performance measurement
- Error tracking
- Metric collection

Author: Atoms MCP Platform
Version: 1.0.0
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

from .logging import PerformanceMetric, get_logger
from .metrics import (
    record_database_query,
    record_error,
    record_tool_execution,
)

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def observe_tool(
    tool_name: str | None = None,
    track_performance: bool = True,
    log_inputs: bool = False,
    log_outputs: bool = False
):
    """
    Decorator for observing tool execution.

    Automatically:
    - Records execution metrics
    - Logs execution details
    - Tracks performance
    - Handles errors

    Args:
        tool_name: Name of the tool (defaults to function name)
        track_performance: Whether to track performance metrics
        log_inputs: Whether to log input arguments
        log_outputs: Whether to log output values

    Example:
        @observe_tool("my_tool", track_performance=True)
        async def my_tool(arg1: str, arg2: int):
            return f"Result: {arg1} {arg2}"
    """

    def decorator(func: F) -> F:
        name = tool_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            perf_metric = PerformanceMetric(f"tool.{name}")

            # Log start
            log_data = {"tool_name": name}
            if log_inputs:
                log_data["inputs"] = {
                    "args": args,
                    "kwargs": kwargs
                }

            logger.info(f"Tool execution started: {name}", extra_fields=log_data)

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Calculate duration
                duration = time.perf_counter() - start_time
                perf_metric.add_metadata("status", "success")
                perf_metric.stop()

                # Record metrics
                if track_performance:
                    record_tool_execution(name, duration, success=True)

                # Log completion
                completion_data = {
                    "tool_name": name,
                    "duration_ms": duration * 1000,
                    "status": "success"
                }
                if log_outputs:
                    completion_data["output"] = result

                logger.info(
                    f"Tool execution completed: {name}",
                    extra_fields=completion_data,
                    performance=perf_metric
                )

                return result

            except Exception as e:
                # Calculate duration
                duration = time.perf_counter() - start_time
                perf_metric.add_metadata("status", "error")
                perf_metric.add_metadata("error_type", type(e).__name__)
                perf_metric.stop()

                # Record error metrics
                if track_performance:
                    record_tool_execution(name, duration, success=False)
                record_error(type(e).__name__, f"tool.{name}")

                # Log error
                logger.error(
                    f"Tool execution failed: {name}",
                    extra_fields={
                        "tool_name": name,
                        "duration_ms": duration * 1000,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    performance=perf_metric,
                    exc_info=True
                )

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            perf_metric = PerformanceMetric(f"tool.{name}")

            # Log start
            log_data = {"tool_name": name}
            if log_inputs:
                log_data["inputs"] = {
                    "args": args,
                    "kwargs": kwargs
                }

            logger.info(f"Tool execution started: {name}", extra_fields=log_data)

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Calculate duration
                duration = time.perf_counter() - start_time
                perf_metric.add_metadata("status", "success")
                perf_metric.stop()

                # Record metrics
                if track_performance:
                    record_tool_execution(name, duration, success=True)

                # Log completion
                completion_data = {
                    "tool_name": name,
                    "duration_ms": duration * 1000,
                    "status": "success"
                }
                if log_outputs:
                    completion_data["output"] = result

                logger.info(
                    f"Tool execution completed: {name}",
                    extra_fields=completion_data,
                    performance=perf_metric
                )

                return result

            except Exception as e:
                # Calculate duration
                duration = time.perf_counter() - start_time
                perf_metric.add_metadata("status", "error")
                perf_metric.add_metadata("error_type", type(e).__name__)
                perf_metric.stop()

                # Record error metrics
                if track_performance:
                    record_tool_execution(name, duration, success=False)
                record_error(type(e).__name__, f"tool.{name}")

                # Log error
                logger.error(
                    f"Tool execution failed: {name}",
                    extra_fields={
                        "tool_name": name,
                        "duration_ms": duration * 1000,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    performance=perf_metric,
                    exc_info=True
                )

                raise

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def log_operation(
    operation_name: str | None = None,
    log_level: str = "INFO",
    log_inputs: bool = False,
    log_outputs: bool = False
):
    """
    Decorator for logging operations.

    Args:
        operation_name: Name of the operation (defaults to function name)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_inputs: Whether to log input arguments
        log_outputs: Whether to log output values

    Example:
        @log_operation("user_authentication", log_level="INFO")
        async def authenticate_user(username: str, password: str):
            return {"user_id": "123"}
    """

    def decorator(func: F) -> F:
        name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Log start
            log_data = {"operation": name}
            if log_inputs:
                log_data["inputs"] = {
                    "args": args,
                    "kwargs": kwargs
                }

            logger.info(f"Operation started: {name}", extra_fields=log_data)

            try:
                result = await func(*args, **kwargs)

                # Log completion
                completion_data = {"operation": name, "status": "success"}
                if log_outputs:
                    completion_data["output"] = result

                logger.info(f"Operation completed: {name}", extra_fields=completion_data)

                return result

            except Exception as e:
                logger.error(
                    f"Operation failed: {name}",
                    extra_fields={
                        "operation": name,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    exc_info=True
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Log start
            log_data = {"operation": name}
            if log_inputs:
                log_data["inputs"] = {
                    "args": args,
                    "kwargs": kwargs
                }

            logger.info(f"Operation started: {name}", extra_fields=log_data)

            try:
                result = func(*args, **kwargs)

                # Log completion
                completion_data = {"operation": name, "status": "success"}
                if log_outputs:
                    completion_data["output"] = result

                logger.info(f"Operation completed: {name}", extra_fields=completion_data)

                return result

            except Exception as e:
                logger.error(
                    f"Operation failed: {name}",
                    extra_fields={
                        "operation": name,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    exc_info=True
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def measure_performance(
    operation_name: str | None = None,
    threshold_warning_ms: float = 1000.0,
    threshold_critical_ms: float = 5000.0
):
    """
    Decorator for measuring operation performance.

    Logs warnings when operations exceed thresholds.

    Args:
        operation_name: Name of the operation (defaults to function name)
        threshold_warning_ms: Warning threshold in milliseconds
        threshold_critical_ms: Critical threshold in milliseconds

    Example:
        @measure_performance("database_query", threshold_warning_ms=500)
        async def query_database(query: str):
            return await db.execute(query)
    """

    def decorator(func: F) -> F:
        name = operation_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            perf_metric = PerformanceMetric(name)

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                perf_metric.stop()

                # Check thresholds
                if duration_ms >= threshold_critical_ms:
                    logger.warning(
                        f"Critical performance threshold exceeded: {name}",
                        extra_fields={
                            "operation": name,
                            "duration_ms": duration_ms,
                            "threshold": "critical"
                        },
                        performance=perf_metric
                    )
                elif duration_ms >= threshold_warning_ms:
                    logger.warning(
                        f"Performance threshold exceeded: {name}",
                        extra_fields={
                            "operation": name,
                            "duration_ms": duration_ms,
                            "threshold": "warning"
                        },
                        performance=perf_metric
                    )

                return result

            except Exception as e:
                perf_metric.add_metadata("error", str(e))
                perf_metric.stop()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            perf_metric = PerformanceMetric(name)

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                perf_metric.stop()

                # Check thresholds
                if duration_ms >= threshold_critical_ms:
                    logger.warning(
                        f"Critical performance threshold exceeded: {name}",
                        extra_fields={
                            "operation": name,
                            "duration_ms": duration_ms,
                            "threshold": "critical"
                        },
                        performance=perf_metric
                    )
                elif duration_ms >= threshold_warning_ms:
                    logger.warning(
                        f"Performance threshold exceeded: {name}",
                        extra_fields={
                            "operation": name,
                            "duration_ms": duration_ms,
                            "threshold": "warning"
                        },
                        performance=perf_metric
                    )

                return result

            except Exception as e:
                perf_metric.add_metadata("error", str(e))
                perf_metric.stop()
                raise

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def track_database_operation(operation_type: str):
    """
    Decorator specifically for tracking database operations.

    Args:
        operation_type: Type of database operation (select, insert, update, delete)

    Example:
        @track_database_operation("select")
        async def get_user(user_id: str):
            return await db.users.get(user_id)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time

                # Record database metrics
                record_database_query(operation_type, duration, success=True)

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                # Record failed query
                record_database_query(operation_type, duration, success=False)

                logger.error(
                    f"Database operation failed: {operation_type}",
                    extra_fields={
                        "operation": operation_type,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    exc_info=True
                )

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time

                # Record database metrics
                record_database_query(operation_type, duration, success=True)

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time

                # Record failed query
                record_database_query(operation_type, duration, success=False)

                logger.error(
                    f"Database operation failed: {operation_type}",
                    extra_fields={
                        "operation": operation_type,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    exc_info=True
                )

                raise

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
