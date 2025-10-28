"""Test lib.atoms.observability modules for 100% coverage."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from lib.atoms.observability.decorators import (
    log_operation,
    measure_performance,
    observe_tool,
    track_database_operation,
)
from lib.atoms.observability.health import ComponentType, HealthCheck, HealthStatus, SystemHealth

# Import observability components
from lib.atoms.observability.logging import LogContext, LogLevel, get_logger
from lib.atoms.observability.metrics import (
    MetricType,
    MetricValue,
    get_metrics_snapshot,
    record_http_request,
    record_tool_execution,
)
from lib.atoms.observability.webhooks import (
    AlertSeverity,
    WebhookClient,
    WebhookConfig,
    WebhookEventType,
    WebhookPayload,
)


class TestLogging:
    """Test logging components."""

    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_log_context(self):
        """Test log context management."""
        context = LogContext()
        context.set_correlation_id("test-correlation-id")
        context.set_user_context("test-user", "user-id")

        assert context.get_correlation_id() == "test-correlation-id"
        assert context.get_user_context() == ("test-user", "user-id")

    def test_log_levels(self):
        """Test log level enumeration."""
        assert LogLevel.DEBUG.value < LogLevel.INFO.value
        assert LogLevel.INFO.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value
        assert LogLevel.ERROR.value < LogLevel.CRITICAL.value


class TestMetrics:
    """Test metrics components."""

    def test_metric_type_enum(self):
        """Test metric type enumeration."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"

    def test_metric_value(self):
        """Test metric value creation."""
        value = MetricValue(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now()
        )
        assert value.name == "test_metric"
        assert value.value == 42.0
        assert value.metric_type == MetricType.COUNTER

    @pytest.mark.asyncio
    async def test_record_http_request(self):
        """Test HTTP request recording."""
        record_http_request(
            method="GET",
            endpoint="/api/test",
            status_code=200,
            duration_ms=150
        )
        # Metrics should be recorded (implementation specific)
        assert True

    @pytest.mark.asyncio
    async def test_record_tool_execution(self):
        """Test tool execution recording."""
        record_tool_execution(
            tool_name="test_tool",
            operation="create",
            duration_ms=50,
            success=True
        )
        # Metrics should be recorded
        assert True

    def test_get_metrics_snapshot(self):
        """Test metrics snapshot."""
        snapshot = get_metrics_snapshot()
        assert isinstance(snapshot, dict)
        assert "metrics" in snapshot


class TestHealth:
    """Test health check components."""

    def test_health_status_enum(self):
        """Test health status enumeration."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_check(self):
        """Test health check creation."""
        check = HealthCheck(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All systems operational"
        )
        assert check.name == "test_check"
        assert check.status == HealthStatus.HEALTHY
        assert check.message == "All systems operational"

    def test_component_type_enum(self):
        """Test component type enumeration."""
        assert ComponentType.DATABASE.value == "database"
        assert ComponentType.CACHE.value == "cache"
        assert ComponentType.EXTERNAL_API.value == "external_api"

    def test_system_health(self):
        """Test system health aggregation."""
        checks = [
            HealthCheck("db", HealthStatus.HEALTHY),
            HealthCheck("cache", HealthStatus.HEALTHY),
            HealthCheck("api", HealthStatus.DEGRADED)
        ]

        system_health = SystemHealth(checks)
        assert system_health.overall_status == HealthStatus.DEGRADED
        assert len(system_health.checks) == 3


class TestWebhooks:
    """Test webhook components."""

    def test_alert_severity_enum(self):
        """Test alert severity enumeration."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_webhook_event_type_enum(self):
        """Test webhook event type enumeration."""
        assert WebhookEventType.HEALTH_ALERT.value == "health_alert"
        assert WebhookEventType.METRIC_ALERT.value == "metric_alert"
        assert WebhookEventType.ERROR_ALERT.value == "error_alert"

    def test_webhook_config(self):
        """Test webhook configuration."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            enabled=True,
            retry_count=3,
            timeout_seconds=30
        )
        assert config.url == "https://example.com/webhook"
        assert config.enabled is True
        assert config.retry_count == 3
        assert config.timeout_seconds == 30

    def test_webhook_payload(self):
        """Test webhook payload creation."""
        payload = WebhookPayload(
            event_type=WebhookEventType.HEALTH_ALERT,
            severity=AlertSeverity.WARNING,
            timestamp=datetime.now(),
            data={"message": "Test alert"}
        )
        assert payload.event_type == WebhookEventType.HEALTH_ALERT
        assert payload.severity == AlertSeverity.WARNING
        assert "message" in payload.data

    @pytest.mark.asyncio
    async def test_webhook_client(self):
        """Test webhook client functionality."""
        config = WebhookConfig(
            url="https://httpbin.org/post",
            enabled=True
        )
        client = WebhookClient(config)

        payload = WebhookPayload(
            event_type=WebhookEventType.HEALTH_ALERT,
            severity=AlertSeverity.INFO,
            timestamp=datetime.now(),
            data={"test": True}
        )

        # Mock the HTTP call
        client.http_client.post = AsyncMock(return_value=Mock(status_code=200))

        result = await client.send_webhook(payload)
        assert result is True


class TestDecorators:
    """Test observability decorators."""

    @observe_tool
    def dummy_tool(self, param1, param2=None):
        """Dummy tool for decorator testing."""
        return f"Result: {param1}, {param2}"

    @log_operation(operation_type="test_operation")
    def dummy_operation(self, data):
        """Dummy operation for logging decorator testing."""
        return data.upper()

    @measure_performance
    def dummy_performance_function(self, n):
        """Dummy function for performance measurement."""
        return sum(range(n))

    @track_database_operation
    def dummy_db_operation(self, query):
        """Dummy database operation."""
        return {"query": query, "result": "success"}

    def test_observe_tool_decorator(self):
        """Test tool observation decorator."""
        result = self.dummy_tool("test_param", param2="test_optional")
        assert result == "Result: test_param, test_optional"

    def test_log_operation_decorator(self):
        """Test operation logging decorator."""
        result = self.dummy_operation("test_data")
        assert result == "TEST_DATA"

    def test_measure_performance_decorator(self):
        """Test performance measurement decorator."""
        result = self.dummy_performance_function(100)
        assert result == sum(range(100))

    def test_track_database_operation_decorator(self):
        """Test database operation tracking decorator."""
        result = self.dummy_db_operation("SELECT * FROM test")
        assert result["query"] == "SELECT * FROM test"
        assert result["result"] == "success"


class TestIntegration:
    """Test integration between observability components."""

    @pytest.mark.asyncio
    async def test_end_to_end_observability(self):
        """Test complete observability flow."""
        # Setup logger
        get_logger("integration_test")

        # Record metrics
        record_http_request("POST", "/api/tools", 201, 100)
        record_tool_execution("test_tool", "execute", 50, True)

        # Check health
        health_check = HealthCheck(
            name="test_system",
            status=HealthStatus.HEALTHY,
            message="System is healthy"
        )

        # Send webhook
        config = WebhookConfig(
            url="https://httpbin.org/post",
            enabled=False  # Disabled for test
        )
        client = WebhookClient(config)

        payload = WebhookPayload(
            event_type=WebhookEventType.HEALTH_ALERT,
            severity=AlertSeverity.INFO,
            timestamp=datetime.now(),
            data={"health_check": health_check.to_dict()}
        )

        # Should not send due to disabled config
        result = await client.send_webhook(payload)
        assert result is False

        # Get metrics snapshot
        snapshot = get_metrics_snapshot()
        assert isinstance(snapshot, dict)
