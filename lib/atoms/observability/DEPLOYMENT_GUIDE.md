# Atoms MCP Observability - Deployment Guide

Complete guide for deploying the observability module to production on Vercel.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Vercel Deployment](#vercel-deployment)
5. [Integration Steps](#integration-steps)
6. [Monitoring Setup](#monitoring-setup)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Dependencies

Add to `requirements.txt`:

```text
fastapi>=0.104.0
starlette>=0.27.0
uvicorn>=0.24.0
aiohttp>=3.9.0
pydantic>=2.0.0
```

### Optional Dependencies

```text
# For Supabase integration
supabase>=2.0.0

# For testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

## Installation

### 1. Copy Observability Module

The observability module is located at:
```
/lib/atoms/observability/
```

Ensure all files are included:
- `__init__.py` - Module exports
- `logging.py` - Structured logging
- `metrics.py` - Metrics collection
- `health.py` - Health monitoring
- `middleware.py` - Request middleware
- `decorators.py` - Observability decorators
- `webhooks.py` - Webhook notifications
- `endpoints.py` - API endpoints

### 2. Verify Installation

```python
# Test import
from lib.atoms.observability import (
    get_logger,
    registry,
    health_monitor,
    router
)

print("Observability module loaded successfully")
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_FILE_LOGGING=false

# Metrics Configuration
METRICS_ENABLED=true
METRICS_PREFIX=atoms_mcp

# Health Check Configuration
HEALTH_CHECK_TIMEOUT=5
HEALTH_CHECK_INTERVAL=30

# Webhook Configuration
VERCEL_WEBHOOK_URL=https://hooks.vercel.com/your-webhook-id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your-webhook-id

# Application Info
APP_VERSION=1.0.0
APP_ENVIRONMENT=production
```

### Vercel Configuration

Create/update `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/metrics",
      "dest": "/api/metrics"
    },
    {
      "src": "/health",
      "dest": "/api/health"
    },
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    }
  ],
  "env": {
    "LOG_LEVEL": "INFO",
    "METRICS_ENABLED": "true",
    "APP_ENVIRONMENT": "production"
  },
  "functions": {
    "api/**/*.py": {
      "memory": 1024,
      "maxDuration": 10
    }
  }
}
```

## Vercel Deployment

### 1. Prepare FastAPI Application

Create `api/index.py`:

```python
from fastapi import FastAPI
from mangum import Mangum

from lib.atoms.observability import (
    router as observability_router,
    RequestTrackingMiddleware,
    ErrorTrackingMiddleware,
)

app = FastAPI(title="Atoms MCP API")

# Add middleware
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(ErrorTrackingMiddleware)

# Include observability endpoints
app.include_router(observability_router)

# Your application routes here
@app.get("/")
def root():
    return {"status": "ok"}

# Vercel handler
handler = Mangum(app)
```

### 2. Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

### 3. Verify Deployment

Test endpoints after deployment:

```bash
# Health check
curl https://your-app.vercel.app/health

# Metrics
curl https://your-app.vercel.app/metrics

# Dashboard
curl https://your-app.vercel.app/api/observability/dashboard
```

## Integration Steps

### Step 1: Initialize Logging

```python
from lib.atoms.observability import get_logger, LogContext

logger = get_logger(__name__)

# Use in your code
logger.info("Application started")

# With context
with LogContext(user_id="user123"):
    logger.info("Processing user request")
```

### Step 2: Add Middleware

```python
from fastapi import FastAPI
from lib.atoms.observability import (
    RequestTrackingMiddleware,
    ErrorTrackingMiddleware,
    PerformanceTrackingMiddleware,
)

app = FastAPI()

# Add middleware (order matters!)
app.add_middleware(RequestTrackingMiddleware)
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(
    PerformanceTrackingMiddleware,
    slow_request_threshold_seconds=1.0
)
```

### Step 3: Register Health Checks

```python
from lib.atoms.observability import (
    register_health_check,
    CustomHealthCheck,
    ComponentType,
)

# Custom health check
def check_database():
    # Your database check logic
    return True

register_health_check(
    CustomHealthCheck(
        name="database",
        component_type=ComponentType.DATABASE,
        check_func=check_database,
        critical=True
    )
)
```

### Step 4: Configure Webhooks

```python
from lib.atoms.observability import (
    configure_vercel_webhook,
    WebhookEventType,
)

# Configure on application startup
configure_vercel_webhook(
    webhook_url=os.getenv("VERCEL_WEBHOOK_URL"),
    event_types=[
        WebhookEventType.DEPLOYMENT_STARTED,
        WebhookEventType.DEPLOYMENT_COMPLETED,
        WebhookEventType.ERROR_OCCURRED,
        WebhookEventType.HEALTH_DEGRADED,
    ]
)
```

### Step 5: Add Observability to Tools

```python
from lib.atoms.observability import observe_tool

