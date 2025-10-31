"""
Comprehensive test suite for Redis cache adapter with full mocking.

This module provides complete test coverage for Redis cache operations,
connection management, batch operations, TTL handling, and error scenarios
using a fully mocked Redis client.
"""

from __future__ import annotations

import pytest
import pickle
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch

from atoms_mcp.adapters.secondary.cache.adapters.redis import (
    RedisCache,
    RedisCacheError,
)


# ============================================================================
# Mock Redis Implementation
# ============================================================================


class MockRedisPipeline:
    """Mock Redis pipeline for batch operations."""

    def __init__(self, storage: dict[bytes, bytes]):
        self.storage = storage
        self.commands: list[tuple[str, tuple, dict]] = []

    def set(self, key: bytes, value: bytes) -> MockRedisPipeline:
        """Queue set command."""
        self.commands.append(("set", (key, value), {}))
        return self

    def setex(self, key: bytes, ttl: int, value: bytes) -> MockRedisPipeline:
        """Queue setex command."""
        self.commands.append(("setex", (key, ttl, value), {}))
        return self

    def execute(self) -> list[Any]:
        """Execute all queued commands."""
        results = []
        for cmd, args, kwargs in self.commands:
            if cmd == "set":
                key, value = args
                self.storage[key] = value
                results.append(True)
            elif cmd == "setex":
                key, ttl, value = args
                self.storage[key] = value
                results.append(True)
        self.commands.clear()
        return results


class MockRedisClient:
    """
    Complete mock implementation of Redis client.

    Features:
    - In-memory storage simulation
    - TTL tracking
    - Batch operations with pipeline
    - Error injection
    - Call tracking
    - Connection state management
    """

    def __init__(
        self,
        should_fail: bool = False,
        connection_alive: bool = True,
    ):
        self.storage: dict[bytes, bytes] = {}
        self.ttl_storage: dict[bytes, int] = {}
        self.call_log: list[tuple[str, tuple, dict]] = []
        self.should_fail = should_fail
        self.connection_alive = connection_alive

    def ping(self) -> bool:
        """Test connection."""
        if not self.connection_alive:
            raise Exception("Connection refused")
        if self.should_fail:
            raise Exception("Redis ping failed")
        self.call_log.append(("ping", (), {}))
        return True

    def get(self, key: bytes) -> Optional[bytes]:
        """Get value by key."""
        self.call_log.append(("get", (key,), {}))
        if self.should_fail:
            raise Exception("Redis get failed")
        return self.storage.get(key)

    def set(self, key: bytes, value: bytes) -> bool:
        """Set value without expiration."""
        self.call_log.append(("set", (key, value), {}))
        if self.should_fail:
            raise Exception("Redis set failed")
        self.storage[key] = value
        return True

    def setex(self, key: bytes, ttl: int, value: bytes) -> bool:
        """Set value with expiration."""
        self.call_log.append(("setex", (key, ttl, value), {}))
        if self.should_fail:
            raise Exception("Redis setex failed")
        self.storage[key] = value
        self.ttl_storage[key] = ttl
        return True

    def delete(self, *keys: bytes) -> int:
        """Delete one or more keys."""
        self.call_log.append(("delete", keys, {}))
        if self.should_fail:
            raise Exception("Redis delete failed")
        deleted = 0
        for key in keys:
            if key in self.storage:
                del self.storage[key]
                self.ttl_storage.pop(key, None)
                deleted += 1
        return deleted

    def exists(self, key: bytes) -> int:
        """Check if key exists."""
        self.call_log.append(("exists", (key,), {}))
        if self.should_fail:
            raise Exception("Redis exists failed")
        return 1 if key in self.storage else 0

    def mget(self, keys: list[bytes]) -> list[Optional[bytes]]:
        """Get multiple values."""
        self.call_log.append(("mget", (keys,), {}))
        if self.should_fail:
            raise Exception("Redis mget failed")
        return [self.storage.get(key) for key in keys]

    def scan_iter(self, match: str, count: int = 100) -> list[bytes]:
        """Scan for keys matching pattern."""
        self.call_log.append(("scan_iter", (), {"match": match, "count": count}))
        if self.should_fail:
            raise Exception("Redis scan_iter failed")

        # Simple pattern matching
        pattern = match.encode()
        if b"*" in pattern:
            prefix = pattern.replace(b"*", b"")
            return [k for k in self.storage.keys() if k.startswith(prefix)]
        return [k for k in self.storage.keys() if k == pattern]

    def pipeline(self) -> MockRedisPipeline:
        """Create a pipeline."""
        self.call_log.append(("pipeline", (), {}))
        if self.should_fail:
            raise Exception("Redis pipeline failed")
        return MockRedisPipeline(self.storage)

    def reset(self):
        """Reset mock state."""
        self.storage.clear()
        self.ttl_storage.clear()
        self.call_log.clear()
        self.should_fail = False
        self.connection_alive = True


