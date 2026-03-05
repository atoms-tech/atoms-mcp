"""
Atoms MCP Observability Module

Production-ready observability infrastructure including:
- Structured logging with correlation IDs
- Prometheus-compatible metrics collection
- Multi-layer health monitoring
- Request tracking middleware
- Performance measurement decorators
- Webhook notifications for alerts
- FastAPI endpoints for monitoring

Author: Atoms MCP Platform
Version: 1.0.0
"""

# Logging exports
# Decorator exports
from .decorators import (
    log_operation,
    measure_performance,
    observe_tool,
    track_database_operation,
)

# Endpoint exports removed - endpoints module moved to archive/unused_modules
# Health monitoring exports
from .health import (
    AuthKitHealthCheck,
    ComponentType,
    CustomHealthCheck,
    HealthCheck,
    HealthCheckResult,
    HealthMonitor,
    HealthStatus,
    PerformanceMonitor,
    SupabaseHealthCheck,
    SystemHealth,
    check_health,
    health_monitor,
    register_health_check,
)
from .logging import (
    AtomLogger,
    LogContext,
    LogLevel,
    PerformanceMetric,
    StructuredFormatter,
    clear_context,
    default_logger,
    get_correlation_id,
    get_logger,
    set_correlation_id,
    set_request_path,
    set_user_context,
)

# Metrics exports
from .metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricType,
    active_connections,
    cache_hit_ratio,
    cache_operations_total,
    database_queries_total,
    database_query_duration_seconds,
    errors_total,
    get_metrics_snapshot,
    get_prometheus_metrics,
    http_request_duration_seconds,
    http_requests_total,
    record_database_query,
    record_error,
    record_http_request,
    record_tool_execution,
    registry,
    tool_execution_duration_seconds,
    tool_executions_total,
)

# Middleware exports
from .middleware import (
    ContextPropagationMiddleware,
    ErrorTrackingMiddleware,
    PerformanceTrackingMiddleware,
    RequestTrackingMiddleware,
    get_propagated_headers,
)

# Webhook exports
from .webhooks import (
    AlertSeverity,
    WebhookClient,
    WebhookConfig,
    WebhookEventType,
    WebhookManager,
    WebhookPayload,
    configure_custom_webhook,
    configure_vercel_webhook,
    webhook_manager,
)

__all__ = [
    # Webhooks
    "AlertSeverity",
    # Logging
    "AtomLogger",
    # Health
    "AuthKitHealthCheck",
    "ComponentType",
    # Middleware
    "ContextPropagationMiddleware",
    # Metrics
    "Counter",
    "CustomHealthCheck",
    "ErrorTrackingMiddleware",
    "Gauge",
    "HealthCheck",
    "HealthCheckResult",
    "HealthMonitor",
    "HealthStatus",
    "Histogram",
    "LogContext",
    "LogLevel",
    "MetricType",
    "PerformanceMetric",
    "PerformanceMonitor",
    "PerformanceTrackingMiddleware",
    "RequestTrackingMiddleware",
    "StructuredFormatter",
    "SupabaseHealthCheck",
    "SystemHealth",
    "WebhookClient",
    "WebhookConfig",
    "WebhookEventType",
    "WebhookManager",
    "WebhookPayload",
    "active_connections",
    "cache_hit_ratio",
    "cache_operations_total",
    "check_health",
    "clear_context",
    "configure_custom_webhook",
    "configure_vercel_webhook",
    "database_queries_total",
    "database_query_duration_seconds",
    "default_logger",
    "errors_total",
    "get_correlation_id",
    # Endpoints removed - endpoints module moved to archive/unused_modules
    "get_logger",
    "get_metrics_snapshot",
    "get_prometheus_metrics",
    "get_propagated_headers",
    "health_monitor",
    "http_request_duration_seconds",
    "http_requests_total",
    # Decorators
    "log_operation",
    "measure_performance",
    "observe_tool",
    "record_database_query",
    "record_error",
    "record_http_request",
    "record_tool_execution",
    "register_health_check",
    "registry",
    "set_correlation_id",
    "set_request_path",
    "set_user_context",
    "tool_execution_duration_seconds",
    "tool_executions_total",
    "track_database_operation",
    "webhook_manager",
]

__version__ = "1.0.0"
