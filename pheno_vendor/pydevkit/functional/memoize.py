"""Memoization utilities."""

from functools import lru_cache as _lru_cache
from functools import wraps
from typing import Any, Callable, Dict, Tuple


def memoize(func: Callable) -> Callable:
    """
    Simple memoization decorator.

    Example:
        @memoize
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    cache: Dict[Tuple, Any] = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key
        key = (args, tuple(sorted(kwargs.items())))

        if key not in cache:
            cache[key] = func(*args, **kwargs)

        return cache[key]

    # Add cache inspection methods
    wrapper.cache = cache
    wrapper.cache_clear = lambda: cache.clear()
    wrapper.cache_info = lambda: {
        'hits': 0,
        'misses': 0,
        'size': len(cache),
    }

    return wrapper


def lru_memoize(maxsize: int = 128) -> Callable:
    """
    LRU cache memoization.

    Example:
        @lru_memoize(maxsize=100)
        def expensive_function(x):
            return x ** 2
    """
    return _lru_cache(maxsize=maxsize)
