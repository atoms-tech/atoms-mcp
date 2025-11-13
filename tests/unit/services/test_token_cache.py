"""Tests for token cache service.

Tests token caching, invalidation, and statistics tracking.
"""

import pytest
import json
import hashlib
from unittest.mock import AsyncMock, MagicMock
from services.auth.token_cache import TokenCache, get_token_cache, reset_token_cache


pytestmark = [pytest.mark.unit]


class TestTokenCacheBasic:
    """Basic token caching operations."""

    def test_token_cache_initialization_no_redis(self):
        """Test token cache initializes with in-memory store when no Redis."""
        cache = TokenCache(redis_client=None)
        
        assert cache.redis is None
        assert cache._memory_store == {}
        assert cache.CACHE_PREFIX == "auth:token"

    def test_token_cache_initialization_with_redis(self):
        """Test token cache initializes with Redis client."""
        mock_redis = MagicMock()
        cache = TokenCache(redis_client=mock_redis)
        
        assert cache.redis is mock_redis
        assert cache._memory_store == {}

    def test_make_key_hashes_token(self):
        """Test that _make_key creates hash-based keys."""
        cache = TokenCache(redis_client=None)
        token = "test-token-123"
        
        key = cache._make_key(token)
        expected_hash = hashlib.sha256(token.encode()).hexdigest()
        expected_key = f"auth:token:{expected_hash}"
        
        assert key == expected_key
        assert "test-token" not in key  # Token not exposed in key

    def test_make_key_same_for_same_token(self):
        """Test that same token always produces same key."""
        cache = TokenCache(redis_client=None)
        token = "test-token"
        
        key1 = cache._make_key(token)
        key2 = cache._make_key(token)
        
        assert key1 == key2

    def test_make_key_different_for_different_tokens(self):
        """Test that different tokens produce different keys."""
        cache = TokenCache(redis_client=None)
        
        key1 = cache._make_key("token-1")
        key2 = cache._make_key("token-2")
        
        assert key1 != key2


class TestTokenCacheMemoryStore:
    """Token cache in-memory operations (no Redis)."""

    async def test_get_empty_cache_returns_none(self):
        """Test getting from empty cache returns None."""
        cache = TokenCache(redis_client=None)
        
        result = await cache.get("nonexistent-token")
        
        assert result is None

    async def test_set_and_get_in_memory(self):
        """Test setting and retrieving token claims in memory."""
        cache = TokenCache(redis_client=None)
        token = "test-token"
        claims = {"user_id": "user-123", "email": "test@example.com"}
        
        # Set token
        success = await cache.set(token, claims)
        assert success is True
        
        # Get token
        result = await cache.get(token)
        assert result == claims
        assert result["user_id"] == "user-123"

    async def test_set_returns_false_for_invalid_inputs(self):
        """Test set returns False for empty token or claims."""
        cache = TokenCache(redis_client=None)
        
        # Empty token
        result = await cache.set("", {"user_id": "123"})
        assert result is False
        
        # Empty claims
        result = await cache.set("token", {})
        assert result is False
        
        # None token
        result = await cache.set(None, {"user_id": "123"})
        assert result is False

    async def test_invalidate_removes_token(self):
        """Test invalidating token removes it from cache."""
        cache = TokenCache(redis_client=None)
        token = "test-token"
        claims = {"user_id": "user-123"}
        
        # Add token
        await cache.set(token, claims)
        assert await cache.get(token) == claims
        
        # Invalidate
        await cache.invalidate(token)
        
        # Should be gone
        result = await cache.get(token)
        assert result is None

    async def test_invalidate_empty_token_safe(self):
        """Test invalidating empty token doesn't error."""
        cache = TokenCache(redis_client=None)
        
        # Should not raise
        await cache.invalidate("")
        await cache.invalidate(None)

    async def test_get_returns_none_for_empty_token(self):
        """Test get returns None for empty token."""
        cache = TokenCache(redis_client=None)
        
        result = await cache.get("")
        assert result is None
        
        result = await cache.get(None)
        assert result is None


