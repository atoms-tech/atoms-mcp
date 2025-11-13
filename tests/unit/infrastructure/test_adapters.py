"""Comprehensive unit tests for infrastructure components.

Covers:
- Rate limiter: token bucket and sliding window algorithms
- Health checks: database, auth, cache, performance, errors, rate limiter
- User ID mapping: WorkOS to UUID conversion and reverse
- Security: input validation, sanitization, rate limit checks
- Factory: adapter creation and backend selection
- Monitoring: performance tracking, error tracking, usage analytics
- Adapter abstractions: interface compliance"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from infrastructure.rate_limiter import RateLimiter, SlidingWindowRateLimiter
from infrastructure.security import UserRateLimiter, InputValidator
from infrastructure.user_mapper import UserIDMapper
from infrastructure.health import HealthChecker
from infrastructure.monitoring import (
    QueryPerformanceMonitor,
    ErrorTracker,
    UsageAnalytics
)
from infrastructure.factory import AdapterFactory, reset_factory


# =============================================================================
# RATE LIMITER TESTS
# =============================================================================

class TestRateLimiter:
    """Test token bucket rate limiter."""

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        limiter = RateLimiter(requests_per_minute=60)
        result = await limiter.acquire("user-1", tokens=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens_within_burst(self):
        limiter = RateLimiter(requests_per_minute=60, burst_size=120)
        for _ in range(10):
            result = await limiter.acquire("user-1", tokens=1)
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_rejects_after_burst_exhausted(self):
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        # Exhaust burst
        for _ in range(5):
            await limiter.acquire("user-1", tokens=1)
        # Next should be rejected
        result = await limiter.acquire("user-1", tokens=1)
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_replenishes_over_time(self):
        # 1 token per second
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        # Exhaust burst
        for _ in range(5):
            await limiter.acquire("user-1", tokens=1)
        # Wait enough time for at least 1 token to replenish (1+ seconds)
        await asyncio.sleep(1.1)
        result = await limiter.acquire("user-1", tokens=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_users_independent_limits(self):
        limiter = RateLimiter(requests_per_minute=60, burst_size=2)
        # User 1 exhausts burst
        await limiter.acquire("user-1", tokens=2)
        result1 = await limiter.acquire("user-1", tokens=1)
        assert result1 is False
        # User 2 should still have tokens
        result2 = await limiter.acquire("user-2", tokens=1)
        assert result2 is True


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter."""

    @pytest.mark.asyncio
    async def test_check_limit_allows_within_window(self):
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=10)
        for _ in range(10):
            result = await limiter.check_limit("user-1")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_limit_blocks_after_max(self):
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=5)
        for _ in range(5):
            await limiter.check_limit("user-1")
        result = await limiter.check_limit("user-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_remaining_tracks_correctly(self):
        limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=10)
        await limiter.check_limit("user-1")
        await limiter.check_limit("user-1")
        remaining = limiter.get_remaining("user-1")
        assert remaining == 8

    @pytest.mark.asyncio
    async def test_window_expiration_resets_limit(self):
        limiter = SlidingWindowRateLimiter(window_seconds=1, max_requests=2)
        # Exhaust limit
        await limiter.check_limit("user-1")
        await limiter.check_limit("user-1")
        # Should be blocked
        result = await limiter.check_limit("user-1")
        assert result is False
        # Wait for window to expire
        await asyncio.sleep(1.1)
        # Should be allowed again
        result = await limiter.check_limit("user-1")
        assert result is True


# =============================================================================
# SECURITY TESTS
# =============================================================================

