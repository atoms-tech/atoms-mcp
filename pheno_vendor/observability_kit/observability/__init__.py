"""
Observability-Kit: Production-Grade Observability SDK

Unified logging, metrics, and distributed tracing for Python applications.
Based on 2025 best practices with support for Prometheus, OpenTelemetry,
Grafana, and Loki.

The Three Pillars of Observability:

1. Structured Logging
   - JSON structured output for log aggregation
   - Correlation ID injection and tracking
   - Context management for request tracing
   - Integration with Grafana Loki

2. Metrics Collection
   - Prometheus-compatible metrics (Counter, Gauge, Histogram)
   - Thread-safe in-memory aggregation
   - Multi-dimensional labels/tags
   - HTTP /metrics endpoint for scraping

3. Distributed Tracing
   - W3C Trace Context standard
   - Parent-child span relationships
   - Context propagation across services
   - OpenTelemetry export support

Quick Start:

    from observability import (
        StructuredLogger,
        MetricsCollector,
        DistributedTracer,
        trace_function,
        PrometheusExporter,
    )

    # Logging
    logger = StructuredLogger("my-app", service_name="api", environment="prod")
    logger.info("Application started", version="1.0.0")

    # Metrics
    metrics = MetricsCollector()
    requests = metrics.counter("http_requests_total", "Total requests", labels=["method"])
    requests.inc({"method": "GET"})

    # Tracing
    tracer = DistributedTracer("my-service")
    with tracer.start_span("process_request") as span:
        span.set_attribute("user_id", "123")

    # Export to Prometheus
    exporter = PrometheusExporter(metrics)
    metrics_text = exporter.export()
"""

__version__ = "0.1.0"

# Core components
from observability.logging.structured import (
    StructuredLogger,
    LogLevel,
    LogContext,
    TimingContext,
    generate_correlation_id,
    set_global_correlation_id,
)
from observability.metrics.collector import (
    MetricsCollector,
    Counter,
    Gauge,
    Histogram,
)
from observability.tracing.tracer import (
    DistributedTracer,
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
)
from observability.tracing.decorators import (
    trace_function,
    trace_async,
    set_default_tracer,
    get_default_tracer,
)
from observability.exporters.prometheus import PrometheusExporter
from observability.health import (
    HealthStatus,
    HealthCheckResult,
    SystemHealthReport,
    HealthMonitor,
    get_health_monitor,
)
from observability.rate_limiting import (
    RateLimiterBase,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
)
from observability.dashboards import (
    MetricType,
    Metric,
    MetricAggregator,
    DashboardDataCollector,
    DashboardFormatter,
    get_dashboard_collector,
    format_dashboard_data,
)
from observability.alerting import (
    AlertSeverity,
    Alert,
    AlertState,
    AlertManager,
    get_alert_manager,
    AlertRule,
    ThresholdCondition,
    RateCondition,
    ComponentHealthCondition,
)

__all__ = [
    # Logging
    "StructuredLogger",
    "LogLevel",
    "LogContext",
    "TimingContext",
    "generate_correlation_id",
    "set_global_correlation_id",
    # Metrics
    "MetricsCollector",
    "Counter",
    "Gauge",
    "Histogram",
    # Tracing
    "DistributedTracer",
    "Span",
    "SpanContext",
    "SpanKind",
    "SpanStatus",
    "trace_function",
    "trace_async",
    "set_default_tracer",
    "get_default_tracer",
    # Exporters
    "PrometheusExporter",
    # Health
    "HealthStatus",
    "HealthCheckResult",
    "SystemHealthReport",
    "HealthMonitor",
    "get_health_monitor",
    # Rate Limiting
    "RateLimiterBase",
    "TokenBucketRateLimiter",
    "SlidingWindowRateLimiter",
    # Dashboards
    "MetricType",
    "Metric",
    "MetricAggregator",
    "DashboardDataCollector",
    "DashboardFormatter",
    "get_dashboard_collector",
    "format_dashboard_data",
    # Alerting
    "AlertSeverity",
    "Alert",
    "AlertState",
    "AlertManager",
    "get_alert_manager",
    "AlertRule",
    "ThresholdCondition",
    "RateCondition",
    "ComponentHealthCondition",
]
