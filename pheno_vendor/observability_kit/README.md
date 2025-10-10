# Observability-Kit

Production-grade observability SDK with unified logging, metrics, and distributed tracing for Python applications.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Observability-Kit provides a comprehensive, standards-compliant observability solution for Python applications based on the **Three Pillars of Observability**:

### 1. Structured Logging
- **JSON structured output** for log aggregation systems (Loki, ELK, Splunk)
- **Automatic correlation ID injection** from pydevkit if available
- **Context-aware logging** with request/trace metadata
- **Performance tracking** with duration measurement
- Thread-safe and async-safe context propagation

### 2. Metrics Collection
- **Prometheus-compatible metrics** (Counter, Gauge, Histogram)
- **Thread-safe in-memory aggregation** with minimal overhead
- **Multi-dimensional labels/tags** for rich metric data
- **HTTP /metrics endpoint** for Prometheus scraping
- Standard Prometheus exposition format

### 3. Distributed Tracing
- **W3C Trace Context standard** for cross-service tracing
- **Parent-child span relationships** for operation hierarchy
- **Context propagation** across distributed services
- **OpenTelemetry export support** for trace backends
- Sampling support for high-volume systems

## Key Features

- **Standards Compliance**: W3C Trace Context, Prometheus exposition format, OpenTelemetry
- **Production Ready**: Thread-safe, async-safe, type-safe with Pydantic
- **Zero Config Start**: Works out of the box with sensible defaults
- **Framework Integration**: Built-in support for FastAPI, Flask, and standalone use
- **Minimal Overhead**: Optimized for performance with lazy evaluation
- **Rich Metadata**: Service name, environment, version, hostname auto-capture
- **Error Tracking**: Automatic exception capture with stack traces
- **Context Propagation**: Seamless correlation between logs, metrics, and traces

## Installation

### Basic Installation

```bash
pip install observability-kit
```

### With Optional Dependencies

```bash
# For Prometheus metrics export
pip install observability-kit[prometheus]

# For OpenTelemetry integration
pip install observability-kit[opentelemetry]

# Install all optional dependencies
pip install observability-kit[all]
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/kooshapari/observability-kit.git
cd observability-kit

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Structured Logging

```python
from observability import StructuredLogger, generate_correlation_id

# Create logger with metadata
logger = StructuredLogger(
    "my-service",
    service_name="api",
    environment="production",
    version="1.0.0"
)

# Basic logging
logger.info("Application started")
logger.warning("High memory usage", memory_mb=512)

# With correlation ID
correlation_id = generate_correlation_id()
logger.set_correlation_id(correlation_id)
logger.info("Processing request", request_id="req-123")

# Context-based logging
with logger.context(user_id="user-456", session_id="sess-789"):
    logger.info("User logged in")
    logger.info("User fetched profile")

# Timing operations
with logger.timing("Database query"):
    # Your database operation here
    pass

# Error logging with exception info
try:
    raise ValueError("Something went wrong")
except Exception as e:
    logger.error("Operation failed", exc_info=e, operation="demo")
```

**JSON Output:**
```json
{
  "timestamp": "2025-01-15T10:30:00.123456Z",
  "level": "INFO",
  "message": "User logged in",
  "logger_name": "my-service",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "b7ad6b7169203331",
  "context": {
    "user_id": "user-456",
    "session_id": "sess-789"
  },
  "service_name": "api",
  "environment": "production",
  "version": "1.0.0",
  "hostname": "api-server-01"
}
```

### 2. Metrics Collection

```python
from observability import MetricsCollector

# Create metrics collector
metrics = MetricsCollector()

# Counter: for counting events (only goes up)
request_counter = metrics.counter(
    "http_requests_total",
    "Total HTTP requests",
    labels=["method", "status"]
)
request_counter.inc({"method": "GET", "status": "200"})
request_counter.inc({"method": "POST", "status": "201"}, value=5)

# Gauge: for values that go up and down
memory_gauge = metrics.gauge(
    "memory_usage_bytes",
    "Current memory usage in bytes"
)
memory_gauge.set(1024 * 1024 * 100)  # 100 MB
memory_gauge.inc(1024 * 1024 * 50)    # Add 50 MB
memory_gauge.dec(1024 * 1024 * 20)    # Remove 20 MB