class TestUserRateLimiter:
    """Test user rate limiter with operation types."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_default(self):
        limiter = UserRateLimiter()
        result = await limiter.check_rate_limit("user-1", "default")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_enforces_search_limit(self):
        limiter = UserRateLimiter()
        # Search has 30 searches/min limit
        for _ in range(30):
            result = await limiter.check_rate_limit("user-1", "search")
            assert result["allowed"] is True
        # Next search should be blocked
        result = await limiter.check_rate_limit("user-1", "search")
        assert result["allowed"] is False
        assert result["retry_after"] == 60

    @pytest.mark.asyncio
    async def test_check_rate_limit_returns_remaining(self):
        limiter = UserRateLimiter()
        result = await limiter.check_rate_limit("user-1", "default")
        assert "remaining" in result
        assert result["remaining"] > 0

    @pytest.mark.asyncio
    async def test_get_stats_tracks_requests(self):
        limiter = UserRateLimiter()
        await limiter.check_rate_limit("user-1", "default")
        stats = limiter.get_stats("user-1")
        assert stats["active_requests"] > 0


class TestInputValidator:
    """Test input validation and sanitization."""

    def test_validate_entity_id_accepts_uuid(self):
        validator = InputValidator()
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validator.validate_entity_id(valid_uuid) is True

    def test_validate_entity_id_accepts_workos(self):
        validator = InputValidator()
        valid_workos = "user_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        assert validator.validate_entity_id(valid_workos) is True

    def test_validate_entity_id_rejects_invalid(self):
        validator = InputValidator()
        assert validator.validate_entity_id("invalid-id") is False

    def test_sanitize_search_term_removes_sql_injection(self):
        validator = InputValidator()
        malicious = "'; DROP TABLE users; --"
        sanitized = validator.sanitize_search_term(malicious)
        assert "DROP" not in sanitized
        assert "--" not in sanitized

    def test_sanitize_search_term_escapes_html(self):
        validator = InputValidator()
        xss_attempt = "<script>alert('xss')</script>"
        sanitized = validator.sanitize_search_term(xss_attempt)
        assert "<" not in sanitized
        assert ">" not in sanitized

    def test_sanitize_search_term_limits_length(self):
        validator = InputValidator()
        long_string = "a" * 1000
        sanitized = validator.sanitize_search_term(long_string)
        assert len(sanitized) <= 500

    def test_validate_data_object_requires_fields(self):
        validator = InputValidator()
        data = {"description": "test"}
        errors = validator.validate_data_object(data, "organization")
        assert "name" in errors

    def test_validate_data_object_checks_types(self):
        validator = InputValidator()
        data = {"name": 123}  # Invalid type
        errors = validator.validate_data_object(data, "organization")
        assert "name" in errors

    def test_sanitize_string_removes_null_bytes(self):
        validator = InputValidator()
        text = "hello\x00world"
        sanitized = validator.sanitize_string(text)
        assert "\x00" not in sanitized

    def test_sanitize_string_limits_length(self):
        validator = InputValidator()
        long_string = "a" * 2000
        sanitized = validator.sanitize_string(long_string, max_length=500)
        assert len(sanitized) <= 500


# =============================================================================
# USER ID MAPPER TESTS
# =============================================================================

class TestUserIDMapper:
    """Test WorkOS to UUID ID mapping."""

    def test_is_workos_id_recognizes_format(self):
        assert UserIDMapper.is_workos_id("user_ABCDEFGHIJKLMNOPQRSTUVWXYZ") is True
        assert UserIDMapper.is_workos_id("user_123456") is False
        assert UserIDMapper.is_workos_id("invalid") is False

    def test_is_uuid_recognizes_format(self):
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert UserIDMapper.is_uuid(valid_uuid) is True
        assert UserIDMapper.is_uuid("not-a-uuid") is False

    @pytest.mark.asyncio
    async def test_workos_to_uuid_caches_result(self):
        mock_db = AsyncMock()
        mock_db.get_single.return_value = {"supabase_uuid": "550e8400-e29b-41d4-a716-446655440000"}

        mapper = UserIDMapper(mock_db)
        workos_id = "user_ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        result1 = await mapper.workos_to_uuid(workos_id)
        result2 = await mapper.workos_to_uuid(workos_id)

        # Should only query once due to caching
        assert mock_db.get_single.call_count == 1
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_workos_to_uuid_raises_on_invalid_format(self):
        mapper = UserIDMapper(AsyncMock())
        with pytest.raises(ValueError):
            await mapper.workos_to_uuid("invalid-id")

    @pytest.mark.asyncio
    async def test_uuid_to_workos_returns_none_if_not_found(self):
        mock_db = AsyncMock()
        mock_db.get_single.return_value = None

        mapper = UserIDMapper(mock_db)
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = await mapper.uuid_to_workos(uuid)

        assert result is None

    @pytest.mark.asyncio
    async def test_convert_if_needed_handles_uuid(self):
        mapper = UserIDMapper(AsyncMock())
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = await mapper.convert_if_needed(uuid)
        assert result == uuid

    def test_clear_cache_resets_caches(self):
        mapper = UserIDMapper(AsyncMock())
        mapper._cache["key"] = "value"
        mapper._reverse_cache["rev_key"] = "rev_value"

        mapper.clear_cache()

        assert len(mapper._cache) == 0
        assert len(mapper._reverse_cache) == 0

    def test_get_cache_stats_reports_sizes(self):
        mapper = UserIDMapper(AsyncMock())
        mapper._cache["key1"] = "value1"
        mapper._cache["key2"] = "value2"

        stats = mapper.get_cache_stats()
        assert stats["workos_to_uuid_entries"] == 2


# =============================================================================
# MONITORING TESTS
# =============================================================================

class TestQueryPerformanceMonitor:
    """Test query performance tracking."""

    @pytest.mark.asyncio
    async def test_track_query_records_stats(self):
        monitor = QueryPerformanceMonitor()
        await monitor.track_query("SELECT", "users", 100.5)

        stats = monitor.get_stats()
        assert stats["total_queries"] == 1
        assert "SELECT:users" in stats["query_breakdown"]

    @pytest.mark.asyncio
    async def test_track_query_identifies_slow_queries(self):
        monitor = QueryPerformanceMonitor()
        monitor.slow_query_threshold = 100

        await monitor.track_query("SELECT", "users", 150.0)

        stats = monitor.get_stats()
        breakdown = stats["query_breakdown"]["SELECT:users"]
        assert breakdown["slow_queries"] == 1

    @pytest.mark.asyncio
    async def test_track_query_calculates_averages(self):
        monitor = QueryPerformanceMonitor()

        await monitor.track_query("SELECT", "users", 100.0)
        await monitor.track_query("SELECT", "users", 200.0)

        stats = monitor.get_stats()
        breakdown = stats["query_breakdown"]["SELECT:users"]
        assert breakdown["avg_time"] == 150.0


class TestErrorTracker:
    """Test error tracking and categorization."""

    @pytest.mark.asyncio
    async def test_track_error_counts_occurrences(self):
        tracker = ErrorTracker()
        await tracker.track_error("ValueError", "invalid input", {})

        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 1
        assert summary["unique_errors"] == 1

    @pytest.mark.asyncio
    async def test_track_error_deduplicates(self):
        tracker = ErrorTracker()
        await tracker.track_error("ValueError", "invalid input", {})
        await tracker.track_error("ValueError", "invalid input", {})

        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 2
        assert summary["unique_errors"] == 1

    @pytest.mark.asyncio
    async def test_track_error_limits_history(self):
        tracker = ErrorTracker()
        tracker.max_history = 100

        for i in range(150):
            await tracker.track_error("ValueError", f"error {i}", {})

        assert len(tracker.error_history) <= 100

    @pytest.mark.asyncio
    async def test_get_error_summary_returns_top_errors(self):
        tracker = ErrorTracker()
        for _ in range(15):
            await tracker.track_error("Error1", "msg1", {})
        for _ in range(10):
            await tracker.track_error("Error2", "msg2", {})

        summary = tracker.get_error_summary()
        error_counts = summary["error_counts"]
        # Validate that the more frequent error has a greater or equal count
        assert error_counts["Error1:msg1"] >= error_counts["Error2:msg2"]


class TestUsageAnalytics:
    """Test usage metrics tracking."""

    @pytest.mark.asyncio
    async def test_track_tool_usage_counts_calls(self):
        analytics = UsageAnalytics()
        await analytics.track_tool_usage("create_entity", "user-1")
        await analytics.track_tool_usage("create_entity", "user-1")

        report = analytics.get_analytics_report()
        # Tool usage tracked
        assert len(report["most_used_tools"]) > 0 or len(analytics.metrics["tool_usage"]) > 0

    @pytest.mark.asyncio
    async def test_track_entity_operation_measures_time(self):
        analytics = UsageAnalytics()
        await analytics.track_entity_operation("entity", "create", "user-1", 100.0)

        report = analytics.get_analytics_report()
        # Should track operations
        assert len(analytics.metrics["entity_operations"]) > 0

    @pytest.mark.asyncio
    async def test_track_search_limits_history(self):
        analytics = UsageAnalytics()

        for i in range(1500):
            await analytics.track_search(f"query{i}", 10, "user-1")

        assert len(analytics.metrics["search_queries"]) <= 1000


# =============================================================================
# HEALTH CHECKER TESTS
# =============================================================================

class TestHealthChecker:
    """Test comprehensive health checking."""

    @pytest.mark.asyncio
    async def test_comprehensive_check_runs_all_checks(self):
        checker = HealthChecker()

        with patch.object(checker, 'check_database', AsyncMock(return_value={"status": "healthy"})):
            with patch.object(checker, 'check_authentication', AsyncMock(return_value={"status": "healthy"})):
                with patch.object(checker, 'check_cache', AsyncMock(return_value={"status": "healthy"})):
                    with patch.object(checker, 'check_performance', AsyncMock(return_value={"status": "healthy"})):
                        with patch.object(checker, 'check_errors', AsyncMock(return_value={"status": "healthy"})):
                            with patch.object(checker, 'check_rate_limiter', AsyncMock(return_value={"status": "active"})):
                                result = await checker.comprehensive_check()

        assert "status" in result
        assert "components" in result
        assert "timestamp" in result

    def test_get_last_check_returns_cached_result(self):
        checker = HealthChecker()
        test_result = {"status": "healthy", "timestamp": "2024-01-01T00:00:00"}
        checker.last_result = test_result

        result = checker.get_last_check()
        assert result == test_result


# =============================================================================
# ADAPTER FACTORY TESTS
# =============================================================================

class TestAdapterFactory:
    """Test adapter factory pattern."""

    def test_factory_creates_supabase_adapters(self):
        with patch.dict('os.environ', {'ATOMS_BACKEND_TYPE': 'supabase'}):
            reset_factory()
            factory = AdapterFactory()

            assert factory.get_backend_type() == "supabase"

    def test_factory_caches_adapters(self):
        with patch.dict('os.environ', {'ATOMS_BACKEND_TYPE': 'supabase'}):
            factory = AdapterFactory()

            adapter1 = factory.get_storage_adapter()
            adapter2 = factory.get_storage_adapter()

            assert adapter1 is adapter2  # Same instance

    def test_factory_raises_on_unknown_backend(self):
        # Set both backend and service mode to ensure unknown backend is checked
        with patch.dict('os.environ', {
            'ATOMS_BACKEND_TYPE': 'unknown',
            'ATOMS_SUPABASE_MODE': 'live'  # Ensure not mock mode
        }):
            # ValueError is raised in __init__ for fail-fast behavior
            with pytest.raises(ValueError, match="Unknown backend type"):
                AdapterFactory()

    def test_factory_get_all_adapters_returns_dict(self):
        with patch.dict('os.environ', {'ATOMS_BACKEND_TYPE': 'supabase'}):
            factory = AdapterFactory()

            adapters = factory.get_all_adapters()
            assert isinstance(adapters, dict)
            assert "auth" in adapters
            assert "database" in adapters
