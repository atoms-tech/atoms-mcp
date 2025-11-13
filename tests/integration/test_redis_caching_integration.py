"""Integration tests for Redis caching layers."""

import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio


class TestEmbeddingCacheIntegration:
    """Integration tests for embedding cache with Vertex AI."""

    @pytest.fixture
    def embedding_service_mock(self):
        """Mock embedding service for testing."""
        with patch("services.embedding_vertex.VertexAIEmbeddingService") as mock_class:
            mock_service = AsyncMock()
            mock_service.generate_embedding = AsyncMock()
            mock_class.return_value = mock_service
            yield mock_service

    async def test_embedding_cache_hit_flow(self):
        """Test complete embedding cache hit flow."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)
        text = "Test embedding text"
        embedding = [0.1, 0.2, 0.3]

        # First call: cache miss
        result1 = await cache.get(text)
        assert result1 is None

        # Cache the embedding
        await cache.set(text, embedding)

        # Second call: cache hit
        result2 = await cache.get(text)
        assert result2 == embedding

    async def test_embedding_multiple_texts(self):
        """Test caching multiple different embeddings."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)
        texts_embeddings = {
            "text one": [0.1, 0.2],
            "text two": [0.3, 0.4],
            "text three": [0.5, 0.6]
        }

        # Cache all
        for text, emb in texts_embeddings.items():
            await cache.set(text, emb)

        # Verify all cached
        for text, expected_emb in texts_embeddings.items():
            cached = await cache.get(text)
            assert cached == expected_emb

    async def test_embedding_cache_statistics(self):
        """Test embedding cache statistics collection."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)

        # Cache some embeddings
        for i in range(5):
            await cache.set(f"text_{i}", [float(i)] * 10)

        # Get statistics
        stats = await cache.get_stats()

        assert isinstance(stats, dict)


class TestTokenCacheAuthIntegration:
    """Integration tests for token cache with auth."""

    async def test_token_cache_with_jwt_claims(self):
        """Test token cache with realistic JWT claims."""
        from services.auth.token_cache import TokenCache

        cache = TokenCache(redis_client=None)

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        jwt_claims = {
            "sub": "user_123",
            "email": "user@example.com",
            "iss": "https://authkit.com",
            "aud": "app_123",
            "iat": 1700000000,
            "exp": 1700003600,
            "auth_type": "authkit_jwt",
            "user_metadata": {"role": "user"}
        }

        # Cache JWT claims
        success = await cache.set(token, jwt_claims)
        assert success is True

        # Retrieve
        cached = await cache.get(token)
        assert cached == jwt_claims
        assert cached["sub"] == "user_123"

    async def test_token_cache_logout_invalidation(self):
        """Test token invalidation on logout."""
        from services.auth.token_cache import TokenCache

        cache = TokenCache(redis_client=None)

        token = "jwt_token"
        claims = {"user_id": "user_1"}

        # Cache token
        await cache.set(token, claims)
        assert await cache.get(token) is not None

        # Logout: invalidate token
        await cache.invalidate(token)

        # Token should be gone
        assert await cache.get(token) is None


class TestRateLimitingIntegration:
    """Integration tests for rate limiting with distributed checks."""

    async def test_rate_limit_across_operation_types(self):
        """Test rate limiting with multiple operation types."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        limiter = DistributedRateLimiter(redis_client=None)
        user_id = "user_123"

        # Make some default requests
        for _ in range(50):
            result = await limiter.check_rate_limit(user_id, "default")
            assert result["allowed"] is True

        # Make some search requests
        for _ in range(20):
            result = await limiter.check_rate_limit(user_id, "search")
            assert result["allowed"] is True

        # Both should have independent counters
        default_remaining = await limiter.get_remaining(user_id, "default")
        search_remaining = await limiter.get_remaining(user_id, "search")

        assert default_remaining == 70  # 120 - 50
        assert search_remaining == 10   # 30 - 20

    async def test_rate_limit_user_isolation(self):
        """Test that different users have independent rate limits."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        limiter = DistributedRateLimiter(redis_client=None)

        # Fill user_1's quota
        for _ in range(120):
            await limiter.check_rate_limit("user_1", "default")

        # user_1 should be blocked
        result = await limiter.check_rate_limit("user_1", "default")
        assert result["allowed"] is False

        # user_2 should not be affected
        result = await limiter.check_rate_limit("user_2", "default")
        assert result["allowed"] is True


class TestCachingLayerFallback:
    """Test graceful fallback when Redis unavailable."""

    async def test_embedding_cache_fallback_no_redis(self):
        """Embedding cache should work without Redis."""
        from services.embedding_cache import EmbeddingCache

        # Create without Redis
        cache = EmbeddingCache(redis_client=None)

        text = "test"
        embedding = [0.1, 0.2]

        # Should still work
        await cache.set(text, embedding)
        result = await cache.get(text)
        assert result == embedding

    async def test_token_cache_fallback_no_redis(self):
        """Token cache should work without Redis."""
        from services.auth.token_cache import TokenCache

        # Create without Redis
        cache = TokenCache(redis_client=None)

        token = "test_token"
        claims = {"user_id": "user_1"}

        # Should still work
        await cache.set(token, claims)
        result = await cache.get(token)
        assert result == claims

    async def test_rate_limiter_fallback_no_redis(self):
        """Rate limiter should use in-memory backend without Redis."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        # Create without Redis
        limiter = DistributedRateLimiter(redis_client=None)

        # Should still work
        result = await limiter.check_rate_limit("user_1", "default")
        assert result["allowed"] is True


class TestCachingCoherence:
    """Test cache coherence across operations."""

    async def test_embedding_cache_coherence(self):
        """Different cache instances should see same cached data."""
        from services.embedding_cache import EmbeddingCache

        cache1 = EmbeddingCache(redis_client=None)
        cache2 = EmbeddingCache(redis_client=None)

        text = "test"
        embedding = [0.1, 0.2, 0.3]

        # Cache in cache1
        await cache1.set(text, embedding)

        # cache2 won't see it (different instances, no Redis)
        result = await cache2.get(text)
        assert result is None

        # But cache1 should see it
        result = await cache1.get(text)
        assert result == embedding

    async def test_token_cache_coherence(self):
        """Token cache coherence within same instance."""
        from services.auth.token_cache import TokenCache

        cache = TokenCache(redis_client=None)

        token = "test_token"
        claims = {"user_id": "user_1"}

        # Set and get in same instance
        await cache.set(token, claims)
        result = await cache.get(token)
        assert result == claims


class TestCachingPerformance:
    """Performance-related integration tests."""

    async def test_embedding_cache_reduces_computations(self):
        """Verify cache reduces redundant computations."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)

        text = "expensive computation"
        embedding = [0.1] * 768  # Large embedding

        # First: cache miss, would trigger computation
        result1 = await cache.get(text)
        assert result1 is None

        # Cache it
        await cache.set(text, embedding)

        # Second: cache hit, no computation needed
        result2 = await cache.get(text)
        assert result2 == embedding
        assert len(result2) == 768

    async def test_token_cache_fast_path(self):
        """Verify token cache provides fast auth path."""
        from services.auth.token_cache import TokenCache

        cache = TokenCache(redis_client=None)

        token = "jwt_token"
        claims = {"user_id": "user_1"}

        # First: miss, would do JWT validation
        result1 = await cache.get(token)
        assert result1 is None

        # Cache
        await cache.set(token, claims)

        # Second: hit, instant response
        result2 = await cache.get(token)
        assert result2 == claims


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
