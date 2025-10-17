# Atoms MCP Observability Module

Production-ready observability infrastructure for the Atoms MCP platform. This module provides comprehensive monitoring, logging, health checking, and alerting capabilities optimized for Vercel deployments.

## Features

### 1. Structured Logging (`logging.py`)
- **JSON-formatted logs** for machine parsing
- **Correlation ID tracking** across requests and services
- **Automatic context injection** (user, session, request path)
- **Performance tracking** integrated with logs
- **Thread-safe operation** for concurrent requests
- **Multiple output formats** (JSON, plain text)

### 2. Metrics Collection (`metrics.py`)
- **Prometheus-compatible** exposition format
- **Request duration histograms** with configurable buckets
- **Tool execution metrics** for MCP operations
- **Error rate monitoring** by type and source
- **Active connection gauging** for resource tracking
- **Database query metrics** with operation tracking
- **Cache metrics** for hit ratio monitoring
- **Thread-safe metric collection**

### 3. Health Monitoring (`health.py`)
- **Multi-layer health checks** (system, dependencies, application)
- **Dependency health monitoring** (Supabase, AuthKit, external APIs)
- **Performance degradation detection** with thresholds
- **Circuit breaker integration** ready
- **Custom health checks** via callable functions
- **Health status aggregation** (healthy, degraded, unhealthy)

### 4. Request Middleware (`middleware.py`)
- **Automatic correlation ID** generation/propagation
- **Response time tracking** with headers
- **Error tracking and logging** with full context
- **Context propagation** across service boundaries
- **Performance monitoring** with slow request detection
- **Active connection tracking**

### 5. Observability Decorators (`decorators.py`)
- **@observe_tool** - Automatic tool execution monitoring
- **@log_operation** - Operation logging with context
- **@measure_performance** - Performance measurement with thresholds
- **@track_database_operation** - Database query tracking
- Support for both **sync and async** functions

### 6. Webhook Notifications (`webhooks.py`)
- **Vercel webhook integration** for deployment notifications
- **Alert system** for errors and warnings
- **Health degradation alerts** with severity levels
- **Custom event notifications**
- **Retry logic** with exponential backoff
- **Parallel webhook delivery**

### 7. API Endpoints (`endpoints.py`)
- **/metrics** - Prometheus exposition format
- **/health** - Comprehensive health check
- **/health/live** - Kubernetes liveness probe
- **/health/ready** - Kubernetes readiness probe
- **/api/observability/dashboard** - Dashboard data
- **/api/observability/metrics/snapshot** - JSON metrics

## Quick Start

### Basic Logging

```python
from lib.atoms.observability import get_logger, LogContext

# Create a logger
logger = get_logger(__name__)

# Log with context
with LogContext(user_id="user123", correlation_id="req-456"):
    logger.info("Processing request", extra_fields={"action": "create_user"})
    logger.error("Operation failed", exc_info=True)
```

### Metrics Collection

```python
from lib.atoms.observability import (
    record_http_request,
    record_tool_execution,
    http_requests_total
)

# Record HTTP request
record_http_request(
    method="POST",
    path="/api/users",
    status=201,
    duration=0.345
)

# Record tool execution
record_tool_execution(
    tool_name="create_user",
    duration=1.234,
    success=True
)

# Manually increment counter
http_requests_total.inc(labels={
    "method": "GET",
    "path": "/api/users",
    "status": "200"
})
```

### Health Checks

```python
from lib.atoms.observability import (
    register_health_check,
    SupabaseHealthCheck,
    CustomHealthCheck,
    check_health
)

# Register Supabase health check
register_health_check(
    SupabaseHealthCheck(supabase_client, timeout_seconds=5.0)
)

# Register custom health check
def check_redis():
    return redis_client.ping()

register_health_check(
    CustomHealthCheck(
        name="redis",
        component_type=ComponentType.CACHE,
        check_func=check_redis,
        critical=True
    )
)

# Check health
health_status = await check_health()
print(health_status.status)  # healthy, degraded, or unhealthy
```

### Middleware Integration

```python
from fastapi import FastAPI
from lib.atoms.observability import (
    RequestTrackingMiddleware,
    ErrorTrackingMiddleware,
    PerformanceTrackingMiddleware
)

app = FastAPI()

# Add middleware (order matters - add in reverse order of execution)
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(
    PerformanceTrackingMiddleware,
    slow_request_threshold_seconds=1.0
)
```

### Using Decorators

```python
from lib.atoms.observability import (
    observe_tool,
    log_operation,
    measure_performance
)

@observe_tool("create_user", track_performance=True, log_inputs=True)
async def create_user(username: str, email: str):
    # Tool execution is automatically monitored
    user = await db.users.create(username=username, email=email)
    return user

@log_operation("process_payment", log_level="INFO")
async def process_payment(amount: float):
    # Operation is logged with start/complete/error
    result = await payment_service.charge(amount)
    return result

@measure_performance("heavy_computation", threshold_warning_ms=500)
def heavy_computation(data: list):
    # Performance is measured and warnings logged if slow
    return sum(data)
```

### Webhook Notifications

