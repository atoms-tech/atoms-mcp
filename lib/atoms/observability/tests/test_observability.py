"""
Comprehensive tests for Atoms MCP Observability module.

Tests all major components:
- Logging with context
- Metrics collection
- Health checks
- Middleware
- Decorators
- Webhooks

Author: Atoms MCP Platform
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lib.atoms.observability import (
    # Logging
    get_logger,
    LogContext,
    set_correlation_id,
    get_correlation_id,
    PerformanceMetric,
    # Metrics
    Counter,
    Gauge,
    Histogram,
    registry,
    record_http_request,
    record_tool_execution,
    get_prometheus_metrics,
    # Health
    HealthCheck,
    HealthStatus,
    ComponentType,
    CustomHealthCheck,
    health_monitor,
    # Decorators
    observe_tool,
    log_operation,
    measure_performance,
    # Webhooks
    WebhookPayload,
    WebhookConfig,
    WebhookClient,
    WebhookEventType,
    AlertSeverity,
)


# ============================================================================
# Logging Tests
# ============================================================================

class TestLogging:
    """Test logging functionality."""

    def test_logger_creation(self):
        """Test logger creation."""
        logger = get_logger("test_logger")
        assert logger.name == "test_logger"

    def test_correlation_id_context(self):
        """Test correlation ID context management."""
        test_id = "test-correlation-123"

        with LogContext(correlation_id=test_id):
            assert get_correlation_id() == test_id

        # Context should be cleared after exiting
        assert get_correlation_id() is None

    def test_auto_correlation_id(self):
        """Test automatic correlation ID generation."""
        with LogContext() as ctx:
            correlation_id = get_correlation_id()
            assert correlation_id is not None
            assert len(correlation_id) > 0

    def test_performance_metric(self):
        """Test performance metric tracking."""
        metric = PerformanceMetric("test_operation")
        metric.add_metadata("key", "value")

        # Simulate some work
        import time
        time.sleep(0.01)

        duration = metric.stop()

        assert duration > 0
        assert metric.duration_ms is not None
        assert metric.metadata["key"] == "value"

        metric_dict = metric.to_dict()
        assert "operation" in metric_dict
        assert "duration_ms" in metric_dict


# ============================================================================
# Metrics Tests
# ============================================================================

class TestMetrics:
    """Test metrics functionality."""

    def test_counter_increment(self):
        """Test counter increment."""
        counter = Counter("test_counter", "Test counter")

        counter.inc()
        assert counter.get() == 1.0

        counter.inc(amount=5.0)
        assert counter.get() == 6.0

    def test_counter_with_labels(self):
        """Test counter with labels."""
        counter = Counter("test_counter_labels", "Test counter", labels=["status"])

        counter.inc(labels={"status": "success"})
        counter.inc(labels={"status": "success"})
        counter.inc(labels={"status": "error"})

        assert counter.get(labels={"status": "success"}) == 2.0
        assert counter.get(labels={"status": "error"}) == 1.0

    def test_gauge_operations(self):
        """Test gauge operations."""
        gauge = Gauge("test_gauge", "Test gauge")

        gauge.set(10.0)
        assert gauge.get() == 10.0

        gauge.inc(5.0)
        assert gauge.get() == 15.0

        gauge.dec(3.0)
        assert gauge.get() == 12.0

    def test_histogram_observations(self):
        """Test histogram observations."""
        histogram = Histogram(
            "test_histogram",
            "Test histogram",
            buckets=[0.1, 0.5, 1.0, 5.0]
        )

        histogram.observe(0.05)
        histogram.observe(0.3)
        histogram.observe(0.8)
        histogram.observe(2.0)

        assert histogram.get_count() == 4
        assert histogram.get_sum() > 0

        buckets = histogram.get_buckets()
        assert len(buckets) == 4

    def test_histogram_context_manager(self):
        """Test histogram timing context manager."""
        histogram = Histogram("test_timing", "Test timing")

        with histogram.time():
            import time
            time.sleep(0.01)

        assert histogram.get_count() == 1
        assert histogram.get_sum() > 0

    def test_prometheus_format(self):
        """Test Prometheus format export."""
        # Register some metrics
        test_counter = registry.register_counter("test_export", "Test export")
        test_counter.inc()

        prometheus_text = get_prometheus_metrics()

        assert "# HELP test_export" in prometheus_text
        assert "# TYPE test_export counter" in prometheus_text

    def test_record_http_request(self):
        """Test HTTP request recording."""
        record_http_request("GET", "/api/test", 200, 0.5)

        # Verify metric was recorded
        prometheus_text = get_prometheus_metrics()
        assert "http_requests_total" in prometheus_text

    def test_record_tool_execution(self):
        """Test tool execution recording."""
        record_tool_execution("test_tool", 1.5, success=True)

        # Verify metric was recorded
        prometheus_text = get_prometheus_metrics()
        assert "tool_executions_total" in prometheus_text


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthChecks:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_custom_health_check_success(self):
        """Test custom health check that succeeds."""
        def check_func():
            return True

        check = CustomHealthCheck(
            name="test_check",
            component_type=ComponentType.INTERNAL_SERVICE,
            check_func=check_func,
            timeout_seconds=1.0
        )

        result = await check.check()

        assert result.status == HealthStatus.HEALTHY
        assert result.component_name == "test_check"

    @pytest.mark.asyncio
    async def test_custom_health_check_failure(self):
        """Test custom health check that fails."""
        def check_func():
            return False

        check = CustomHealthCheck(
            name="test_check_fail",
            component_type=ComponentType.INTERNAL_SERVICE,
            check_func=check_func
        )

        result = await check.check()

        assert result.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_custom_health_check_timeout(self):
        """Test health check timeout."""
        async def slow_check():
            await asyncio.sleep(5.0)
            return True

        check = CustomHealthCheck(
            name="slow_check",
            component_type=ComponentType.INTERNAL_SERVICE,
            check_func=slow_check,
            timeout_seconds=0.1
        )

        result = await check.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert "timed out" in result.message.lower()

    @pytest.mark.asyncio
    async def test_custom_health_check_exception(self):
        """Test health check that raises exception."""
        def failing_check():
            raise Exception("Check failed")

        check = CustomHealthCheck(
            name="exception_check",
            component_type=ComponentType.INTERNAL_SERVICE,
            check_func=failing_check
        )

        result = await check.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert "error" in result.message.lower()


# ============================================================================
# Decorator Tests
# ============================================================================

class TestDecorators:
    """Test observability decorators."""

    @pytest.mark.asyncio
    async def test_observe_tool_decorator(self):
        """Test @observe_tool decorator."""
        @observe_tool("test_tool", track_performance=True)
        async def test_function(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2

        result = await test_function(5)

        assert result == 10

        # Verify metrics were recorded
        prometheus_text = get_prometheus_metrics()
        assert "tool_executions_total" in prometheus_text

    @pytest.mark.asyncio
    async def test_observe_tool_error_handling(self):
        """Test @observe_tool error handling."""
        @observe_tool("failing_tool", track_performance=True)
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()

        # Verify error was recorded
        prometheus_text = get_prometheus_metrics()
        assert "errors_total" in prometheus_text

    @pytest.mark.asyncio
    async def test_log_operation_decorator(self):
        """Test @log_operation decorator."""
        @log_operation("test_operation")
        async def test_operation(x: int) -> int:
            return x + 1

        result = await test_operation(10)
        assert result == 11

    @pytest.mark.asyncio
    async def test_measure_performance_decorator(self):
        """Test @measure_performance decorator."""
        @measure_performance("test_perf", threshold_warning_ms=10)
        async def fast_function():
            await asyncio.sleep(0.001)
            return "done"

        result = await fast_function()
        assert result == "done"

    def test_sync_function_with_observe_tool(self):
        """Test @observe_tool with synchronous function."""
        @observe_tool("sync_tool")
        def sync_function(x: int) -> int:
            return x * 3

        result = sync_function(4)
        assert result == 12


# ============================================================================
# Webhook Tests
# ============================================================================

class TestWebhooks:
    """Test webhook functionality."""

    def test_webhook_payload_creation(self):
        """Test webhook payload creation."""
        payload = WebhookPayload(
            event_type=WebhookEventType.ERROR_OCCURRED,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            metadata={"error_code": 500}
        )

        payload_dict = payload.to_dict()

        assert payload_dict["event_type"] == "error.occurred"
        assert payload_dict["severity"] == "error"
        assert payload_dict["title"] == "Test Error"
        assert payload_dict["metadata"]["error_code"] == 500

    def test_webhook_config_event_filtering(self):
        """Test webhook event type filtering."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            name="test_webhook",
            event_types=[
                WebhookEventType.ERROR_OCCURRED,
                WebhookEventType.WARNING_OCCURRED
            ]
        )

        assert config.should_send_event(WebhookEventType.ERROR_OCCURRED)
        assert not config.should_send_event(WebhookEventType.DEPLOYMENT_STARTED)

    def test_webhook_config_all_events(self):
        """Test webhook with all events enabled."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            name="all_events",
            event_types=[]  # Empty = all events
        )

        assert config.should_send_event(WebhookEventType.ERROR_OCCURRED)
        assert config.should_send_event(WebhookEventType.DEPLOYMENT_STARTED)

    @pytest.mark.asyncio
    async def test_webhook_client_send(self):
        """Test webhook client sending."""
        config = WebhookConfig(
            url="https://httpbin.org/post",
            name="test_webhook",
            retry_attempts=1,
            timeout_seconds=5.0
        )

        client = WebhookClient(config)

        payload = WebhookPayload(
            event_type=WebhookEventType.CUSTOM_EVENT,
            severity=AlertSeverity.INFO,
            title="Test Event",
            message="Test message"
        )

        # This will actually send to httpbin.org (public test endpoint)
        # In production tests, you'd mock this
        result = await client.send(payload)

        # httpbin.org should accept the request
        assert result is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.mark.asyncio
    async def test_full_request_flow(self):
        """Test full request flow with all observability components."""
        correlation_id = "test-integration-123"

        with LogContext(correlation_id=correlation_id, user_id="user-456"):
            # Verify context is set
            assert get_correlation_id() == correlation_id

            # Record HTTP request
            record_http_request("POST", "/api/test", 201, 0.5)

            # Execute monitored tool
            @observe_tool("integration_tool")
            async def integration_tool():
                return {"status": "success"}

            result = await integration_tool()
            assert result["status"] == "success"

            # Check metrics were recorded
            prometheus_text = get_prometheus_metrics()
            assert "http_requests_total" in prometheus_text
            assert "tool_executions_total" in prometheus_text


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