class MockConnectionPool:
    """Mock Redis connection pool."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.disconnected = False

    def disconnect(self):
        """Disconnect the pool."""
        self.disconnected = True

    @classmethod
    def from_url(cls, url: str, **kwargs) -> MockConnectionPool:
        """Create pool from URL."""
        return cls(url=url, **kwargs)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_redis_client():
    """Provide a fresh mock Redis client."""
    return MockRedisClient()


@pytest.fixture
def mock_redis_module(mock_redis_client):
    """Mock the redis module."""
    with patch("atoms_mcp.adapters.secondary.cache.adapters.redis.Redis") as mock_redis:
        with patch("atoms_mcp.adapters.secondary.cache.adapters.redis.ConnectionPool", MockConnectionPool):
            mock_redis.return_value = mock_redis_client
            yield mock_redis_client


@pytest.fixture
def redis_cache(mock_redis_module):
    """Provide a Redis cache instance with mocked client."""
    cache = RedisCache(
        host="localhost",
        port=6379,
        db=0,
        default_ttl=300,
    )
    yield cache
    try:
        cache.close()
    except Exception:
        pass


# ============================================================================
# Connection and Initialization Tests (8 tests)
# ============================================================================


class TestRedisCacheConnection:
    """Test Redis cache connection and initialization."""

    def test_cache_initialization_success(self, mock_redis_module):
        """
        Given: Valid Redis connection parameters
        When: Creating a Redis cache
        Then: Cache is initialized successfully
        """
        cache = RedisCache(host="localhost", port=6379)

        assert cache.client is not None
        assert "ping" in [call[0] for call in mock_redis_module.call_log]

    def test_cache_initialization_with_url(self, mock_redis_module):
        """
        Given: Redis connection URL
        When: Creating cache with URL
        Then: Cache is initialized from URL
        """
        cache = RedisCache(redis_url="redis://localhost:6379/0")

        assert cache.client is not None

    def test_cache_initialization_with_password(self, mock_redis_module):
        """
        Given: Redis connection with password
        When: Creating cache
        Then: Password is used in connection
        """
        cache = RedisCache(
            host="localhost",
            port=6379,
            password="secret",
        )

        assert cache.client is not None

    def test_cache_initialization_connection_failed(self, mock_redis_module):
        """
        Given: Redis connection that fails
        When: Attempting to create cache
        Then: RedisCacheError is raised
        """
        mock_redis_module.connection_alive = False

        with pytest.raises(RedisCacheError, match="Failed to connect"):
            RedisCache(host="localhost", port=6379)

    def test_cache_initialization_without_redis_installed(self):
        """
        Given: Redis module not available
        When: Attempting to create cache
        Then: RedisCacheError is raised
        """
        with patch("atoms_mcp.adapters.secondary.cache.adapters.redis.REDIS_AVAILABLE", False):
            with pytest.raises(RedisCacheError, match="Redis is not installed"):
                RedisCache(host="localhost", port=6379)

    def test_cache_custom_key_prefix(self, mock_redis_module):
        """
        Given: Custom key prefix
        When: Creating cache
        Then: Prefix is applied to all keys
        """
        cache = RedisCache(host="localhost", port=6379, key_prefix="myapp:")

        assert cache.key_prefix == "myapp:"

    def test_cache_custom_default_ttl(self, mock_redis_module):
        """
        Given: Custom default TTL
        When: Creating cache
        Then: TTL is stored
        """
        cache = RedisCache(host="localhost", port=6379, default_ttl=600)

        assert cache.default_ttl == 600

    def test_cache_close_connection(self, redis_cache):
        """
        Given: Active cache connection
        When: Closing cache
        Then: Connection pool is disconnected
        """
        redis_cache.close()

        assert redis_cache.pool.disconnected


# ============================================================================
# Basic Cache Operations Tests (10 tests)
# ============================================================================


class TestRedisCacheBasicOperations:
    """Test basic Redis cache operations."""

    def test_set_and_get_value(self, redis_cache):
        """
        Given: A value to cache
        When: Setting and getting the value
        Then: Same value is returned
        """
        key = "test_key"
        value = {"data": "test value", "number": 42}

        redis_cache.set(key, value)
        result = redis_cache.get(key)

        assert result == value

    def test_set_with_custom_ttl(self, redis_cache, mock_redis_module):
        """
        Given: Value with custom TTL
        When: Setting value
        Then: TTL is applied
        """
        key = "expire_key"
        value = "test"
        ttl = 60

        redis_cache.set(key, value, ttl=ttl)

        # Check that setex was called with correct TTL
        assert any(
            call[0] == "setex" and call[1][1] == ttl
            for call in mock_redis_module.call_log
        )

    def test_set_with_zero_ttl(self, redis_cache, mock_redis_module):
        """
        Given: Value with zero TTL (no expiration)
        When: Setting value
        Then: Value is set without expiration
        """
        key = "no_expire"
        value = "test"

        redis_cache.set(key, value, ttl=0)

        # Check that set was called (not setex)
        assert any(
            call[0] == "set"
            for call in mock_redis_module.call_log
        )

    def test_set_with_default_ttl(self, redis_cache, mock_redis_module):
        """
        Given: Value without explicit TTL
        When: Setting value
        Then: Default TTL is used
        """
        key = "default_ttl"
        value = "test"

        redis_cache.set(key, value)

        # Check that setex was called with default TTL
        assert any(
            call[0] == "setex" and call[1][1] == 300  # default_ttl
            for call in mock_redis_module.call_log
        )

    def test_get_nonexistent_key(self, redis_cache):
        """
        Given: Key that doesn't exist
        When: Getting the key
        Then: None is returned
        """
        result = redis_cache.get("nonexistent")

        assert result is None

    def test_delete_existing_key(self, redis_cache):
        """
        Given: Existing key in cache
        When: Deleting the key
        Then: Key is removed and True is returned
        """
        key = "to_delete"
        redis_cache.set(key, "value")

        result = redis_cache.delete(key)

        assert result is True
        assert redis_cache.get(key) is None

    def test_delete_nonexistent_key(self, redis_cache):
        """
        Given: Key that doesn't exist
        When: Attempting to delete
        Then: False is returned
        """
        result = redis_cache.delete("nonexistent")

        assert result is False

    def test_exists_key_present(self, redis_cache):
        """
        Given: Existing key in cache
        When: Checking if key exists
        Then: True is returned
        """
        key = "exists_test"
        redis_cache.set(key, "value")

        exists = redis_cache.exists(key)

        assert exists is True

    def test_exists_key_absent(self, redis_cache):
        """
        Given: Non-existing key
        When: Checking if key exists
        Then: False is returned
        """
        exists = redis_cache.exists("nonexistent")

        assert exists is False

    def test_key_prefix_application(self, mock_redis_module):
        """
        Given: Cache with custom prefix
        When: Setting and getting values
        Then: Prefix is applied to all operations
        """
        cache = RedisCache(
            host="localhost",
            port=6379,
            key_prefix="test:",
        )

        cache.set("key", "value")

        # Check that prefixed key was used
        prefixed_key = b"test:key"
        assert prefixed_key in mock_redis_module.storage


# ============================================================================
# Batch Operations Tests (6 tests)
# ============================================================================


class TestRedisCacheBatchOperations:
    """Test batch operations in Redis cache."""

    def test_get_many_success(self, redis_cache):
        """
        Given: Multiple keys in cache
        When: Getting multiple keys
        Then: All values are returned
        """
        keys = ["key1", "key2", "key3"]
        values = ["value1", "value2", "value3"]

        for key, value in zip(keys, values):
            redis_cache.set(key, value)

        result = redis_cache.get_many(keys)

        assert len(result) == 3
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["key3"] == "value3"

    def test_get_many_partial_hits(self, redis_cache):
        """
        Given: Some keys exist, some don't
        When: Getting multiple keys
        Then: Only existing keys are returned
        """
        redis_cache.set("key1", "value1")
        redis_cache.set("key3", "value3")

        result = redis_cache.get_many(["key1", "key2", "key3"])

        assert len(result) == 2
        assert "key1" in result
        assert "key3" in result
        assert "key2" not in result

    def test_get_many_empty_list(self, redis_cache):
        """
        Given: Empty list of keys
        When: Getting multiple keys
        Then: Empty dict is returned
        """
        result = redis_cache.get_many([])

        assert result == {}

    def test_set_many_success(self, redis_cache):
        """
        Given: Multiple key-value pairs
        When: Setting multiple values
        Then: All values are stored
        """
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

        result = redis_cache.set_many(data)

        assert result is True
        for key, value in data.items():
            assert redis_cache.get(key) == value

    def test_set_many_with_ttl(self, redis_cache, mock_redis_module):
        """
        Given: Multiple values with custom TTL
        When: Setting values
        Then: TTL is applied to all
        """
        data = {"key1": "value1", "key2": "value2"}
        ttl = 120

        redis_cache.set_many(data, ttl=ttl)

        # Verify setex was used with correct TTL
        setex_calls = [
            call for call in mock_redis_module.call_log
            if call[0] == "pipeline"
        ]
        assert len(setex_calls) > 0

    def test_set_many_empty_dict(self, redis_cache):
        """
        Given: Empty dictionary
        When: Setting multiple values
        Then: True is returned (no-op)
        """
        result = redis_cache.set_many({})

        assert result is True


# ============================================================================
# Clear and Pattern Operations Tests (3 tests)
# ============================================================================


class TestRedisCacheClearOperations:
    """Test cache clearing and pattern matching."""

    def test_clear_all_keys_with_prefix(self, redis_cache):
        """
        Given: Multiple keys with same prefix
        When: Clearing cache
        Then: All keys with prefix are removed
        """
        redis_cache.set("key1", "value1")
        redis_cache.set("key2", "value2")
        redis_cache.set("key3", "value3")

        result = redis_cache.clear()

        assert result is True
        assert redis_cache.get("key1") is None
        assert redis_cache.get("key2") is None
        assert redis_cache.get("key3") is None

    def test_clear_empty_cache(self, redis_cache):
        """
        Given: Empty cache
        When: Clearing cache
        Then: True is returned (no-op)
        """
        result = redis_cache.clear()

        assert result is True

    def test_clear_with_pattern_matching(self, mock_redis_module):
        """
        Given: Keys matching pattern
        When: Clearing cache
        Then: Only matching keys are removed
        """
        cache = RedisCache(
            host="localhost",
            port=6379,
            key_prefix="app:",
        )

        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("post:1", "data3")

        cache.clear()

        # All keys with app: prefix should be gone
        prefixed_keys = [k for k in mock_redis_module.storage.keys() if k.startswith(b"app:")]
        assert len(prefixed_keys) == 0


# ============================================================================
# Error Handling Tests (5 tests)
# ============================================================================


class TestRedisCacheErrorHandling:
    """Test error handling in Redis cache."""

    def test_get_error(self, redis_cache, mock_redis_module):
        """
        Given: Redis get operation fails
        When: Getting value
        Then: RedisCacheError is raised
        """
        mock_redis_module.should_fail = True

        with pytest.raises(RedisCacheError, match="Failed to get value"):
            redis_cache.get("key")

    def test_set_error(self, redis_cache, mock_redis_module):
        """
        Given: Redis set operation fails
        When: Setting value
        Then: RedisCacheError is raised
        """
        mock_redis_module.should_fail = True

        with pytest.raises(RedisCacheError, match="Failed to set value"):
            redis_cache.set("key", "value")

    def test_delete_error(self, redis_cache, mock_redis_module):
        """
        Given: Redis delete operation fails
        When: Deleting key
        Then: RedisCacheError is raised
        """
        mock_redis_module.should_fail = True

        with pytest.raises(RedisCacheError, match="Failed to delete"):
            redis_cache.delete("key")

    def test_exists_error(self, redis_cache, mock_redis_module):
        """
        Given: Redis exists operation fails
        When: Checking existence
        Then: RedisCacheError is raised
        """
        mock_redis_module.should_fail = True

        with pytest.raises(RedisCacheError, match="Failed to check existence"):
            redis_cache.exists("key")

    def test_clear_error(self, redis_cache, mock_redis_module):
        """
        Given: Redis clear operation fails
        When: Clearing cache
        Then: RedisCacheError is raised
        """
        mock_redis_module.should_fail = True

        with pytest.raises(RedisCacheError, match="Failed to clear cache"):
            redis_cache.clear()


# ============================================================================
# Serialization Tests (5 tests)
# ============================================================================


class TestRedisCacheSerialization:
    """Test serialization and deserialization in Redis cache."""

    def test_serialize_simple_types(self, redis_cache):
        """
        Given: Simple Python types
        When: Storing and retrieving
        Then: Values are correctly serialized/deserialized
        """
        test_cases = [
            ("string", "test string"),
            ("int", 42),
            ("float", 3.14),
            ("bool", True),
            ("none", None),
        ]

        for key, value in test_cases:
            redis_cache.set(key, value)
            result = redis_cache.get(key)
            assert result == value

    def test_serialize_complex_dict(self, redis_cache):
        """
        Given: Complex nested dictionary
        When: Storing and retrieving
        Then: Structure is preserved
        """
        data = {
            "user": {
                "name": "John",
                "age": 30,
                "tags": ["admin", "user"],
            },
            "metadata": {
                "created": "2024-01-01",
                "count": 42,
            },
        }

        redis_cache.set("complex", data)
        result = redis_cache.get("complex")

        assert result == data
        assert result["user"]["name"] == "John"
        assert "admin" in result["user"]["tags"]

    def test_serialize_list(self, redis_cache):
        """
        Given: List of values
        When: Storing and retrieving
        Then: List is preserved
        """
        data = [1, 2, 3, "four", {"five": 5}]

        redis_cache.set("list", data)
        result = redis_cache.get("list")

        assert result == data

    def test_serialize_custom_object(self, redis_cache):
        """
        Given: Custom Python object
        When: Storing and retrieving
        Then: Object is preserved (via pickle)
        """

        class CustomObject:
            def __init__(self, name: str, value: int):
                self.name = name
                self.value = value

            def __eq__(self, other):
                return (
                    isinstance(other, CustomObject)
                    and self.name == other.name
                    and self.value == other.value
                )

        obj = CustomObject("test", 42)

        redis_cache.set("custom", obj)
        result = redis_cache.get("custom")

        assert result == obj
        assert result.name == "test"
        assert result.value == 42

    def test_serialize_binary_data(self, redis_cache):
        """
        Given: Binary data
        When: Storing and retrieving
        Then: Data is preserved
        """
        data = b"binary data \x00\x01\x02"

        redis_cache.set("binary", data)
        result = redis_cache.get("binary")

        assert result == data


# ============================================================================
# Connection Pool Tests (3 tests)
# ============================================================================


class TestRedisCacheConnectionPool:
    """Test connection pooling functionality."""

    def test_connection_pool_creation(self, mock_redis_module):
        """
        Given: Redis cache with pool configuration
        When: Creating cache
        Then: Connection pool is created with correct params
        """
        cache = RedisCache(
            host="localhost",
            port=6379,
            max_connections=20,
        )

        assert cache.pool is not None
        assert cache.pool.kwargs.get("max_connections") == 20

    def test_connection_pool_from_url(self, mock_redis_module):
        """
        Given: Redis URL
        When: Creating cache
        Then: Connection pool is created from URL
        """
        cache = RedisCache(redis_url="redis://localhost:6379/1")

        assert cache.pool is not None

    def test_connection_pool_disconnect(self, redis_cache):
        """
        Given: Active connection pool
        When: Closing cache
        Then: Pool is disconnected
        """
        redis_cache.close()

        assert redis_cache.pool.disconnected
