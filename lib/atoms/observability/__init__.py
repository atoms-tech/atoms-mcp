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

# Endpoint exports
from .endpoints import (
    get_dashboard,
    get_health,
    get_metrics,
    router,
)

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
    # Logging
    "AtomLogger",
    "LogContext",
    "LogLevel",
    "PerformanceMetric",
    "StructuredFormatter",
    "clear_context",
    "default_logger",
    "get_correlation_id",
    "get_logger",
    "set_correlation_id",
    "set_request_path",
    "set_user_context",
    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "MetricType",
    "active_connections",
    "cache_hit_ratio",
    "cache_operations_total",
    "database_queries_total",
    "database_query_duration_seconds",
    "errors_total",
    "get_metrics_snapshot",
    "get_prometheus_metrics",
    "http_request_duration_seconds",
    "http_requests_total",
    "record_database_query",
    "record_error",
    "record_http_request",
    "record_tool_execution",
    "registry",
    "tool_execution_duration_seconds",
    "tool_executions_total",
    # Health
    "AuthKitHealthCheck",
    "ComponentType",
    "CustomHealthCheck",
    "HealthCheck",
    "HealthCheckResult",
    "HealthMonitor",
    "HealthStatus",
    "PerformanceMonitor",
    "SupabaseHealthCheck",
    "SystemHealth",
    "check_health",
    "health_monitor",
    "register_health_check",
    # Middleware
    "ContextPropagationMiddleware",
    "ErrorTrackingMiddleware",
    "PerformanceTrackingMiddleware",
    "RequestTrackingMiddleware",
    "get_propagated_headers",
    # Decorators
    "log_operation",
    "measure_performance",
    "observe_tool",
    "track_database_operation",
    # Webhooks
    "AlertSeverity",
    "WebhookClient",
    "WebhookConfig",
    "WebhookEventType",
    "WebhookManager",
    "WebhookPayload",
    "configure_custom_webhook",
    "configure_vercel_webhook",
    "webhook_manager",
    # Endpoints
    "get_dashboard",
    "get_health",
    "get_metrics",
    "router",
]

__version__ = "1.0.0"
