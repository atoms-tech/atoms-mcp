"""Tests for distributed rate limiter."""

import pytest
import asyncio
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


class TestDistributedRateLimiter:
    """Test distributed rate limiter with Redis backend."""

    @pytest.fixture
    def limiter_in_memory(self):
        """Limiter using in-memory storage (no Redis)."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter
        return DistributedRateLimiter(redis_client=None)

    @pytest.fixture
    def limiter_with_redis(self):
        """Limiter with mock Redis backend."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter
        mock_redis = AsyncMock()
        return DistributedRateLimiter(redis_client=mock_redis), mock_redis

    async def test_allows_requests_within_limit(self, limiter_in_memory):
        """Should allow requests within rate limit."""
        for i in range(120):
            result = await limiter_in_memory.check_rate_limit("user_1", "default")
            assert result["allowed"] is True
            assert result["current_count"] == i + 1

    async def test_blocks_requests_over_limit(self, limiter_in_memory):
        """Should block requests exceeding rate limit."""
        # Fill quota
        for _ in range(120):
            await limiter_in_memory.check_rate_limit("user_1", "default")

        # Next request should be blocked
        result = await limiter_in_memory.check_rate_limit("user_1", "default")
        assert result["allowed"] is False
        assert result["error"] is not None
        assert result["retry_after"] == 60

    async def test_different_operation_types_independent(self, limiter_in_memory):
        """Different operation types should have independent limits."""
        # Search limit: 30/min
        for i in range(30):
            result = await limiter_in_memory.check_rate_limit("user_1", "search")
            assert result["allowed"] is True

        # 31st search blocked
        result = await limiter_in_memory.check_rate_limit("user_1", "search")
        assert result["allowed"] is False

        # But default should still work (separate counter)
        result = await limiter_in_memory.check_rate_limit("user_1", "default")
        assert result["allowed"] is True

    async def test_different_users_independent(self, limiter_in_memory):
        """Different users should have independent limits."""
        # Fill user_1 quota
        for _ in range(120):
            await limiter_in_memory.check_rate_limit("user_1", "default")

        # user_2 should still have quota
        result = await limiter_in_memory.check_rate_limit("user_2", "default")
        assert result["allowed"] is True

    async def test_get_remaining_calculates_correctly(self, limiter_in_memory):
        """get_remaining should return correct count."""
        # Make 50 requests
        for _ in range(50):
            await limiter_in_memory.check_rate_limit("user_1", "default")

        remaining = await limiter_in_memory.get_remaining("user_1", "default")
        assert remaining == 70  # 120 - 50

    async def test_get_remaining_returns_max_when_no_requests(self, limiter_in_memory):
        """get_remaining should return full limit for new user."""
        remaining = await limiter_in_memory.get_remaining("user_new", "default")
        assert remaining == 120

    async def test_reset_user_clears_counter(self, limiter_in_memory):
        """reset_user should clear rate limit counter."""
        # Fill quota
        for _ in range(120):
            await limiter_in_memory.check_rate_limit("user_1", "default")

        # Reset
        await limiter_in_memory.reset_user("user_1", "default")

        # Should allow requests again
        result = await limiter_in_memory.check_rate_limit("user_1", "default")
        assert result["allowed"] is True

    async def test_get_stats_returns_limit_info(self, limiter_in_memory):
        """get_stats should return rate limit statistics."""
        # Make 30 requests
        for _ in range(30):
            await limiter_in_memory.check_rate_limit("user_1", "default")

        stats = await limiter_in_memory.get_stats("user_1")

        assert "default" in stats
        assert stats["default"]["limit"] == 120
        assert stats["default"]["remaining"] == 90
        assert stats["default"]["used"] == 30

    async def test_redis_incr_integration(self):
        """Test Redis INCR backend integration."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        mock_redis = AsyncMock()
        mock_redis.incr.side_effect = [1, 2, 3]  # Return incrementing values
        mock_redis.expire.return_value = None

        limiter = DistributedRateLimiter(redis_client=mock_redis)

        # Check rate limit - should use INCR
        result1 = await limiter.check_rate_limit("user_1", "default")
        result2 = await limiter.check_rate_limit("user_1", "default")

        assert result1["allowed"] is True
        assert result2["allowed"] is True
        assert mock_redis.incr.call_count == 2

    async def test_missing_user_id_returns_error(self, limiter_in_memory):
        """Missing user_id should return error."""
        result = await limiter_in_memory.check_rate_limit("", "default")
        assert result["allowed"] is False
        assert result["error"] is not None

    async def test_unknown_operation_type_uses_default(self, limiter_in_memory):
        """Unknown operation type should use default limits."""
        result = await limiter_in_memory.check_rate_limit("user_1", "unknown_op")
        assert result["allowed"] is True
        assert result["limit"] == 120  # Default limit

    async def test_redis_error_handling(self):
        """Test graceful handling of Redis errors (fail open)."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter

        mock_redis = AsyncMock()
        mock_redis.incr.side_effect = Exception("Redis connection error")

        limiter = DistributedRateLimiter(redis_client=mock_redis)

        # Should fail open - allow request even if Redis fails
        result = await limiter.check_rate_limit("user_1", "default")
        assert result["allowed"] is True
        assert "warning" in result

    async def test_concurrent_requests_same_user(self, limiter_in_memory):
        """Multiple concurrent requests from same user should respect limit."""
        async def make_request():
            return await limiter_in_memory.check_rate_limit("user_1", "default")

        # Make 150 concurrent requests (over limit of 120)
        tasks = [make_request() for _ in range(150)]
        results = await asyncio.gather(*tasks)

        allowed = sum(1 for r in results if r["allowed"])
        blocked = sum(1 for r in results if not r["allowed"])

        # Should allow exactly 120, block the rest
        assert allowed == 120
        assert blocked == 30

    async def test_all_operation_types_exist(self, limiter_in_memory):
        """All operation types should have defined limits."""
        operation_types = ["default", "search", "create", "update", "delete", "auth"]

        for op_type in operation_types:
            assert op_type in limiter_in_memory.limits
            assert "requests" in limiter_in_memory.limits[op_type]
            assert "window" in limiter_in_memory.limits[op_type]


class TestRateLimiterEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def limiter(self):
        """Rate limiter for edge case tests."""
        from infrastructure.distributed_rate_limiter import DistributedRateLimiter
        return DistributedRateLimiter(redis_client=None)

    async def test_exactly_at_limit(self, limiter):
        """Request at exact limit should be allowed."""
        # Make exactly 120 requests
        for i in range(120):
            result = await limiter.check_rate_limit("user_1", "default")
            assert result["allowed"] is True

        # 121st should be blocked
        result = await limiter.check_rate_limit("user_1", "default")
        assert result["allowed"] is False

    async def test_very_large_user_id(self, limiter):
        """Should handle very large user IDs."""
        large_id = "u" * 1000
        result = await limiter.check_rate_limit(large_id, "default")
        assert result["allowed"] is True

    async def test_special_characters_in_user_id(self, limiter):
        """Should handle special characters in user ID."""
        special_id = "user_123@domain.com!#$%"
        result = await limiter.check_rate_limit(special_id, "default")
        assert result["allowed"] is True

    async def test_window_reset_simulation(self, limiter):
        """Simulate window reset by clearing counter."""
        # Fill window
        for _ in range(120):
            await limiter.check_rate_limit("user_1", "default")

        # Verify blocked
        assert (await limiter.check_rate_limit("user_1", "default"))["allowed"] is False

        # Reset user
        await limiter.reset_user("user_1", "default")

        # Should allow again
        result = await limiter.check_rate_limit("user_1", "default")
        assert result["allowed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
