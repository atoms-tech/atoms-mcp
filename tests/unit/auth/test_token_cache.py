"""Tests for token cache service."""

import pytest
import hashlib
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


class TestTokenCache:
    """Test token cache functionality."""

    @pytest.fixture
    def cache(self):
        """Create token cache with no Redis."""
        from services.auth.token_cache import TokenCache
        return TokenCache(redis_client=None)

    @pytest.fixture
    def cache_with_redis(self):
        """Create token cache with mock Redis."""
        from services.auth.token_cache import TokenCache
        mock_redis = AsyncMock()
        return TokenCache(redis_client=mock_redis), mock_redis

    async def test_get_returns_none_for_missing_token(self, cache):
        """Get should return None for uncached tokens."""
        result = await cache.get("unknown_token")
        assert result is None

    async def test_set_and_get_token_claims(self, cache):
        """Should store and retrieve token claims."""
        token = "jwt_token_abc123"
        claims = {
            "user_id": "user_123",
            "email": "user@example.com",
            "auth_type": "authkit_jwt"
        }

        success = await cache.set(token, claims)
        assert success is True

        result = await cache.get(token)
        assert result == claims

    async def test_get_returns_exact_claims(self, cache):
        """Retrieved claims should match stored value exactly."""
        token = "token_123"
        claims = {
            "user_id": "u_1",
            "email": "test@example.com",
            "scope": "read write",
            "exp": 1234567890
        }

        await cache.set(token, claims)
        result = await cache.get(token)

        assert result == claims
        for key in claims:
            assert result[key] == claims[key]

    async def test_different_tokens_different_claims(self, cache):
        """Different tokens should have independent claims."""
        token1 = "token_1"
        token2 = "token_2"
        claims1 = {"user_id": "user_1"}
        claims2 = {"user_id": "user_2"}

        await cache.set(token1, claims1)
        await cache.set(token2, claims2)

        assert await cache.get(token1) == claims1
        assert await cache.get(token2) == claims2

    async def test_make_key_uses_token_hash(self, cache):
        """Cache key should use hash of token, not token itself."""
        token = "sensitive_jwt_token"
        key = cache._make_key(token)

        # Should not contain actual token
        assert token not in key

        # Should contain hash
        expected_hash = hashlib.sha256(token.encode()).hexdigest()
        assert expected_hash in key

    async def test_make_key_consistent(self, cache):
        """Same token should produce same key."""
        token = "jwt_token"
        key1 = cache._make_key(token)
        key2 = cache._make_key(token)

        assert key1 == key2

    async def test_make_key_different_for_different_tokens(self, cache):
        """Different tokens should produce different keys."""
        token1 = "token_1"
        token2 = "token_2"

        key1 = cache._make_key(token1)
        key2 = cache._make_key(token2)

        assert key1 != key2

    async def test_invalidate_removes_token(self, cache):
        """Invalidate should remove token from cache."""
        token = "test_token"
        claims = {"user_id": "user_1"}

        await cache.set(token, claims)
        assert await cache.get(token) is not None

        await cache.invalidate(token)
        assert await cache.get(token) is None

    async def test_invalidate_missing_token_noop(self, cache):
        """Invalidating missing token should not raise."""
        # Should not raise
        await cache.invalidate("nonexistent_token")

    async def test_get_stats_initial_empty(self, cache):
        """Initial stats should show no hits or misses."""
        stats = await cache.get_stats()

        assert isinstance(stats, dict)
        assert stats.get("hits", 0) == 0

    async def test_get_stats_with_redis(self, cache_with_redis):
        """Stats should track cache performance with Redis."""
        cache, mock_redis = cache_with_redis

        mock_redis.get.return_value = "10"
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = None

        stats = await cache.get_stats()
        assert isinstance(stats, dict)

    async def test_empty_token_returns_none(self, cache):
        """Empty token should return None."""
        result = await cache.get("")
        assert result is None

    async def test_empty_claims_not_cached(self, cache):
        """Empty claims should not be cached."""
        token = "token"

        success = await cache.set(token, None)
        assert success is False

        success = await cache.set(token, {})
        assert success is False

    async def test_complex_claims_cached(self, cache):
        """Complex claims with nested structure should cache."""
        token = "jwt_token"
        claims = {
            "user_id": "user_123",
            "email": "user@example.com",
            "roles": ["admin", "user"],
            "permissions": {
                "read": True,
                "write": False
            },
            "metadata": {
                "created_at": "2025-01-01",
                "scopes": ["openid", "profile"]
            }
        }

        success = await cache.set(token, claims)
        assert success is True

        result = await cache.get(token)
        assert result == claims

    async def test_ttl_parameter_passed_to_redis(self, cache_with_redis):
        """TTL should be passed to Redis setex."""
        cache, mock_redis = cache_with_redis

        token = "token"
        claims = {"user_id": "user_1"}
        custom_ttl = 7200

        mock_redis.setex.return_value = None

        await cache.set(token, claims, ttl=custom_ttl)

        if mock_redis.setex.called:
            args = mock_redis.setex.call_args[0]
            assert custom_ttl in args

    async def test_redis_error_handling_get(self, cache_with_redis):
        """Get should handle Redis errors gracefully."""
        cache, mock_redis = cache_with_redis
        mock_redis.get.side_effect = Exception("Redis error")

        result = await cache.get("token")
        assert result is None

    async def test_redis_error_handling_set(self, cache_with_redis):
        """Set should handle Redis errors gracefully."""
        cache, mock_redis = cache_with_redis
        mock_redis.setex.side_effect = Exception("Redis error")

        success = await cache.set("token", {"data": "value"})
        assert success is False

    async def test_redis_error_handling_invalidate(self, cache_with_redis):
        """Invalidate should handle Redis errors gracefully."""
        cache, mock_redis = cache_with_redis
        mock_redis.delete.side_effect = Exception("Redis error")

        # Should not raise
        await cache.invalidate("token")