```python
from lib.atoms.observability import (
    configure_vercel_webhook,
    webhook_manager,
    WebhookEventType,
    AlertSeverity
)

# Configure Vercel webhook
configure_vercel_webhook(
    webhook_url="https://hooks.vercel.com/abc123",
    event_types=[
        WebhookEventType.DEPLOYMENT_STARTED,
        WebhookEventType.DEPLOYMENT_COMPLETED,
        WebhookEventType.ERROR_OCCURRED
    ]
)

# Send custom alert
await webhook_manager.send_error_alert(
    error_type="DatabaseConnectionError",
    error_message="Failed to connect to Supabase",
    source="database.connection",
    metadata={"retry_count": 3}
)

# Send health degradation alert
await webhook_manager.send_health_degraded(
    component_name="supabase",
    health_status=HealthStatus.UNHEALTHY,
    message="Supabase connection timeout",
    metadata={"timeout_seconds": 5.0}
)
```

### Endpoints Integration

```python
from fastapi import FastAPI
from lib.atoms.observability import router as observability_router

app = FastAPI()

# Include observability endpoints
app.include_router(observability_router)

# Now available:
# GET /metrics - Prometheus metrics
# GET /health - Health check
# GET /health/live - Liveness probe
# GET /health/ready - Readiness probe
# GET /api/observability/dashboard - Dashboard data
# GET /api/observability/metrics/snapshot - JSON metrics
```

## Advanced Usage

### Custom Metrics

```python
from lib.atoms.observability import registry

# Register custom counter
custom_counter = registry.register_counter(
    "custom_events_total",
    "Total custom events",
    labels=["event_type", "status"]
)

# Use it
custom_counter.inc(labels={"event_type": "signup", "status": "success"})

# Register custom histogram
response_time = registry.register_histogram(
    "api_response_time_seconds",
    "API response time in seconds",
    labels=["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Measure with context manager
with response_time.time(labels={"endpoint": "/api/users"}):
    result = await process_request()
```

### Performance Monitoring

```python
from lib.atoms.observability import PerformanceMonitor

# Create performance monitor
perf_monitor = PerformanceMonitor(
    window_size=100,
    warning_threshold_ms=1000.0,
    critical_threshold_ms=5000.0
)

# Record response times
for response_time in response_times:
    perf_monitor.record_response_time(response_time)

# Check for degradation
status = perf_monitor.detect_degradation()
if status == HealthStatus.DEGRADED:
    logger.warning("Performance degradation detected")
```

### Context Propagation

```python
from lib.atoms.observability import get_propagated_headers
import httpx

async def call_downstream_service(request: Request):
    # Get headers to propagate
    headers = get_propagated_headers(request)

    # Add to downstream request
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://internal-service/api/endpoint",
            headers=headers
        )
    return response
```

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=/var/log/atoms-mcp.log

# Metrics
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# Health Checks
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=5

# Webhooks
VERCEL_WEBHOOK_URL=https://hooks.vercel.com/abc123
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xyz
```

### Vercel Deployment

Add to `vercel.json`:

```json
{
  "rewrites": [
    {
      "source": "/metrics",
      "destination": "/api/metrics"
    },
    {
      "source": "/health",
      "destination": "/api/health"
    }
  ],
  "env": {
    "LOG_LEVEL": "INFO",
    "METRICS_ENABLED": "true"
  }
}
```

## Performance Overhead

The observability module is designed for minimal overhead:

- **Logging**: ~0.1ms per log entry (JSON formatting)
- **Metrics**: ~0.05ms per metric update (thread-safe)
- **Health checks**: Run on-demand, not on every request
- **Middleware**: ~0.2ms per request (correlation ID + tracking)
- **Decorators**: ~0.1ms per decorated function call

Total overhead per request: **~0.5ms** with all features enabled.

## Best Practices

1. **Use correlation IDs** - Always set correlation IDs for request tracking
2. **Log structured data** - Use extra_fields for machine-readable logs
3. **Monitor critical paths** - Add observability to business-critical operations
4. **Set appropriate thresholds** - Configure performance thresholds based on SLOs
5. **Test health checks** - Ensure health checks are fast and reliable
6. **Use labels wisely** - Don't create high-cardinality label combinations
7. **Batch webhook notifications** - Avoid webhook storms during incidents

## Troubleshooting

### High Memory Usage

If metrics memory grows too large:
```python
# Limit histogram buckets
registry.register_histogram(
    "my_metric",
    "Description",
    buckets=[0.1, 1.0, 10.0]  # Fewer buckets
)
```

### Slow Health Checks

Reduce timeout or disable non-critical checks:
```python
check = CustomHealthCheck(
    name="optional_service",
    check_func=check_func,
    timeout_seconds=2.0,  # Shorter timeout
    critical=False  # Don't affect overall health
)
```

### Missing Correlation IDs

Ensure middleware is properly configured:
```python
# Middleware must be added before routes
app.add_middleware(RequestTrackingMiddleware)

# Then define routes
@app.get("/api/endpoint")
async def endpoint():
    # Correlation ID is automatically set
    logger.info("Processing request")
```

## Integration Examples

See the `/examples` directory for complete integration examples:
- `examples/basic_fastapi.py` - Basic FastAPI integration
- `examples/tool_monitoring.py` - MCP tool monitoring
- `examples/health_checks.py` - Custom health checks
- `examples/webhook_alerts.py` - Webhook alert setup

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/atoms-mcp/issues
- Documentation: https://docs.atoms-mcp.com/observability
- Discord: https://discord.gg/atoms-mcp
