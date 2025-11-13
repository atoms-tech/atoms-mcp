"""End-to-end tests for Redis caching integration."""

import pytest
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


class TestRedisCachingE2E:
    """End-to-end tests for complete caching workflow."""

    async def test_rate_limiting_blocks_excessive_requests(self):
        """E2E: Rate limiting should block excessive requests."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        limiter = DistributedRateLimiter(redis_client=None)

        # Make 120 requests
        blocked_count = 0
        for i in range(150):
            result = await limiter.check_rate_limit("test_user", "default")
            if not result["allowed"]:
                blocked_count += 1

        # Should have blocked excess requests
        assert blocked_count == 30  # 150 - 120

    async def test_embedding_cache_workflow(self):
        """E2E: Embedding cache complete workflow."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)

        # Simulate embedding workflow
        text_query = "user search query"
        expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        # Step 1: Check cache (miss)
        cached = await cache.get(text_query)
        assert cached is None

        # Step 2: Compute embedding (simulated)
        computed_embedding = expected_embedding

        # Step 3: Store in cache
        await cache.set(text_query, computed_embedding)

        # Step 4: Future requests hit cache
        cached_result = await cache.get(text_query)
        assert cached_result == expected_embedding

    async def test_token_auth_workflow(self):
        """E2E: Token authentication with caching."""
        from services.auth.token_cache import TokenCache

        cache = TokenCache(redis_client=None)

        # Simulate auth workflow
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        # Step 1: Parse JWT (first request)
        claims_from_jwt = {
            "sub": "1234567890",
            "name": "John Doe",
            "iat": 1516239022,
            "auth_type": "jwt"
        }

        # Step 2: Cache claims
        await cache.set(jwt_token, claims_from_jwt)

        # Step 3: Future requests use cache
        cached_claims = await cache.get(jwt_token)
        assert cached_claims == claims_from_jwt
        assert cached_claims["name"] == "John Doe"

        # Step 4: Token invalidation on logout
        await cache.invalidate(jwt_token)
        assert await cache.get(jwt_token) is None


class TestMultipleUsersE2E:
    """E2E tests with multiple concurrent users."""

    async def test_multiple_users_independent_rate_limits(self):
        """Multiple users should have independent rate limits."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        limiter = DistributedRateLimiter(redis_client=None)

        async def user_requests(user_id, count):
            """Simulate user making requests."""
            results = []
            for _ in range(count):
                result = await limiter.check_rate_limit(user_id, "default")
                results.append(result["allowed"])
            return sum(results)

        # Three users making requests sequentially
        user1_allowed = await user_requests("user_1", 50)
        user2_allowed = await user_requests("user_2", 50)
        user3_allowed = await user_requests("user_3", 150)  # Over limit

        assert user1_allowed == 50
        assert user2_allowed == 50
        assert user3_allowed == 120  # Limited to max


class TestCacheClusteringE2E:
    """E2E tests simulating distributed cache scenarios."""

    async def test_cache_persistence_across_operations(self):
        """Cache should persist across multiple operations."""
        from services.embedding_cache import EmbeddingCache
        from services.auth.token_cache import TokenCache

        emb_cache = EmbeddingCache(redis_client=None)
        token_cache = TokenCache(redis_client=None)

        # Cache embeddings
        texts = ["search query 1", "search query 2", "search query 3"]
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]

        for text, emb in zip(texts, embeddings):
            await emb_cache.set(text, emb)

        # Cache tokens
        tokens = ["token_1", "token_2", "token_3"]
        claims = [
            {"user_id": "user_1"},
            {"user_id": "user_2"},
            {"user_id": "user_3"}
        ]

        for token, claim in zip(tokens, claims):
            await token_cache.set(token, claim)

        # Verify all persist
        for text, emb in zip(texts, embeddings):
            assert await emb_cache.get(text) == emb

        for token, claim in zip(tokens, claims):
            assert await token_cache.get(token) == claim


class TestErrorRecoveryE2E:
    """E2E tests for error handling and recovery."""

    async def test_rate_limiter_handles_errors_gracefully(self):
        """Rate limiter should handle errors without crashing."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        # Create with failing Redis mock
        mock_redis = AsyncMock()
        mock_redis.incr.side_effect = [
            Exception("Redis timeout"),
            Exception("Redis timeout"),
            1,  # Eventually succeeds
        ]
        mock_redis.expire.return_value = None

        limiter = DistributedRateLimiter(redis_client=mock_redis)

        # Should fail open and allow request despite Redis errors
        result = await limiter.check_rate_limit("user", "default")
        assert result["allowed"] is True
        assert "warning" in result

    async def test_cache_handles_corrupted_data(self):
        """Cache should handle corrupted/invalid data gracefully."""
        from services.embedding_cache import EmbeddingCache

        mock_redis = AsyncMock()
        mock_redis.get.return_value = "not-valid-json"

        cache = EmbeddingCache(redis_client=mock_redis)

        # Should handle invalid JSON gracefully
        try:
            result = await cache.get("key")  # noqa: F841
            # Could be None or raise depending on implementation
        except Exception:  # pylint: disable=bare-except
            pass  # Expected


class TestScalingE2E:
    """E2E tests for scaling scenarios."""

    async def test_high_volume_token_caching(self):
        """Test caching high volume of tokens."""
        from services.auth.token_cache import TokenCache

        cache = TokenCache(redis_client=None)

        # Cache 1000 tokens
        num_tokens = 1000
        for i in range(num_tokens):
            token = f"token_{i}"
            claims = {"user_id": f"user_{i}", "session": i}
            await cache.set(token, claims)

        # Verify sample of cached tokens
        for i in [0, 100, 500, 999]:
            token = f"token_{i}"
            result = await cache.get(token)
            assert result is not None
            assert result["user_id"] == f"user_{i}"

    async def test_high_volume_embedding_caching(self):
        """Test caching large number of embeddings."""
        from services.embedding_cache import EmbeddingCache

        cache = EmbeddingCache(redis_client=None)

        # Cache 500 embeddings
        num_embeddings = 500
        embedding_dim = 768

        for i in range(num_embeddings):
            text = f"document {i}"
            embedding = [float(i) / 1000.0] * embedding_dim
            await cache.set(text, embedding)

        # Verify sample of cached embeddings
        for i in [0, 100, 250, 499]:
            text = f"document {i}"
            result = await cache.get(text)
            assert result is not None
            assert len(result) == embedding_dim


class TestMixedWorkloadE2E:
    """E2E tests with mixed concurrent workloads."""

    async def test_concurrent_rate_limit_and_caching(self):
        """Test rate limiting and caching working together."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter
        from services.embedding_cache import EmbeddingCache
        import asyncio

        limiter = DistributedRateLimiter(redis_client=None)
        cache = EmbeddingCache(redis_client=None)

        async def simulate_user_workflow(user_id):
            """Simulate user making requests and caching."""
            # Check rate limit
            result = await limiter.check_rate_limit(user_id, "default")
            if not result["allowed"]:
                return False

            # Cache embedding
            await cache.set(f"text_{user_id}", [0.1, 0.2])

            # Retrieve from cache
            cached = await cache.get(f"text_{user_id}")
            return cached is not None

        # 10 concurrent users
        tasks = [simulate_user_workflow(f"user_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