# Histogram: for distribution of values
latency_histogram = metrics.histogram(
    "request_duration_seconds",
    "Request duration in seconds",
    labels=["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
latency_histogram.observe(0.042, {"endpoint": "/api/users"})

# Export to Prometheus format
prometheus_text = metrics.to_prometheus_text()
print(prometheus_text)
```

### 3. Distributed Tracing

```python
from observability import DistributedTracer, SpanKind, trace_function, set_default_tracer

# Create tracer
tracer = DistributedTracer("my-service", sample_rate=1.0)
set_default_tracer(tracer)

# Manual span creation with context manager
with tracer.start_span("process_order", kind=SpanKind.INTERNAL) as span:
    span.set_attribute("order_id", "order-123")
    span.set_attribute("amount", 99.99)

    # Nested span for database operation
    with tracer.start_span("db.query", kind=SpanKind.CLIENT) as db_span:
        db_span.set_attribute("query", "SELECT * FROM orders")
        db_span.set_attribute("db.system", "postgresql")
        # Database operation here

    # Add events to span
    span.add_event("Payment processed", {"status": "success"})

# Decorator-based tracing
@trace_function(capture_args=True, capture_result=True)
def fetch_user(user_id: str) -> dict:
    """Fetch user with automatic tracing."""
    return {"id": user_id, "name": "Alice"}

# Async function tracing
from observability import trace_async

@trace_async(capture_args=True)
async def fetch_user_async(user_id: str) -> dict:
    """Async fetch user with automatic tracing."""
    return {"id": user_id, "name": "Bob"}
```

### 4. W3C Trace Context Propagation

```python
# Service A: Create span and inject context
with tracer.start_span("service_a_operation", kind=SpanKind.SERVER) as span:
    # Inject trace context for HTTP headers
    headers = tracer.inject_context(span)
    # headers = {"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"}

    # Make HTTP request to Service B with headers
    # requests.get("http://service-b/api", headers=headers)

# Service B: Extract context and continue trace
def handle_request(request_headers):
    # Extract parent context from headers
    parent_context = tracer.extract_context(request_headers)

    # Create child span
    with tracer.start_span(
        "service_b_operation",
        kind=SpanKind.SERVER,
        parent_context=parent_context
    ) as span:
        # This span is now part of the same trace
        span.set_attribute("service", "service-b")
```

## FastAPI Integration

Complete FastAPI application with observability instrumentation:

```python
from fastapi import FastAPI, Request
from observability import (
    StructuredLogger,
    MetricsCollector,
    DistributedTracer,
    PrometheusExporter,
    SpanKind,
    generate_correlation_id,
    set_default_tracer,
    trace_async,
)

# Initialize observability stack
logger = StructuredLogger("api", service_name="user-service", environment="prod")
metrics = MetricsCollector()
tracer = DistributedTracer("user-service")
set_default_tracer(tracer)

# Define metrics
http_requests = metrics.counter(
    "http_requests_total",
    "Total HTTP requests",
    labels=["method", "endpoint", "status"]
)
http_duration = metrics.histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    labels=["method", "endpoint"]
)

app = FastAPI()

# Observability middleware
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    import time
    start_time = time.time()

    # Correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", generate_correlation_id())
    logger.set_correlation_id(correlation_id)

    # Trace context
    parent_context = tracer.extract_context(dict(request.headers))

    with tracer.start_span(
        f"{request.method} {request.url.path}",
        kind=SpanKind.SERVER,
        parent_context=parent_context
    ) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))

        # Set trace context in logger
        logger.set_trace_context(span.context.trace_id, span.context.span_id)

        logger.info("Request started", method=request.method, path=request.url.path)

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        http_requests.inc({
            "method": request.method,
            "endpoint": request.url.path,
            "status": str(response.status_code)
        })
        http_duration.observe(duration, {
            "method": request.method,
            "endpoint": request.url.path
        })

        logger.info(
            "Request completed",
            status=response.status_code,
            duration_ms=duration * 1000
        )

        # Add headers
        response.headers["X-Correlation-ID"] = correlation_id
        trace_headers = tracer.inject_context(span)
        response.headers.update(trace_headers)

        return response

# API endpoints
@app.get("/users/{user_id}")
@trace_async(capture_args=True)
async def get_user(user_id: str):
    logger.info("Fetching user", user_id=user_id)
    return {"id": user_id, "name": "Alice"}

# Prometheus metrics endpoint
exporter = PrometheusExporter(metrics)
exporter.setup_fastapi(app)