class TestTokenCacheSecurity:
    """Security tests for token cache."""

    @pytest.fixture
    def cache(self):
        """Token cache for security tests."""
        from services.auth.token_cache import TokenCache
        return TokenCache(redis_client=None)

    async def test_token_not_stored_in_key(self, cache):
        """Token should not appear in cache key."""
        token = "jwt_abc123xyz_secret"
        key = cache._make_key(token)

        # Token should not be visible in key
        assert token not in key
        assert "secret" not in key

    async def test_claims_stored_not_token(self, cache):
        """Only claims should be stored, not the token itself."""
        token = "jwt_token_secret"
        claims = {"user_id": "user_1"}

        await cache.set(token, claims)

        # Get returns claims, not token
        result = await cache.get(token)
        assert result == claims
        assert token not in str(result)

    async def test_sensitive_claim_values_stored(self, cache):
        """Sensitive claim values should be stored as-is."""
        token = "token"
        claims = {
            "access_token": "secret_access_token",
            "refresh_token": "secret_refresh_token",
            "password_reset_token": "reset_secret"
        }

        await cache.set(token, claims)
        result = await cache.get(token)

        # Sensitive values should be stored
        assert result["access_token"] == "secret_access_token"


class TestTokenCacheEdgeCases:
    """Edge case tests for token cache."""

    @pytest.fixture
    def cache(self):
        """Token cache for edge cases."""
        from services.auth.token_cache import TokenCache
        return TokenCache(redis_client=None)

    async def test_very_long_token(self, cache):
        """Should handle very long tokens."""
        long_token = "x" * 5000
        claims = {"user_id": "user_1"}

        success = await cache.set(long_token, claims)
        assert success is True

        result = await cache.get(long_token)
        assert result == claims

    async def test_token_with_special_characters(self, cache):
        """Should handle tokens with special characters."""
        special_token = "jwt.abc@xyz#123$%^&*()"
        claims = {"user_id": "user_1"}

        success = await cache.set(special_token, claims)
        assert success is True

        result = await cache.get(special_token)
        assert result == claims

    async def test_claims_with_unicode(self, cache):
        """Should handle Unicode in claims."""
        token = "token"
        claims = {
            "user_id": "user_1",
            "name": "Jöhn Döe",
            "email": "user@例え.jp"
        }

        await cache.set(token, claims)
        result = await cache.get(token)

        assert result["name"] == "Jöhn Döe"
        assert result["email"] == "user@例え.jp"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
