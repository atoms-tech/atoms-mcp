"""
Redis cache implementation.

This module provides a Redis-based cache implementation with
connection pooling and batch operations.
"""

from __future__ import annotations

import pickle
from typing import Any, Optional

try:
    import redis
    from redis import ConnectionPool, Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    Redis = None
    ConnectionPool = None

from atoms_mcp.domain.ports.cache import Cache


class RedisCacheError(Exception):
    """Exception raised for Redis cache errors."""

    pass


class RedisCache(Cache):
    """
    Redis-based cache implementation.

    This cache implementation:
    - Uses Redis for distributed caching
    - Connection pooling for efficiency
    - Automatic serialization with pickle
    - Batch operations support
    - Expiration handling
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10,
        default_ttl: int = 300,
        key_prefix: str = "atoms:",
    ) -> None:
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (overrides other connection params)
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            max_connections: Maximum connections in pool
            default_ttl: Default time-to-live in seconds
            key_prefix: Prefix for all cache keys

        Raises:
            RedisCacheError: If Redis is not available or connection fails
        """
        if not REDIS_AVAILABLE:
            raise RedisCacheError("Redis is not installed. Install with: pip install redis")

        self.default_ttl = default_ttl
        self.key_prefix = key_prefix

        try:
            # Create connection pool
            if redis_url:
                self.pool = ConnectionPool.from_url(
                    redis_url,
                    max_connections=max_connections,
                    decode_responses=False,  # We'll handle encoding
                )
            else:
                self.pool = ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    max_connections=max_connections,
                    decode_responses=False,
                )

            # Create Redis client
            self.client: Redis = Redis(connection_pool=self.pool)

            # Test connection
            self.client.ping()

        except Exception as e:
            raise RedisCacheError(f"Failed to connect to Redis: {e}") from e

    def _make_key(self, key: str) -> str:
        """
        Add prefix to cache key.

        Args:
            key: Original key

        Returns:
            Prefixed key
        """
        return f"{self.key_prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """
        Serialize value for storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes
        """
        return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize value from storage.

        Args:
            data: Serialized bytes

        Returns:
            Deserialized value
        """
        return pickle.loads(data)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists, None otherwise

        Raises:
            RedisCacheError: If Redis operation fails
        """
        try:
            data = self.client.get(self._make_key(key))
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            raise RedisCacheError(f"Failed to get value for key {key}: {e}") from e

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default, 0 = no expiration)

        Returns:
            True if successful

        Raises:
            RedisCacheError: If Redis operation fails
        """
        try:
            data = self._serialize(value)

            if ttl is None:
                ttl = self.default_ttl

            if ttl > 0:
                return bool(self.client.setex(self._make_key(key), ttl, data))
            else:
                return bool(self.client.set(self._make_key(key), data))

        except Exception as e:
            raise RedisCacheError(f"Failed to set value for key {key}: {e}") from e

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted, False otherwise

        Raises:
            RedisCacheError: If Redis operation fails
        """
        try:
            return bool(self.client.delete(self._make_key(key)))
        except Exception as e:
            raise RedisCacheError(f"Failed to delete key {key}: {e}") from e

    def clear(self) -> bool:
        """
        Clear all values with the key prefix from the cache.

        Returns:
            True if successful

        Raises:
            RedisCacheError: If Redis operation fails
        """
        try:
            # Find all keys with prefix
            pattern = f"{self.key_prefix}*"
            keys = list(self.client.scan_iter(match=pattern, count=100))

            if keys:
                self.client.delete(*keys)

            return True
        except Exception as e:
            raise RedisCacheError(f"Failed to clear cache: {e}") from e

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        Raises:
            RedisCacheError: If Redis operation fails
        """
        try:
            return bool(self.client.exists(self._make_key(key)))
        except Exception as e:
            raise RedisCacheError(f"Failed to check existence of key {key}: {e}") from e

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)

        Raises:
            RedisCacheError: If Redis operation fails
        """
        if not keys:
            return {}

        try:
            prefixed_keys = [self._make_key(key) for key in keys]
            values = self.client.mget(prefixed_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)

            return result

        except Exception as e:
            raise RedisCacheError(f"Failed to get multiple values: {e}") from e

    def set_many(self, mapping: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store multiple values in the cache.

        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (None = use default)

        Returns:
            True if all successful

        Raises:
            RedisCacheError: If Redis operation fails
        """
        if not mapping:
            return True

        try:
            # Use pipeline for atomic operations
            pipe = self.client.pipeline()

            if ttl is None:
                ttl = self.default_ttl

            for key, value in mapping.items():
                data = self._serialize(value)
                prefixed_key = self._make_key(key)

                if ttl > 0:
                    pipe.setex(prefixed_key, ttl, data)
                else:
                    pipe.set(prefixed_key, data)

            pipe.execute()
            return True

        except Exception as e:
            raise RedisCacheError(f"Failed to set multiple values: {e}") from e

    def close(self) -> None:
        """Close Redis connection pool."""
        try:
            self.pool.disconnect()
        except Exception:
            pass

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
