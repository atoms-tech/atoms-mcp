"""
Test framework decorators for MCP testing.

This module provides decorators for marking, skipping, and managing test functions
in the MCP test framework.
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any

import pytest

# Test registry for tracking decorated tests
_test_registry: dict[str, dict[str, Any]] = {}


def skip_if(condition: Callable[[], bool], reason: str = "Condition not met"):
    """
    Skip a test if the given condition function returns True.

    Args:
        condition: Function that returns True if test should be skipped
        reason: Reason for skipping the test

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if condition():
                pytest.skip(reason)
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if condition():
                pytest.skip(reason)
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def mcp_test(tool_name: str, category: str = "general", priority: int = 1):
    """
    Mark a test as an MCP test with metadata.

    Args:
        tool_name: Name of the MCP tool being tested
        category: Test category (e.g., 'auth', 'workspace', 'tools')
        priority: Test priority (1=highest, 5=lowest)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func._mcp_test_metadata = {"tool_name": tool_name, "category": category, "priority": priority}

        # Register the test
        _test_registry[func.__name__] = func._mcp_test_metadata

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def require_auth(func: Callable) -> Callable:
    """
    Mark a test as requiring authentication.

    Args:
        func: Test function to decorate

    Returns:
        Decorated function
    """
    func._requires_auth = True

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


def timeout(seconds: int):
    """
    Set a timeout for a test function.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.wait_for(
                asyncio.create_task(func(*args, **kwargs))
                if asyncio.iscoroutinefunction(func)
                else asyncio.create_task(asyncio.to_thread(func, *args, **kwargs)),
                timeout=seconds,
            )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Retry a test function on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return await asyncio.to_thread(func, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
                    else:
                        raise last_exception
            return None

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise last_exception
            return None

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def cache_result(func: Callable) -> Callable:
    """
    Cache the result of a test function.

    Args:
        func: Test function to decorate

    Returns:
        Decorated function with caching
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = str(args) + str(sorted(kwargs.items()))
        if cache_key not in cache:
            cache[cache_key] = func(*args, **kwargs)
        return cache[cache_key]

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        cache_key = str(args) + str(sorted(kwargs.items()))
        if cache_key not in cache:
            cache[cache_key] = await func(*args, **kwargs)
        return cache[cache_key]

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


def get_test_registry() -> dict[str, dict[str, Any]]:
    """
    Get the test registry containing all registered test metadata.

    Returns:
        Dictionary mapping test names to their metadata
    """
    return _test_registry.copy()