# Run: uvicorn main:app --host 0.0.0.0 --port 8000
```

## Grafana Stack Setup

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4318:4318"   # OTLP HTTP
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml

volumes:
  grafana-storage:
```

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['host.docker.internal:8000']
    scrape_interval: 5s
```

### Grafana Setup

1. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

2. **Access Grafana:**
   - URL: http://localhost:3000
   - Login: admin/admin

3. **Add Data Sources:**
   - **Prometheus**: http://prometheus:9090
   - **Loki**: http://loki:3100
   - **Tempo**: http://tempo:3200

4. **Sample Queries:**
   ```promql
   # Request rate
   rate(http_requests_total[5m])

   # Request duration p95
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

   # Error rate
   sum(rate(http_requests_total{status=~"5.."}[5m])) /
   sum(rate(http_requests_total[5m]))
   ```

5. **Loki Log Queries:**
   ```logql
   # All logs for service
   {service_name="user-service"}

   # Error logs only
   {service_name="user-service"} |= "ERROR"

   # Logs for specific trace
   {service_name="user-service"} | json | trace_id="0af7651916cd43dd8448eb211c80319c"
   ```

## API Reference

### StructuredLogger

```python
class StructuredLogger:
    def __init__(
        self,
        name: str,
        *,
        service_name: Optional[str] = None,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        level: LogLevel = LogLevel.INFO,
        output_stream = None,
    ):
        """Initialize structured logger."""

    def info(self, message: str, **extra: Any) -> None:
        """Log info message."""

    def error(self, message: str, *, exc_info: Optional[Exception] = None, **extra: Any) -> None:
        """Log error message with optional exception info."""

    def context(self, **context_data: Any) -> LogContext:
        """Create a context manager that adds context to all logs."""

    def timing(self, message: Optional[str] = None) -> TimingContext:
        """Create a context manager for timing operations."""

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current context/thread."""

    def set_trace_context(self, trace_id: str, span_id: str) -> None:
        """Set trace context for current context/thread."""
```

### MetricsCollector

```python
class MetricsCollector:
    def counter(self, name: str, help_text: str, labels: Optional[List[str]] = None) -> Counter:
        """Create or retrieve a counter metric."""

    def gauge(self, name: str, help_text: str, labels: Optional[List[str]] = None) -> Gauge:
        """Create or retrieve a gauge metric."""

    def histogram(
        self,
        name: str,
        help_text: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[Sequence[float]] = None,
    ) -> Histogram:
        """Create or retrieve a histogram metric."""

    def to_prometheus_text(self) -> str:
        """Export metrics in Prometheus text format."""
```

### DistributedTracer

```python
class DistributedTracer:
    def __init__(
        self,
        service_name: str,
        *,
        sample_rate: float = 1.0,
        max_spans: int = 10000,
    ):
        """Initialize distributed tracer."""

    def start_span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[SpanContext] = None,
    ) -> SpanManager:
        """Start a new span."""

    def inject_context(self, span: Span) -> Dict[str, str]:
        """Inject trace context as HTTP headers (W3C Trace Context)."""

    def extract_context(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract trace context from HTTP headers."""

    def export_spans(self) -> List[Dict[str, Any]]:
        """Export all spans as dictionaries."""
```

### PrometheusExporter

```python
class PrometheusExporter:
    def __init__(self, collector: MetricsCollector):
        """Initialize Prometheus exporter."""

    def export(self) -> str:
        """Export metrics in Prometheus text format."""

    def setup_fastapi(self, app, path: str = "/metrics") -> None:
        """Setup Prometheus metrics endpoint in FastAPI app."""

    def setup_flask(self, app, path: str = "/metrics") -> None:
        """Setup Prometheus metrics endpoint in Flask app."""

    def start_server(self, port: int = 9090, host: str = "0.0.0.0") -> None:
        """Start a standalone HTTP server for metrics endpoint."""
```

## Production Deployment Best Practices

### 1. Log Configuration

```python
# Production logger setup
logger = StructuredLogger(
    "my-service",
    service_name="user-api",
    environment="production",
    version=os.getenv("APP_VERSION", "unknown"),
    level=LogLevel.INFO,  # Don't use DEBUG in production
)