class TestTokenCacheRedis:
    """Token cache with Redis operations."""

    async def test_set_with_redis(self):
        """Test setting token claims to Redis."""
        mock_redis = AsyncMock()
        cache = TokenCache(redis_client=mock_redis)
        
        token = "test-token"
        claims = {"user_id": "user-123"}
        
        success = await cache.set(token, claims, ttl=3600)
        
        assert success is True
        mock_redis.setex.assert_called_once()
        
        # Check call args
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith("auth:token:")  # Key
        assert call_args[0][1] == 3600  # TTL
        assert "user_id" in json.loads(call_args[0][2])  # JSON claims

    async def test_get_from_redis(self):
        """Test getting token claims from Redis."""
        mock_redis = AsyncMock()
        token = "test-token"
        claims = {"user_id": "user-123", "email": "test@example.com"}
        
        # Mock Redis returning JSON
        mock_redis.get.return_value = json.dumps(claims)
        
        cache = TokenCache(redis_client=mock_redis)
        result = await cache.get(token)
        
        assert result == claims
        mock_redis.get.assert_called_once()

    async def test_get_from_redis_returns_none_on_miss(self):
        """Test get returns None when Redis has no value."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        cache = TokenCache(redis_client=mock_redis)
        result = await cache.get("nonexistent")
        
        assert result is None

    async def test_invalidate_with_redis(self):
        """Test invalidating token in Redis."""
        mock_redis = AsyncMock()
        cache = TokenCache(redis_client=mock_redis)
        
        await cache.invalidate("test-token")
        
        mock_redis.delete.assert_called_once()

    async def test_redis_error_handling_on_get(self):
        """Test graceful error handling when Redis get fails."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")
        
        cache = TokenCache(redis_client=mock_redis)
        result = await cache.get("test-token")
        
        # Should return None on error, not raise
        assert result is None

    async def test_redis_error_handling_on_set(self):
        """Test graceful error handling when Redis set fails."""
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        
        cache = TokenCache(redis_client=mock_redis)
        result = await cache.set("test-token", {"user_id": "123"})
        
        # Should return False on error
        assert result is False

    async def test_redis_error_handling_on_invalidate(self):
        """Test graceful error handling when Redis delete fails."""
        mock_redis = AsyncMock()
        mock_redis.delete.side_effect = Exception("Redis error")
        
        cache = TokenCache(redis_client=mock_redis)
        
        # Should not raise
        await cache.invalidate("test-token")


class TestTokenCacheStats:
    """Token cache statistics tracking."""

    async def test_record_stat_increments_counter(self):
        """Test recording stats increments Redis counter."""
        mock_redis = AsyncMock()
        cache = TokenCache(redis_client=mock_redis)
        
        await cache._record_stat("hits")
        
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()

    async def test_track_validation(self):
        """Test tracking validation stats."""
        mock_redis = AsyncMock()
        cache = TokenCache(redis_client=mock_redis)
        
        await cache.track_validation()
        
        # Should increment validations counter
        call_args = mock_redis.incr.call_args
        assert "validations" in call_args[0][0]

    async def test_track_miss(self):
        """Test tracking cache miss stats."""
        mock_redis = AsyncMock()
        cache = TokenCache(redis_client=mock_redis)
        
        await cache.track_miss()
        
        # Should increment misses counter
        call_args = mock_redis.incr.call_args
        assert "misses" in call_args[0][0]

    async def test_get_stats_no_redis(self):
        """Test getting stats without Redis returns defaults."""
        cache = TokenCache(redis_client=None)
        
        stats = await cache.get_stats()
        
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["validations"] == 0
        assert stats["hit_ratio"] == 0.0

    async def test_get_stats_with_redis(self):
        """Test getting stats from Redis."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = lambda key: {
            "auth:token:stats:hits": "100",
            "auth:token:stats:misses": "25",
            "auth:token:stats:validations": "30",
        }.get(key, "0")
        
        cache = TokenCache(redis_client=mock_redis)
        stats = await cache.get_stats()
        
        assert stats["hits"] == 100
        assert stats["misses"] == 25
        assert stats["validations"] == 30
        assert stats["total_attempts"] == 125
        # 100/125 = 80%
        assert stats["hit_ratio"] == 80.0

    async def test_get_stats_zero_attempts(self):
        """Test hit ratio calculation with zero attempts."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "0"
        
        cache = TokenCache(redis_client=mock_redis)
        stats = await cache.get_stats()
        
        assert stats["hit_ratio"] == 0.0

    async def test_get_stats_error_handling(self):
        """Test get_stats handles Redis errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")
        
        cache = TokenCache(redis_client=mock_redis)
        stats = await cache.get_stats()
        
        # Should return defaults on error
        assert stats["hits"] == 0
        assert stats["misses"] == 0


class TestTokenCacheGlobalInstance:
    """Token cache global singleton."""

    async def test_get_token_cache_returns_singleton(self):
        """Test get_token_cache returns same instance."""
        await reset_token_cache()
        
        cache1 = await get_token_cache()
        cache2 = await get_token_cache()
        
        assert cache1 is cache2

    async def test_reset_token_cache_clears_singleton(self):
        """Test reset_token_cache clears the global instance."""
        cache1 = await get_token_cache()
        
        await reset_token_cache()
        
        cache2 = await get_token_cache()
        
        # Should be different instances
        assert cache1 is not cache2

    async def test_token_cache_global_stores_to_memory_when_no_redis(self):
        """Test global token cache uses memory when Redis unavailable."""
        await reset_token_cache()
        
        cache = await get_token_cache()
        
        # Set and get
        token = "test-token"
        claims = {"user_id": "user-123"}
        await cache.set(token, claims)
        result = await cache.get(token)
        
        assert result == claims
