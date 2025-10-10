# Migration Guide: Dashboard & Alerting (zen-mcp-server → observability-kit)

This guide helps you migrate from zen-mcp-server's `monitoring_dashboard.py` to the modular dashboard and alerting system in observability-kit.

## Overview

The dashboard and alerting utilities have been extracted and refactored into production-ready modules:

- **observability/dashboards/** - Metric aggregation, real-time streaming, data formatting
- **observability/alerting/** - Alert management, rules, and notifications

## Installation

```bash
# Basic installation
pip install -e /path/to/pheno-sdk/observability-kit

# With WebSocket support (optional)
pip install observability-kit[websockets]

# With HTTP notifications (optional)  
pip install observability-kit[http]
```

## Key Changes

### Architecture

**Before (zen-mcp-server):**
- Monolithic `MonitoringDashboard` class
- Lambda-based alert conditions
- Built-in WebSocket server
- Tight coupling with zen-mcp-server utilities

**After (observability-kit):**
- Modular components (aggregator, collector, streamer, manager)
- Structured alert conditions (ThresholdCondition, RateCondition, etc.)
- Optional WebSocket support
- Framework-agnostic design

## Migration Steps

### 1. Update Imports

**Before:**
```python
from utils.monitoring_dashboard import (
    MonitoringDashboard,
    AlertSeverity,
    Alert,
    MetricType,
    Metric,
)
```

**After:**
```python
from observability import (
    # Dashboards
    MetricAggregator,
    DashboardDataCollector,
    DashboardFormatter,
    # Alerting
    AlertManager,
    AlertSeverity,
    Alert,
    AlertRule,
    ThresholdCondition,
)
```

### 2. Dashboard Setup

**Before:**
```python
dashboard = MonitoringDashboard(
    redis_client=redis_client,
    websocket_port=8765,
)
await dashboard.start_monitoring()
```

**After:**
```python
# Basic setup
aggregator = MetricAggregator(redis_client=redis_client)
collector = DashboardDataCollector(metric_aggregator=aggregator)

# With WebSocket (optional)
from observability.dashboards import WebSocketDashboard
dashboard = WebSocketDashboard(
    dashboard_collector=collector,
    port=8765,
)
await dashboard.start()
```

### 3. Recording Metrics

**Before:**
```python
await dashboard.record_metric(
    "api_requests",
    1,
    "counter",
    labels={"endpoint": "/users"}
)
```

**After:**
```python
from observability.dashboards import MetricType

await aggregator.record_metric(
    "api_requests",
    1,
    MetricType.COUNTER,
    labels={"endpoint": "/users"}
)
```

### 4. Alert Management

**Before:**
```python
dashboard.add_alert_rule(
    name="high_cpu",
    description="CPU > 90%",
    severity=AlertSeverity.HIGH,
    condition=lambda: get_cpu_usage() > 0.9,
    threshold=0.9,
)
```

**After:**
```python
from observability.alerting import (
    AlertManager,
    AlertRule,
    ThresholdCondition,
)

manager = AlertManager()

rule = AlertRule(
    name="high_cpu",
    description="CPU > 90%",
    severity=AlertSeverity.HIGH,
    condition=ThresholdCondition("cpu_usage", 0.9, ">"),
    threshold=0.9,
)

# Evaluate and trigger
context = {"cpu_usage": 0.95}
if rule.evaluate(context):
    alert = rule.create_alert()
    manager.alerts[alert.alert_id] = alert
    manager.trigger_alert(alert.alert_id, current_value=0.95)
```

### 5. Health Monitoring Integration

**Before:**
```python
health = await dashboard.get_system_health()
```

**After:**
```python
from observability import HealthMonitor

health_monitor = HealthMonitor()

@health_monitor.register_check("database")
async def check_database():
    return HealthCheckResult(
        component="database",
        status=HealthStatus.HEALTHY,
    )

collector = DashboardDataCollector(
    metric_aggregator=aggregator,
    health_monitor=health_monitor,
)
```

### 6. Notifications

**Before:**
```python
# Webhook via environment variable
dashboard = MonitoringDashboard()
```

**After:**
```python
manager = AlertManager(webhook_url="https://hooks.example.com/alert")

# Custom handlers
async def slack_handler(alert):
    # Send to Slack
    pass

manager.add_notification_handler("slack", slack_handler)

# Trigger and notify
manager.trigger_alert(alert_id)
await manager.send_notifications(alert_id)
```

## Feature Comparison

| Feature | zen-mcp-server | observability-kit |
|---------|---------------|-------------------|
| Metric Recording | ✅ | ✅ |
| WebSocket Streaming | ✅ Built-in | ✅ Optional |
| Alert Rules | ✅ Lambda | ✅ Structured conditions |
| Multi-Tenant | ❌ | ✅ |
| Health Integration | ✅ Embedded | ✅ Modular |
| Redis Persistence | ✅ | ✅ |
| Custom Conditions | ❌ | ✅ |
| Alert Filtering | ❌ | ✅ |

## Complete Example

**Before (zen-mcp-server):**
```python
from utils.monitoring_dashboard import MonitoringDashboard, AlertSeverity

dashboard = MonitoringDashboard()

dashboard.add_alert_rule(
    name="high_error_rate",
    description="Error rate > 5%",
    severity=AlertSeverity.HIGH,
    condition=lambda: calculate_error_rate() > 0.05,
    threshold=0.05,
)

await dashboard.start_monitoring()
await dashboard.record_metric("errors", 1, "counter")
data = await dashboard.get_dashboard_data()
```

**After (observability-kit):**
```python
from observability import (
    MetricAggregator,
    DashboardDataCollector,
    AlertManager,
    AlertRule,
    RateCondition,
    AlertSeverity,
    MetricType,
)

# Setup
aggregator = MetricAggregator()
manager = AlertManager()
collector = DashboardDataCollector(metric_aggregator=aggregator)

# Create alert rule
error_rule = AlertRule(
    name="high_error_rate",
    description="Error rate > 5%",
    severity=AlertSeverity.HIGH,
    condition=RateCondition("errors", "requests", 0.05),
    threshold=0.05,
)

# Record metrics
await aggregator.record_metric("errors", 1, MetricType.COUNTER)
await aggregator.record_metric("requests", 1, MetricType.COUNTER)

# Check alerts
metrics = await aggregator.get_metrics()
context = {
    "errors": sum(1 for m in metrics if m.name == "errors"),
    "requests": sum(1 for m in metrics if m.name == "requests"),
}

if error_rule.evaluate(context):
    alert = error_rule.create_alert()
    manager.alerts[alert.alert_id] = alert
    await manager.check_and_notify(alert.alert_id, context["errors"] / context["requests"])

# Get dashboard data
data = await collector.get_dashboard_data()
```

## New Features

### 1. Multi-Tenant Support

```python
# Tenant-specific metrics
await aggregator.record_metric(
    "requests", 1, MetricType.COUNTER,
    tenant_id="tenant_a"
)

# Tenant-specific alerts
alert = manager.register_alert(
    ...,
    tenant_id="tenant_a"
)

# Tenant filtering
alerts = manager.get_active_alerts(tenant_id="tenant_a")
```

### 2. Structured Alert Conditions

```python
from observability.alerting import (
    ThresholdCondition,
    RateCondition,
    ComponentHealthCondition,
    CompositeCondition,
)

# Threshold
cpu_condition = ThresholdCondition("cpu_usage", 0.9, ">")

# Rate
error_condition = RateCondition("errors", "total_requests", 0.05)

# Component health
db_condition = ComponentHealthCondition("database", ["critical"])

# Composite (AND/OR)
composite = CompositeCondition(
    [cpu_condition, error_condition],
    logic="AND"
)
```

### 3. Alert Filtering

```python
# By severity
critical_alerts = manager.get_active_alerts(severity=AlertSeverity.CRITICAL)

# By tenant
tenant_alerts = manager.get_active_alerts(tenant_id="tenant_a")

# Custom filter
def priority_filter(alert):
    return alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]

manager.add_filter(priority_filter)
filtered = manager.get_active_alerts()
```

### 4. Dashboard Formatting

```python
from observability.dashboards import DashboardFormatter

formatter = DashboardFormatter()

# Format component status
status = formatter.format_component_status(
    component_name="database",
    status="healthy",
    response_time_ms=42.5,
)

# Format time series
series = formatter.format_metric_series(
    metrics,
    bucket_minutes=5
)

# Format alerts
alert_data = formatter.format_alert(
    alert_id="alert-123",
    name="high_cpu",
    severity="high",
    triggered_at=datetime.now(),
)
```

## Testing

Run the examples:
```bash
cd pheno-sdk/observability-kit

# Dashboard examples
python examples/monitoring_dashboard.py

# Alerting examples
python examples/alerting_system.py
```

Run tests:
```bash
pytest tests/test_dashboards.py -v
pytest tests/test_alerting.py -v
```

## Troubleshooting

### WebSocket Not Available
```bash
pip install websockets
```

### Import Errors
```bash
pip install -e /path/to/pheno-sdk/observability-kit
```

### Check Optional Dependencies
```python
from observability.dashboards import streaming
print(f"WebSocket: {streaming.WEBSOCKETS_AVAILABLE}")
```

## Next Steps

1. Update zen-mcp-server to use observability-kit
2. Run integration tests
3. Monitor for runtime issues
4. Explore multi-tenancy features
5. Add custom alert conditions

## Resources

- Examples: `/examples/monitoring_dashboard.py`, `/examples/alerting_system.py`
- Tests: `/tests/test_dashboards.py`, `/tests/test_alerting.py`
- Source: `/observability/dashboards/`, `/observability/alerting/`
