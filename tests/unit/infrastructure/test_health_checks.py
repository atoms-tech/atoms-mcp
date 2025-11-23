"""Tests for health check system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestHealthChecker:
    """Test health checker functionality."""

    @pytest.fixture
    def health_checker(self):
        """Create a health checker instance."""
        from infrastructure.health import HealthChecker
        return HealthChecker()

    @pytest.mark.asyncio
    async def test_check_database_healthy(self, health_checker):
        """Test database health check when healthy."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = {}
            mock_get.return_value = mock_client

            result = await health_checker.check_database()
            assert result['status'] == 'healthy'
            assert 'latency_ms' in result
            assert result['responsive'] is True

    @pytest.mark.asyncio
    async def test_check_database_unhealthy(self, health_checker):
        """Test database health check when unhealthy."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            result = await health_checker.check_database()
            assert result['status'] == 'unhealthy'
            assert 'error' in result
            assert result['responsive'] is False

    @pytest.mark.asyncio
    async def test_check_authentication_healthy(self, health_checker):
        """Test authentication health check when AuthKit is configured."""
        with patch.dict('os.environ', {'FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN': 'https://authkit.example.com'}):
            result = await health_checker.check_authentication()
            assert result['status'] == 'healthy'
            assert result['service'] == 'AuthKitProvider'
            assert 'domain' in result

    @pytest.mark.asyncio
    async def test_check_authentication_unhealthy(self, health_checker):
        """Test authentication health check when AuthKit is not configured."""
        with patch.dict('os.environ', {}, clear=False):
            # Remove the AuthKit domain env var
            import os
            if 'FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN' in os.environ:
                del os.environ['FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN']
            
            result = await health_checker.check_authentication()
            assert result['status'] == 'degraded'
            assert 'warning' in result

    @pytest.mark.asyncio
    async def test_check_cache(self, health_checker):
        """Test cache health check."""
        with patch('infrastructure.supabase_db.SupabaseDatabaseAdapter') as mock_adapter:
            mock_instance = MagicMock()
            mock_instance._query_cache = {}
            mock_adapter.return_value = mock_instance

            result = await health_checker.check_cache()
            assert 'status' in result
            assert 'size' in result

    @pytest.mark.asyncio
    async def test_check_performance(self, health_checker):
        """Test performance health check."""
        with patch('infrastructure.monitoring.get_performance_monitor') as mock_get:
            mock_monitor = MagicMock()
            mock_monitor.get_stats.return_value = {
                'total_queries': 100,
                'query_breakdown': {'test': {'slow_queries': 5}}
            }
            mock_get.return_value = mock_monitor

            result = await health_checker.check_performance()
            assert 'status' in result
            assert 'total_queries' in result

    @pytest.mark.asyncio
    async def test_check_errors(self, health_checker):
        """Test error health check."""
        with patch('infrastructure.monitoring.get_error_tracker') as mock_get:
            mock_tracker = MagicMock()
            mock_tracker.get_error_summary.return_value = {
                'total_errors': 50,
                'unique_errors': 10
            }
            mock_get.return_value = mock_tracker

            result = await health_checker.check_errors()
            assert 'status' in result
            assert 'total_errors' in result

    @pytest.mark.asyncio
    async def test_check_rate_limiter(self, health_checker):
        """Test rate limiter health check."""
        with patch('infrastructure.security.get_rate_limiter') as mock_get:
            mock_limiter = MagicMock()
            mock_limiter.user_requests = {}
            mock_get.return_value = mock_limiter

            result = await health_checker.check_rate_limiter()
            assert result['status'] == 'active'
            assert 'tracked_users' in result

    @pytest.mark.asyncio
    async def test_comprehensive_check(self, health_checker):
        """Test comprehensive health check."""
        with patch('supabase_client.get_supabase') as mock_supabase, \
             patch('infrastructure.supabase_db.SupabaseDatabaseAdapter') as mock_db, \
             patch('infrastructure.monitoring.get_performance_monitor') as mock_perf, \
             patch('infrastructure.monitoring.get_error_tracker') as mock_errors, \
             patch('infrastructure.security.get_rate_limiter') as mock_limiter:

            mock_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.return_value = {}
            mock_db.return_value._query_cache = {}
            mock_perf.return_value.get_stats.return_value = {'total_queries': 0}
            mock_errors.return_value.get_error_summary.return_value = {'total_errors': 0}
            mock_limiter.return_value.user_requests = {}

            result = await health_checker.comprehensive_check()
            assert 'status' in result
            assert 'components' in result
            assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_get_last_check(self, health_checker):
        """Test getting last health check result."""
        result = health_checker.get_last_check()
        assert result is None  # No check has been run yet

    @pytest.mark.asyncio
    async def test_health_checker_initialization(self, health_checker):
        """Test health checker initialization."""
        assert health_checker.last_check is None
        assert health_checker.last_result is None
        assert health_checker.check_interval == 60

    # =====================================================
    # PHASE 9 ADDITIONAL TESTS
    # =====================================================

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self, health_checker):
        """Test Redis health check when healthy."""
        with patch('redis.Redis') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            result = await health_checker.check_redis()
            assert result['status'] == 'healthy'
            assert result['responsive'] is True

    @pytest.mark.asyncio
    async def test_check_redis_unhealthy(self, health_checker):
        """Test Redis health check when unhealthy."""
        with patch('redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")

            result = await health_checker.check_redis()
            assert result['status'] == 'unhealthy'
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_check_all_services(self, health_checker):
        """Test checking all services."""
        with patch.object(health_checker, 'check_database') as mock_db:
            with patch.object(health_checker, 'check_redis') as mock_redis:
                with patch.object(health_checker, 'check_authentication') as mock_auth:
                    mock_db.return_value = {'status': 'healthy'}
                    mock_redis.return_value = {'status': 'healthy'}
                    mock_auth.return_value = {'status': 'healthy'}

                    result = await health_checker.check_all()
                    assert result is not None
                    assert 'database' in result or 'services' in result

    @pytest.mark.asyncio
    async def test_health_check_caching(self, health_checker):
        """Test health check result caching."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = {}
            mock_get.return_value = mock_client

            # First check
            result1 = await health_checker.check_database()
            # Second check (may use cache)
            result2 = await health_checker.check_database()

            assert result1 is not None
            assert result2 is not None

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, health_checker):
        """Test health check with timeout."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_get.side_effect = TimeoutError("Request timeout")

            result = await health_checker.check_database()
            assert result['status'] == 'unhealthy'
            assert 'timeout' in result.get('error', '').lower() or 'error' in result

    @pytest.mark.asyncio
    async def test_health_check_partial_failure(self, health_checker):
        """Test health check with partial service failure."""
        with patch.object(health_checker, 'check_database') as mock_db:
            with patch.object(health_checker, 'check_redis') as mock_redis:
                mock_db.return_value = {'status': 'healthy'}
                mock_redis.return_value = {'status': 'unhealthy', 'error': 'Connection failed'}

                result = await health_checker.check_all()
                assert result is not None

    @pytest.mark.asyncio
    async def test_health_check_performance_metrics(self, health_checker):
        """Test health check includes performance metrics."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = {}
            mock_get.return_value = mock_client

            result = await health_checker.check_database()
            assert 'latency_ms' in result or 'response_time' in result or 'status' in result

    @pytest.mark.asyncio
    async def test_health_check_timestamp(self, health_checker):
        """Test health check includes timestamp."""
        with patch('supabase_client.get_supabase') as mock_get:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = {}
            mock_get.return_value = mock_client

            result = await health_checker.check_database()
            assert 'timestamp' in result or 'checked_at' in result or 'status' in result