# Write logs to file for Promtail/Fluentd
log_file = open("/var/log/app/application.log", "a")
logger = StructuredLogger("my-service", output_stream=log_file)
```

### 2. Metrics Configuration

```python
# Use appropriate bucket sizes for your latency patterns
http_duration = metrics.histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    labels=["method", "endpoint"],
    # Customize buckets based on your SLAs
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Limit label cardinality to avoid memory issues
# Bad: user_id as label (high cardinality)
# Good: endpoint, method, status (low cardinality)
```

### 3. Trace Sampling

```python
# Use sampling in high-volume production
tracer = DistributedTracer(
    "my-service",
    sample_rate=0.1,  # Sample 10% of traces
    max_spans=10000,  # Limit memory usage
)

# Always sample errors
with tracer.start_span("operation") as span:
    try:
        # operation
        pass
    except Exception as e:
        # Force sampling for errors
        span.context.trace_flags |= 0x01
        raise
```

### 4. Resource Management

```python
# Periodic cleanup of old spans
import threading
import time

def cleanup_spans():
    while True:
        time.sleep(300)  # Every 5 minutes
        tracer.clear_spans()

cleanup_thread = threading.Thread(target=cleanup_spans, daemon=True)
cleanup_thread.start()
```

### 5. Error Handling

```python
# Always log errors with context
try:
    process_request(request_id)
except Exception as e:
    logger.error(
        "Request processing failed",
        exc_info=e,
        request_id=request_id,
        user_id=user_id,
    )
    # Record error metric
    error_count.inc({"error_type": type(e).__name__})
    raise
```

## Performance Considerations

### Overhead Benchmarks

- **Logging**: ~0.1ms per log entry (JSON serialization)
- **Metrics**: ~0.01ms per metric operation (thread-safe increment)
- **Tracing**: ~0.05ms per span creation (context propagation)

### Optimization Tips

1. **Use appropriate log levels:**
   ```python
   # Don't use DEBUG in production
   logger = StructuredLogger("app", level=LogLevel.INFO)
   ```

2. **Limit label cardinality:**
   ```python
   # Bad: High cardinality
   counter.inc({"user_id": user_id})  # Millions of users

   # Good: Low cardinality
   counter.inc({"endpoint": "/api/users"})  # Few endpoints
   ```

3. **Sample traces in high-volume systems:**
   ```python
   tracer = DistributedTracer("app", sample_rate=0.01)  # 1% sampling
   ```

4. **Use context managers for cleanup:**
   ```python
   # Spans automatically end and release resources
   with tracer.start_span("operation") as span:
       # work
       pass  # Span ends here
   ```

5. **Batch metric updates when possible:**
   ```python
   # Instead of multiple inc(1) calls
   counter.inc(value=batch_size)
   ```

## Integration with pydevkit Correlation IDs

Observability-Kit automatically integrates with [pydevkit](https://github.com/kooshapari/pydevkit) for correlation ID management:

```python
# pydevkit sets correlation ID
from pydevkit.tracing.correlation_id import set_correlation_id
set_correlation_id("req-123")

# Observability-Kit automatically picks it up
logger = StructuredLogger("app")
logger.info("Request received")  # Includes correlation_id: "req-123"

# Or set globally for observability-kit
from observability import set_global_correlation_id
set_global_correlation_id("req-456")  # Also sets in pydevkit if available
```

## Examples

Complete examples are available in the `examples/` directory:

- **basic_usage.py**: Comprehensive examples of all three pillars
- **fastapi_example.py**: Full FastAPI application with observability
- **grafana_setup.py**: Grafana stack configuration and setup

Run examples:

```bash
# Basic usage
python examples/basic_usage.py

# FastAPI example
pip install fastapi uvicorn
python examples/fastapi_example.py

# Then access:
# - API: http://localhost:8000
# - Metrics: http://localhost:8000/metrics
# - Spans: http://localhost:8000/debug/spans

# Grafana setup guide
python examples/grafana_setup.py
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=observability --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy observability/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- **Documentation**: [https://observability-kit.readthedocs.io](https://observability-kit.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/kooshapari/observability-kit/issues)
- **Repository**: [https://github.com/kooshapari/observability-kit](https://github.com/kooshapari/observability-kit)

## Acknowledgments

Built with best practices from:
- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)
- [Prometheus Exposition Format](https://prometheus.io/docs/instrumenting/exposition_formats/)
- [OpenTelemetry](https://opentelemetry.io/)
- [The Three Pillars of Observability](https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/)
