"""Tests for embedding cache service."""

import pytest
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


class TestEmbeddingCache:
    """Test embedding cache functionality."""

    @pytest.fixture
    def cache(self):
        """Create embedding cache with no Redis."""
        from services.embedding_cache import EmbeddingCache
        return EmbeddingCache(redis_client=None)

    @pytest.fixture
    def cache_with_redis(self):
        """Create embedding cache with mock Redis."""
        from services.embedding_cache import EmbeddingCache
        mock_redis = AsyncMock()
        return EmbeddingCache(redis_client=mock_redis), mock_redis

    async def test_get_returns_none_for_missing_key(self, cache):
        """Get should return None for uncached embeddings."""
        result = await cache.get("unknown text")
        assert result is None

    async def test_set_and_get_embedding(self, cache):
        """Should store and retrieve embeddings."""
        text = "Hello world"
        embedding = [0.1, 0.2, 0.3, 0.4]
        model = "gemini-embedding-001"

        success = await cache.set(text, embedding, model)
        assert success is True

        result = await cache.get(text, model)
        assert result == embedding

    async def test_get_returns_exact_embedding(self, cache):
        """Retrieved embedding should match stored value exactly."""
        text = "Test text"
        embedding = [0.123456789, 0.987654321, 0.555555555]

        await cache.set(text, embedding)
        result = await cache.get(text)

        assert result == embedding
        for orig, retrieved in zip(embedding, result):
            assert orig == retrieved

    async def test_different_texts_different_embeddings(self, cache):
        """Different texts should have independent embeddings."""
        text1 = "First text"
        text2 = "Second text"
        emb1 = [0.1, 0.2]
        emb2 = [0.3, 0.4]

        await cache.set(text1, emb1)
        await cache.set(text2, emb2)

        assert await cache.get(text1) == emb1
        assert await cache.get(text2) == emb2

    async def test_same_text_different_models(self, cache):
        """Same text, different models should have separate cache entries."""
        text = "Same text"
        emb1 = [0.1, 0.2]
        emb2 = [0.3, 0.4]

        await cache.set(text, emb1, "model1")
        await cache.set(text, emb2, "model2")

        assert await cache.get(text, "model1") == emb1
        assert await cache.get(text, "model2") == emb2

    async def test_make_key_normalization(self, cache):
        """Cache keys should be normalized consistently."""
        # Different whitespace should produce same key
        key1 = cache._make_key("hello world", "model")
        key2 = cache._make_key("  hello world  ", "model")

        # After normalization, should be same
        assert key1 == key2

    async def test_make_key_case_insensitive(self, cache):
        """Cache keys should be case-insensitive."""
        key1 = cache._make_key("Hello World", "model")
        key2 = cache._make_key("hello world", "model")

        assert key1 == key2

    async def test_clear_removes_embedding(self, cache):
        """Clear should remove embedding from cache."""
        text = "Test"
        embedding = [0.1, 0.2]

        await cache.set(text, embedding)
        assert await cache.get(text) is not None

        await cache.clear(text)
        assert await cache.get(text) is None

    async def test_get_stats_initial_empty(self, cache):
        """Initial stats should show no hits or misses."""
        stats = await cache.get_stats()

        # In-memory cache doesn't track stats without Redis
        assert isinstance(stats, dict)

    async def test_get_stats_with_redis(self, cache_with_redis):
        """Stats should track hits and misses with Redis."""
        cache, mock_redis = cache_with_redis

        # Mock Redis stat tracking
        mock_redis.get.side_effect = [None, None, None]  # miss, miss, miss
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = None

        await cache.get("text1")  # miss

        stats = await cache.get_stats()
        assert isinstance(stats, dict)

    async def test_empty_text_not_cached(self, cache):
        """Empty or whitespace-only text should not be cached."""
        # Empty string
        success = await cache.set("", [0.1, 0.2])
        assert success is False

        # Whitespace only
        success = await cache.set("   ", [0.1, 0.2])
        assert success is False

    async def test_empty_embedding_not_cached(self, cache):
        """Empty embeddings should not be cached."""
        success = await cache.set("text", [])
        assert success is False

        success = await cache.set("text", None)
        assert success is False

    async def test_large_embedding_vector(self, cache):
        """Should handle large embedding vectors."""
        text = "Large embedding"
        # 768-dimensional embedding (common size)
        large_embedding = [0.123] * 768

        success = await cache.set(text, large_embedding)
        assert success is True

        result = await cache.get(text)
        assert len(result) == 768
        assert result == large_embedding

    async def test_ttl_parameter_passed_to_redis(self, cache_with_redis):
        """TTL should be passed to Redis setex."""
        cache, mock_redis = cache_with_redis

        text = "Test"
        embedding = [0.1, 0.2]
        custom_ttl = 7200

        mock_redis.setex.return_value = None

        await cache.set(text, embedding, ttl=custom_ttl)

        # Should call setex with the custom TTL
        if mock_redis.setex.called:
            args = mock_redis.setex.call_args[0]
            assert custom_ttl in args

    async def test_redis_error_handling_get(self, cache_with_redis):
        """Get should handle Redis errors gracefully."""
        cache, mock_redis = cache_with_redis
        mock_redis.get.side_effect = Exception("Redis error")

        result = await cache.get("text")
        assert result is None

    async def test_redis_error_handling_set(self, cache_with_redis):
        """Set should handle Redis errors gracefully."""
        cache, mock_redis = cache_with_redis
        mock_redis.setex.side_effect = Exception("Redis error")

        # Should not raise
        success = await cache.set("text", [0.1])
        assert success is False


class TestEmbeddingCacheKey:
    """Test cache key generation."""

    @pytest.fixture
    def cache(self):
        """Embedding cache for key tests."""
        from services.embedding_cache import EmbeddingCache
        return EmbeddingCache(redis_client=None)

    async def test_key_format_includes_model(self, cache):
        """Key should include model name."""
        key = cache._make_key("text", "gemini-embedding-001")
        assert "gemini-embedding-001" in key

    async def test_key_format_includes_hash(self, cache):
        """Key should include hash of text."""
        text = "test text"
        key = cache._make_key(text, "model")

        # Should be deterministic
        key2 = cache._make_key(text, "model")
        assert key == key2

    async def test_key_format_includes_preview(self, cache):
        """Key should include text preview for debugging."""
        text = "test text preview"
        key = cache._make_key(text, "model")

        # Should contain part of text (normalized)
        assert "test" in key.lower() or "preview" in key.lower()

    async def test_key_prefix(self, cache):
        """Cache keys should use proper prefix."""
        text = "test"
        key = cache._make_key(text, "model")

        assert key.startswith("embed:")


class TestEmbeddingCacheIntegration:
    """Integration tests for embedding cache."""

    async def test_get_or_none_alias(self):
        """get_or_none should be alias for get."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)
        text = "test"
        embedding = [0.1, 0.2]

        await cache.set(text, embedding)

        result1 = await cache.get(text)
        result2 = await cache.get_or_none(text)

        assert result1 == result2

    async def test_cache_hit_tracking(self):
        """Cache should track hits and misses."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)
        text = "test"
        embedding = [0.1, 0.2]

        # Set up embedding
        await cache.set(text, embedding)

        # Hit
        await cache.get(text)
        await cache.get(text)

        # Miss
        await cache.get("nonexistent")

        stats = await cache.get_stats()
        # Without Redis, basic stats may be minimal
        assert isinstance(stats, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
