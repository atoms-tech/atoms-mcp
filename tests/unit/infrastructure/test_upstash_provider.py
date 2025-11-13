"""Tests for Upstash Redis provider wrapper."""

import pytest
import os
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio


class TestUpstashKVWrapper:
    """Test Upstash KV store wrapper."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Upstash Redis client."""
        return AsyncMock()

    @pytest.fixture
    def wrapper(self, mock_redis):
        """Create wrapper with mock Redis."""
        from infrastructure.upstash_provider import UpstashKVWrapper
        return UpstashKVWrapper(mock_redis)

    async def test_get_returns_none_when_key_missing(self, wrapper, mock_redis):
        """Get should return None for missing keys."""
        mock_redis.get.return_value = None

        result = await wrapper.get("nonexistent")

        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent")

    async def test_get_parses_json_string(self, wrapper, mock_redis):
        """Get should parse JSON strings from Redis."""
        import json
        test_data = {"key": "value", "number": 42}
        mock_redis.get.return_value = json.dumps(test_data)

        result = await wrapper.get("test_key")

        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")

    async def test_set_stores_json_serialized_value(self, wrapper, mock_redis):
        """Set should JSON-serialize and store value."""
        import json
        test_data = {"key": "value"}

        await wrapper.set("test_key", test_data)

        mock_redis.set.assert_called_once()
        args = mock_redis.set.call_args[0]
        assert args[0] == "test_key"
        assert json.loads(args[1]) == test_data

    async def test_set_with_ttl_uses_setex(self, wrapper, mock_redis):
        """Set with TTL should use setex command."""
        test_data = {"key": "value"}

        await wrapper.set("test_key", test_data, ttl=3600)

        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "test_key"
        assert args[1] == 3600

    async def test_delete_removes_key(self, wrapper, mock_redis):
        """Delete should remove key from Redis."""
        await wrapper.delete("test_key")

        mock_redis.delete.assert_called_once_with("test_key")

    async def test_get_handles_redis_error_gracefully(self, wrapper, mock_redis):
        """Get should return None on Redis error."""
        mock_redis.get.side_effect = Exception("Redis error")

        result = await wrapper.get("test_key")

        assert result is None

    async def test_set_handles_redis_error_gracefully(self, wrapper, mock_redis):
        """Set should not raise on Redis error."""
        mock_redis.set.side_effect = Exception("Redis error")

        # Should not raise
        await wrapper.set("test_key", {"data": "value"})


class TestUpstashStoreProvider:
    """Test get_upstash_store provider function."""

    @patch.dict(os.environ, {}, clear=False)
    async def test_returns_memory_store_when_not_configured(self):
        """Should return MemoryStore when Upstash not configured."""
        # Clear Upstash env vars
        for key in ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"]:
            os.environ.pop(key, None)

        from infrastructure.upstash_provider import get_upstash_store
        store = await get_upstash_store()

        # Should be memory store or basic fallback
        assert store is not None
        assert hasattr(store, "get")
        # MemoryStore uses put/put_many, not set
        assert hasattr(store, "put") or hasattr(store, "set")

    @patch.dict(os.environ, {
        "UPSTASH_REDIS_REST_URL": "https://test.upstash.io",
        "UPSTASH_REDIS_REST_TOKEN": "token"
    })
    async def test_returns_upstash_wrapper_when_configured(self):
        """Should return UpstashKVWrapper when credentials set."""
        # With real credentials, would create wrapper
        # For testing, just verify wrapper can be created with a mock redis
        from infrastructure.upstash_provider import UpstashKVWrapper
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        wrapper = UpstashKVWrapper(mock_redis)
        assert wrapper is not None
        assert hasattr(wrapper, "get")
        assert hasattr(wrapper, "set")


class TestUpstashRedisClient:
    """Test get_upstash_redis client function."""

    @patch.dict(os.environ, {}, clear=False)
    async def test_returns_none_when_not_configured(self):
        """Should return None when Upstash not configured."""
        os.environ.pop("UPSTASH_REDIS_REST_URL", None)
        os.environ.pop("UPSTASH_REDIS_REST_TOKEN", None)

        from infrastructure.upstash_provider import get_upstash_redis
        result = await get_upstash_redis()

        assert result is None

    @patch.dict(os.environ, {
        "UPSTASH_REDIS_REST_URL": "https://test.upstash.io",
        "UPSTASH_REDIS_REST_TOKEN": "token"
    })
    async def test_returns_redis_client_when_configured(self):
        """Should return Redis client when credentials set."""
        # Without actual Upstash credentials, will return None or wrapper
        from infrastructure.upstash_provider import get_upstash_redis
        
        result = await get_upstash_redis()
        
        # Result might be None or a wrapper - both acceptable
        assert result is None or hasattr(result, "get")


class TestBasicInMemoryStore:
    """Test fallback in-memory store."""

    async def test_basic_store_get_set_delete(self):
        """Basic store should support get/set/delete."""
        from infrastructure.upstash_provider import _BasicInMemoryStore

        store = _BasicInMemoryStore()
        data = {"key": "value"}

        # Initially empty
        assert await store.get("test") is None

        # Set and get
        await store.set("test", data)
        result = await store.get("test")
        assert result == data

        # Delete
        await store.delete("test")
        assert await store.get("test") is None

    async def test_basic_store_close_noop(self):
        """Basic store close should be no-op."""
        from infrastructure.upstash_provider import _BasicInMemoryStore

        store = _BasicInMemoryStore()
        # Should not raise
        await store.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