@observe_tool("my_tool", track_performance=True, log_inputs=True)
async def my_tool(param1: str, param2: int):
    # Your tool logic
    result = await process_data(param1, param2)
    return result
```

### Step 6: Include Observability Endpoints

```python
from lib.atoms.observability import router

app.include_router(router)
```

## Monitoring Setup

### 1. Prometheus Integration

Configure Prometheus to scrape metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'atoms-mcp'
    scrape_interval: 15s
    static_configs:
      - targets: ['your-app.vercel.app']
    metrics_path: '/metrics'
    scheme: https
```

### 2. Grafana Dashboard

Import the Atoms MCP dashboard:

1. Open Grafana
2. Go to Dashboards → Import
3. Use dashboard ID: `atoms-mcp-observability`
4. Configure data source

Key metrics to monitor:
- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Request latency
- `tool_executions_total` - Tool execution count
- `errors_total` - Error rate
- `health_check_status` - Component health

### 3. Alert Rules

Create alerting rules in Prometheus:

```yaml
# alerts.yml
groups:
  - name: atoms_mcp
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: ServiceUnhealthy
        expr: health_check_status{component="supabase"} < 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical component unhealthy"

      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile latency above 5s"
```

### 4. Vercel Integration

Configure Vercel webhooks in dashboard:

1. Go to Project Settings → Webhooks
2. Add webhook URL (your notification endpoint)
3. Select events:
   - Deployment Started
   - Deployment Completed
   - Deployment Failed

### 5. Log Aggregation

For production log aggregation, integrate with:

**Option A: Vercel Log Drains**
```bash
vercel integration add logtail
```

**Option B: Custom Log Drain**
Configure in Vercel dashboard to send logs to your logging service.

## Troubleshooting

### Issue: Metrics Not Appearing

**Solution:**
```python
# Verify metrics are being recorded
from lib.atoms.observability import get_prometheus_metrics

metrics = get_prometheus_metrics()
print(metrics)  # Should show metrics in Prometheus format
```

### Issue: Health Checks Timing Out

**Solution:**
```python
# Increase timeout
register_health_check(
    CustomHealthCheck(
        name="slow_service",
        component_type=ComponentType.EXTERNAL_API,
        check_func=check_func,
        timeout_seconds=10.0,  # Increase timeout
        critical=False  # Make non-critical if optional
    )
)
```

### Issue: Webhook Notifications Not Sending

**Solution:**
```python
# Test webhook manually
from lib.atoms.observability import webhook_manager, AlertSeverity

result = await webhook_manager.send_custom_event(
    title="Test Alert",
    message="Testing webhook configuration",
    severity=AlertSeverity.INFO
)
print(f"Webhook result: {result}")
```

### Issue: High Memory Usage

**Solution:**
```python
# Reduce metric cardinality
# Avoid high-cardinality labels (e.g., user IDs in labels)

# Before (bad):
counter.inc(labels={"user_id": user_id})  # Don't do this!

# After (good):
counter.inc(labels={"user_type": user_type})  # Use categories
```

### Issue: Correlation IDs Not Propagating

**Solution:**
```python
# Ensure middleware is properly configured
from lib.atoms.observability import RequestTrackingMiddleware

# Add middleware BEFORE routes
app.add_middleware(RequestTrackingMiddleware)

# Then define routes
@app.get("/api/endpoint")
async def endpoint():
    # Correlation ID is automatically available
    pass
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Middleware added to FastAPI app
- [ ] Health checks registered
- [ ] Webhooks configured
- [ ] Observability endpoints included
- [ ] Prometheus scraping configured
- [ ] Grafana dashboard imported
- [ ] Alert rules defined
- [ ] Log drains configured
- [ ] Performance thresholds tuned
- [ ] Error tracking tested
- [ ] Deployment notifications working

## Performance Optimization

### 1. Disable Unnecessary Features

```python
# In development, disable webhooks
if os.getenv("APP_ENVIRONMENT") != "production":
    # Don't configure webhooks in dev
    pass
```

### 2. Adjust Metric Resolution

```python
# Use fewer histogram buckets for high-throughput endpoints
custom_histogram = registry.register_histogram(
    "fast_endpoint_duration",
    "Fast endpoint duration",
    buckets=[0.01, 0.1, 1.0]  # Fewer buckets = less memory
)
```

### 3. Batch Logging

```python
# For high-volume logs, consider batching
# (Implementation depends on your logging backend)
```

## Support

For issues and questions:
- Documentation: https://docs.atoms-mcp.com
- GitHub Issues: https://github.com/atoms-mcp/issues
- Discord: https://discord.gg/atoms-mcp

## Next Steps

1. Review the [README.md](README.md) for API documentation
2. Check [examples/](examples/) for integration examples
3. Run tests with `pytest lib/atoms/observability/tests/`
4. Monitor your deployment metrics
5. Set up alerts for critical conditions
