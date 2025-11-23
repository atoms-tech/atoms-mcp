"""Week 1 tests for Redis monitoring."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestRedisMetricsWeek1:
    """Test Redis metrics tracking."""

    @pytest.fixture
    def redis_client(self):
        """Create a mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def metrics(self, redis_client):
        """Create a RedisMetrics instance."""
        from infrastructure.redis_monitoring import RedisMetrics
        return RedisMetrics(redis_client)

    @pytest.mark.asyncio
    async def test_metrics_initialization(self, metrics):
        """Test metrics initialization."""
        assert metrics is not None
        assert metrics.local_stats is not None
        assert "embedding_cache_hits" in metrics.local_stats
        assert "token_cache_hits" in metrics.local_stats
        assert "rate_limit_checks" in metrics.local_stats

    @pytest.mark.asyncio
    async def test_metrics_initialization_no_redis(self):
        """Test metrics initialization without Redis."""
        from infrastructure.redis_monitoring import RedisMetrics
        metrics = RedisMetrics(None)
        assert metrics is not None
        assert metrics.redis is None

    @pytest.mark.asyncio
    async def test_get_all_metrics(self, metrics):
        """Test getting all metrics."""
        with patch('infrastructure.redis_monitoring.RedisMetrics._get_embedding_cache_stats', new_callable=AsyncMock) as mock_embed, \
             patch('infrastructure.redis_monitoring.RedisMetrics._get_token_cache_stats', new_callable=AsyncMock) as mock_token, \
             patch('infrastructure.redis_monitoring.RedisMetrics._get_rate_limit_stats', new_callable=AsyncMock) as mock_rate, \
             patch('infrastructure.redis_monitoring.RedisMetrics._get_redis_status', new_callable=AsyncMock) as mock_status:
            
            mock_embed.return_value = {"hits": 100}
            mock_token.return_value = {"hits": 50}
            mock_rate.return_value = {"checks": 1000}
            mock_status.return_value = {"status": "connected"}
            
            result = await metrics.get_all_metrics()
            assert "timestamp" in result
            assert "embedding_cache" in result
            assert "token_cache" in result
            assert "rate_limiting" in result
            assert "redis_status" in result

    @pytest.mark.asyncio
    async def test_get_all_metrics_error_handling(self, metrics):
        """Test error handling in metrics collection."""
        with patch('infrastructure.redis_monitoring.RedisMetrics._get_embedding_cache_stats', new_callable=AsyncMock) as mock_embed:
            mock_embed.side_effect = Exception("Redis error")
            
            result = await metrics.get_all_metrics()
            # Should handle error gracefully
            assert result is not None

    @pytest.mark.asyncio
    async def test_embedding_cache_stats_with_redis(self, metrics):
        """Test embedding cache stats with Redis."""
        with patch('services.embedding_cache.get_embedding_cache', new_callable=AsyncMock) as mock_get:
            mock_cache = AsyncMock()
            mock_cache.get_stats = AsyncMock(return_value={
                "hits": 100,
                "misses": 20,
                "total": 120,
                "hit_ratio": 0.833
            })
            mock_get.return_value = mock_cache
            
            result = await metrics._get_embedding_cache_stats()
            assert result["backend"] == "upstash_redis"
            assert result["hits"] == 100
            assert result["misses"] == 20

    @pytest.mark.asyncio
    async def test_embedding_cache_stats_no_redis(self):
        """Test embedding cache stats without Redis."""
        from infrastructure.redis_monitoring import RedisMetrics
        metrics = RedisMetrics(None)
        
        result = await metrics._get_embedding_cache_stats()
        assert result["backend"] == "none"

    @pytest.mark.asyncio
    async def test_token_cache_stats_with_redis(self, metrics):
        """Test token cache stats with Redis."""
        with patch('services.auth.token_cache.get_token_cache', new_callable=AsyncMock) as mock_get:
            mock_cache = AsyncMock()
            mock_cache.get_stats = AsyncMock(return_value={
                "hits": 500,
                "misses": 50,
                "total": 550,
                "hit_ratio": 0.909
            })
            mock_get.return_value = mock_cache
            
            result = await metrics._get_token_cache_stats()
            assert result["backend"] == "upstash_redis"
            assert result["hits"] == 500

    @pytest.mark.asyncio
    async def test_rate_limit_stats(self, metrics):
        """Test rate limit stats."""
        with patch('infrastructure.security.get_rate_limiter', new_callable=AsyncMock) as mock_get:
            mock_limiter = AsyncMock()
            mock_limiter.get_stats = AsyncMock(return_value={
                "total_checks": 10000,
                "exceeded": 50,
                "active_users": 100
            })
            mock_get.return_value = mock_limiter
            
            result = await metrics._get_rate_limit_stats()
            assert result is not None

    @pytest.mark.asyncio
    async def test_redis_status(self, metrics):
        """Test Redis status check."""
        result = await metrics._get_redis_status()
        assert result is not None

    @pytest.mark.asyncio
    async def test_metrics_local_stats_tracking(self, metrics):
        """Test local stats tracking."""
        assert metrics.local_stats["embedding_cache_hits"] == 0
        assert metrics.local_stats["token_cache_hits"] == 0
        assert metrics.local_stats["rate_limit_checks"] == 0

    @pytest.mark.asyncio
    async def test_metrics_timestamp(self, metrics):
        """Test timestamp generation."""
        timestamp = metrics._get_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, (str, int, float))

