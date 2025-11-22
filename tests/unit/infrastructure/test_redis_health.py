"""Tests for Redis health checks."""

import pytest
from unittest.mock import AsyncMock, patch
from infrastructure.redis_health import check_redis_health


class TestRedisHealth:
    """Test Redis health checking functionality."""

    @pytest.mark.asyncio
    async def test_check_redis_health_success(self):
        """Test successful Redis health check."""
        with patch('infrastructure.upstash_provider.get_upstash_redis') as mock_get:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value="PONG")
            mock_get.return_value = mock_redis

            result = await check_redis_health()
            assert result['status'] == 'healthy'
            assert result['connected'] is True

    @pytest.mark.asyncio
    async def test_check_redis_health_failure(self):
        """Test failed Redis health check."""
        with patch('infrastructure.upstash_provider.get_upstash_redis') as mock_get:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get.return_value = mock_redis

            result = await check_redis_health()
            assert result['status'] == 'unhealthy'
            assert result['connected'] is False

    @pytest.mark.asyncio
    async def test_check_redis_health_unconfigured(self):
        """Test Redis health check when unconfigured."""
        with patch('infrastructure.upstash_provider.get_upstash_redis') as mock_get:
            mock_get.return_value = None

            result = await check_redis_health()
            assert result['status'] == 'unconfigured'

    @pytest.mark.asyncio
    async def test_check_redis_health_timeout(self):
        """Test Redis health check with timeout."""
        with patch('infrastructure.upstash_provider.get_upstash_redis') as mock_get:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=TimeoutError("Connection timeout"))
            mock_get.return_value = mock_redis

            result = await check_redis_health()
            assert result['status'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_check_redis_health_response_format(self):
        """Test Redis health check response format."""
        with patch('infrastructure.upstash_provider.get_upstash_redis') as mock_get:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value="PONG")
            mock_get.return_value = mock_redis

            result = await check_redis_health()
            assert 'status' in result
            assert 'connected' in result
            assert 'backend' in result

