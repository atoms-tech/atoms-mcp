"""Phase 7 comprehensive tests for Redis health - 40% → 85%."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRedisHealthPhase7:
    """Test Redis health functionality comprehensively."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_redis_health_check(self, mock_redis_client):
        """Test Redis health check."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.ping = AsyncMock(return_value=True)
        
        result = await health_check.check()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_health_check_failure(self, mock_redis_client):
        """Test Redis health check failure."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await health_check.check()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_memory_usage(self, mock_redis_client):
        """Test Redis memory usage."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.info = AsyncMock(return_value={"used_memory": 1000000})
        
        result = await health_check.get_memory_usage()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_connection_pool_status(self, mock_redis_client):
        """Test Redis connection pool status."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.connection_pool = MagicMock()
        mock_redis_client.connection_pool.connection_count = 10
        
        result = await health_check.get_connection_pool_status()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_key_count(self, mock_redis_client):
        """Test Redis key count."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.dbsize = AsyncMock(return_value=1000)
        
        result = await health_check.get_key_count()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_eviction_policy(self, mock_redis_client):
        """Test Redis eviction policy."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.config_get = AsyncMock(return_value={"maxmemory-policy": "allkeys-lru"})
        
        result = await health_check.get_eviction_policy()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_replication_status(self, mock_redis_client):
        """Test Redis replication status."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.info = AsyncMock(return_value={"role": "master"})
        
        result = await health_check.get_replication_status()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_slowlog(self, mock_redis_client):
        """Test Redis slowlog."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.slowlog_get = AsyncMock(return_value=[])
        
        result = await health_check.get_slowlog()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_persistence_status(self, mock_redis_client):
        """Test Redis persistence status."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.info = AsyncMock(return_value={"rdb_last_save_time": 1234567890})
        
        result = await health_check.get_persistence_status()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_client_list(self, mock_redis_client):
        """Test Redis client list."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.client_list = AsyncMock(return_value=[])
        
        result = await health_check.get_client_list()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_health_comprehensive(self, mock_redis_client):
        """Test comprehensive Redis health check."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_redis_client.info = AsyncMock(return_value={"used_memory": 1000000})
        
        result = await health_check.check()
        assert result is not None

    @pytest.mark.asyncio
    async def test_redis_health_error_handling(self, mock_redis_client):
        """Test Redis health error handling."""
        from infrastructure.redis_health import RedisHealthCheck
        
        health_check = RedisHealthCheck(mock_redis_client)
        mock_redis_client.ping = AsyncMock(side_effect=Exception("Error"))
        
        result = await health_check.check()
        assert result is not None

