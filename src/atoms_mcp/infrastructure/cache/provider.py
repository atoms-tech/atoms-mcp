"""
Cache provider implementations.

This module provides concrete cache implementations including
in-memory cache (default, no dependencies) and optional Redis cache.
"""

import time
from typing import Any, Optional

from ...domain.ports.cache import Cache
from ..errors.exceptions import CacheException


class InMemoryCacheProvider(Cache):
    """
    In-memory cache implementation using a dictionary.

    This is the default cache provider with no external dependencies.
    Suitable for single-instance deployments and development.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize in-memory cache.

        Args:
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        self._cache: dict[str, tuple[Any, Optional[float]]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        try:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                return None

            return value
        except Exception as e:
            raise CacheException(
                message="Failed to get value from cache",
                operation="get",
                key=key,
                cause=e,
            )

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Enforce max size using LRU-like eviction
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Remove oldest entry (first item in dict)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            # Calculate expiry time
            expiry = None
            if ttl is not None and ttl > 0:
                expiry = time.time() + ttl
            elif ttl is None and self._default_ttl > 0:
                expiry = time.time() + self._default_ttl

            self._cache[key] = (value, expiry)
            return True
        except Exception as e:
            raise CacheException(
                message="Failed to set value in cache",
                operation="set",
                key=key,
                cause=e,
            )

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted, False otherwise
        """
        try:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
        except Exception as e:
            raise CacheException(
                message="Failed to delete value from cache",
                operation="delete",
                key=key,
                cause=e,
            )

    def clear(self) -> bool:
        """
        Clear all values from the cache.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._cache.clear()
            return True
        except Exception as e:
            raise CacheException(
                message="Failed to clear cache",
                operation="clear",
                cause=e,
            )

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired, False otherwise
        """
        value = self.get(key)
        return value is not None

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store multiple values in the cache.

        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            True if all successful, False otherwise
        """
        try:
            for key, value in mapping.items():
                self.set(key, value, ttl)
            return True
        except Exception as e:
            raise CacheException(
                message="Failed to set multiple values in cache",
                operation="set_many",
                cause=e,
            )


class RedisCacheProvider(Cache):
    """
    Redis cache implementation.

    Optional cache provider requiring redis package.
    Suitable for multi-instance deployments and production.
    """

    def __init__(self, redis_url: str, default_ttl: int = 300):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds

        Raises:
            ImportError: If redis package is not installed
            CacheException: If connection fails
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "redis package is required for RedisCacheProvider. "
                "Install with: pip install redis"
            )

        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._default_ttl = default_ttl
            # Test connection
            self._redis.ping()
        except Exception as e:
            raise CacheException(
                message="Failed to connect to Redis",
                operation="connect",
                cause=e,
            )

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        try:
            import json

            value = self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            raise CacheException(
                message="Failed to get value from Redis",
                operation="get",
                key=key,
                cause=e,
            )

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            True if successful, False otherwise
        """
        try:
            import json

            serialized = json.dumps(value)
            ttl_seconds = ttl if ttl is not None else self._default_ttl

            if ttl_seconds > 0:
                self._redis.setex(key, ttl_seconds, serialized)
            else:
                self._redis.set(key, serialized)
            return True
        except Exception as e:
            raise CacheException(
                message="Failed to set value in Redis",
                operation="set",
                key=key,
                cause=e,
            )

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted, False otherwise
        """
        try:
            deleted = self._redis.delete(key)
            return deleted > 0
        except Exception as e:
            raise CacheException(
                message="Failed to delete value from Redis",
                operation="delete",
                key=key,
                cause=e,
            )

    def clear(self) -> bool:
        """
        Clear all values from the cache.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._redis.flushdb()
            return True
        except Exception as e:
            raise CacheException(
                message="Failed to clear Redis cache",
                operation="clear",
                cause=e,
            )

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return self._redis.exists(key) > 0
        except Exception as e:
            raise CacheException(
                message="Failed to check key existence in Redis",
                operation="exists",
                key=key,
                cause=e,
            )

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        try:
            import json

            values = self._redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            raise CacheException(
                message="Failed to get multiple values from Redis",
                operation="get_many",
                cause=e,
            )

    def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store multiple values in the cache.

        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            True if all successful, False otherwise
        """
        try:
            import json

            pipeline = self._redis.pipeline()
            ttl_seconds = ttl if ttl is not None else self._default_ttl

            for key, value in mapping.items():
                serialized = json.dumps(value)
                if ttl_seconds > 0:
                    pipeline.setex(key, ttl_seconds, serialized)
                else:
                    pipeline.set(key, serialized)

            pipeline.execute()
            return True
        except Exception as e:
            raise CacheException(
                message="Failed to set multiple values in Redis",
                operation="set_many",
                cause=e,
            )


def create_cache_provider(
    backend: str = "memory",
    redis_url: Optional[str] = None,
    max_size: int = 1000,
    default_ttl: int = 300,
) -> Cache:
    """
    Factory function to create cache provider based on configuration.

    Args:
        backend: Cache backend type ("memory" or "redis")
        redis_url: Redis connection URL (required if backend="redis")
        max_size: Maximum cache size (for in-memory cache)
        default_ttl: Default time-to-live in seconds

    Returns:
        Cache provider instance

    Raises:
        ValueError: If invalid backend or missing configuration
    """
    if backend == "memory":
        return InMemoryCacheProvider(max_size=max_size, default_ttl=default_ttl)
    elif backend == "redis":
        if not redis_url:
            raise ValueError("redis_url is required for Redis cache backend")
        return RedisCacheProvider(redis_url=redis_url, default_ttl=default_ttl)
    else:
        raise ValueError(f"Unknown cache backend: {backend}")
