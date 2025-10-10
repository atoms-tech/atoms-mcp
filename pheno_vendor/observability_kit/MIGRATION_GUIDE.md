# Migration Guide: Structured Logging Enhancements

This guide helps you migrate from the basic structured logging implementation to the enhanced observability-kit with advanced features.

## What's New

The enhanced structured logging system adds:

1. **StructuredFormatter** - Integration with Python's logging module
2. **SecurityFilter** - Automatic PII/secrets redaction
3. **PerformanceFilter** - Duration tracking and slow operation detection
4. **Event-specific methods** - audit(), security(), business(), performance()
5. **Function decorators** - @log_function_call, @log_async_function_call, @log_call
6. **Enhanced context management** - LogContext with correlation IDs

## Migration Steps

### 1. Update Your Imports

**Old (zen-mcp-server style):**
```python
from utils.structured_logging import (
    get_logger,
    LogContext,
    log_function_call,
    log_async_function_call,
)

logger = get_logger(__name__)
```

**New (observability-kit):**
```python
from observability.logging import (
    StructuredLogger,
    LogContext,
    log_function_call,
    log_async_function_call,
    StructuredFormatter,
    SecurityFilter,
    PerformanceFilter,
)

logger = StructuredLogger(__name__)
```

### 2. Using StructuredFormatter with Python's logging

The new `StructuredFormatter` integrates with Python's standard logging module:

```python
import logging
from observability.logging import StructuredFormatter, SecurityFilter

# Create logger
logger = logging.getLogger(__name__)

# Add handler with structured formatter
handler = logging.StreamHandler()
formatter = StructuredFormatter(
    service_name="my-service",
    environment="production",
    version="1.0.0"
)
handler.setFormatter(formatter)

# Add security filter for PII redaction
handler.addFilter(SecurityFilter())

logger.addHandler(handler)

# Use it
logger.info("User logged in", extra={"user_id": "123"})
```

### 3. Security Filtering

Automatically redact sensitive information:

```python
from observability.logging import SecurityFilter

# Create filter with custom options
security_filter = SecurityFilter(
    redact_emails=True,
    redact_credit_cards=True,
    redact_ssn=True,
    redact_phone=True,
    custom_patterns=[r"customer_id:\s*(\d+)"]
)

handler.addFilter(security_filter)

# These will be automatically redacted:
logger.info("User password=secret123")  # "password=[REDACTED]"
logger.info("Card: 4532-1234-5678-9010")  # "Card: [REDACTED]"
logger.info("Email: alice@example.com")   # "Email: [REDACTED]"
```

### 4. Performance Tracking

Track operation duration automatically:

```python
from observability.logging import PerformanceFilter

# Add performance filter
perf_filter = PerformanceFilter(
    slow_threshold_ms=1000,   # Mark as slow if > 1s
    warn_threshold_ms=5000,   # Upgrade to WARNING if > 5s
)
handler.addFilter(perf_filter)

# Log request start/end with correlation ID
correlation_id = "req-123"

logger.info("Request started", extra={
    "event_type": "request_start",
    "correlation_id": correlation_id
})

# ... do work ...

logger.info("Request ended", extra={
    "event_type": "request_end",
    "correlation_id": correlation_id
})
# Automatically includes duration_ms!
```

### 5. Event-Specific Logging

Use specialized logging methods:

**Old:**
```python
logger.info(f"AUDIT: user_login", user_id="123")
```

**New:**
```python
# Audit events
logger.audit("user_login", user_id="123", ip="192.168.1.1")

# Security events
logger.security("failed_auth", user="admin", attempts=3)

# Business events
logger.business("order_completed", order_id="ORD-123", amount=99.99)

# Performance events
logger.performance("db_query", duration=0.145, query="SELECT * FROM users")

# Request logging
logger.request_start("GET", "/api/users")
logger.request_end("GET", "/api/users", 200, duration_ms=150.5)

# Tool calls (for MCP servers)
logger.tool_call("execute_code", language="python")
logger.tool_result("execute_code", success=True, duration=0.523)
```

### 6. Function Decorators

**Old:**
```python
@log_function_call(logger, log_args=True)
def process_data(data):
    return data
```

**New (same, but with more options):**
```python
from observability.logging import log_call

# Universal decorator (works for sync and async)
@log_call(logger, log_args=True, log_result=True)
def process_data(data):
    return data

@log_call(logger, log_args=True)
async def async_process(data):
    return data

# Method-specific decorator
from observability.logging import trace_method

class UserService:
    @trace_method(logger)
    def get_user(self, user_id: str):
        return {"id": user_id}
```

### 7. Context Management

**Old (zen-mcp-server):**
```python
with LogContext(
    correlation_id="123",
    tenant_id="tenant-a",
    user_id="user-1"
):
    logger.info("Processing request")
```

**New (same API, enhanced):**
```python
from observability.logging import LogContext

# Same API as before
with LogContext(
    correlation_id="123",
    tenant_id="tenant-a",
    user_id="user-1"
):
    logger.info("Processing request")

# Or use StructuredLogger's context method
with logger.context(user_id="123", session_id="sess-456"):
    logger.info("Processing")
```

### 8. Complete Migration Example

**Before (zen-mcp-server):**
```python
from utils.structured_logging import (
    get_logger,
    LogContext,
    log_function_call,
)

logger = get_logger(__name__)

@log_function_call(logger)
def process_request(user_id: str):
    with LogContext(correlation_id=f"req-{user_id}"):
        logger.info("Processing user request")
        return {"status": "success"}
```

**After (observability-kit with all features):**
```python
import logging
from observability.logging import (
    StructuredLogger,
    StructuredFormatter,
    SecurityFilter,
    PerformanceFilter,
    LogContext,
    log_call,
)

# Setup Python logging with all filters
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter(
    service_name="my-service",
    environment="production"
))
handler.addFilter(SecurityFilter())
handler.addFilter(PerformanceFilter(slow_threshold_ms=1000))
logger.addHandler(handler)

# Also create StructuredLogger for event methods
struct_logger = StructuredLogger(__name__)

@log_call(log_args=True, log_result=True)
def process_request(user_id: str):
    with LogContext(correlation_id=f"req-{user_id}"):
        struct_logger.audit("request_received", user_id=user_id)

        # Sensitive data automatically redacted
        logger.info(f"Processing for password=secret123")

        struct_logger.business("request_processed", user_id=user_id)

        return {"status": "success"}
```

## Backward Compatibility

The observability-kit maintains backward compatibility:

1. **StructuredLogger** still exists and works the same way
2. **LogContext** has the same API
3. **Decorators** have the same function signatures
4. **Context variables** (`_correlation_id_var`, etc.) are preserved

You can gradually migrate by:

1. Keep using `StructuredLogger` for application code
2. Add `StructuredFormatter` + filters to existing Python loggers
3. Gradually adopt event-specific methods (audit, security, etc.)
4. Add decorators to new functions

## Performance Considerations

- **SecurityFilter**: Regex-based, minimal overhead (~0.1ms per log)
- **PerformanceFilter**: In-memory tracking, negligible overhead
- **StructuredFormatter**: JSON serialization, ~0.5ms per log (same as before)

## Integration with zen-mcp-server

zen-mcp-server has been updated with a graceful fallback:

```python
# In zen-mcp-server/utils/monitoring_dashboard.py
try:
    from observability.logging import StructuredLogger
    logger = StructuredLogger(__name__)
except ImportError:
    # Fallback to local implementation
    from utils.structured_logging import get_logger
    logger = get_logger(__name__)
```

This allows:
- Using observability-kit when available
- Falling back to local implementation if not installed
- Zero breaking changes

## Testing Your Migration

Run the example to verify:

```bash
cd pheno-sdk/observability-kit
python examples/structured_logging_advanced.py
```

Run tests:

```bash
pytest tests/test_logging_advanced.py -v
```

## Common Issues

### Issue: "SecurityFilter not redacting"
**Solution:** Make sure filter is added to handler, not logger:
```python
handler.addFilter(SecurityFilter())  # Correct
logger.addFilter(SecurityFilter())   # Won't work
```

### Issue: "PerformanceFilter not calculating duration"
**Solution:** Ensure correlation_id and event_type are in extra:
```python
logger.info("Start", extra={
    "event_type": "request_start",
    "correlation_id": "123"
})
```

### Issue: "Import error from observability.logging"
**Solution:** Install observability-kit:
```bash
pip install -e pheno-sdk/observability-kit
```

## Next Steps

1. Review the [examples/structured_logging_advanced.py](examples/structured_logging_advanced.py) for comprehensive examples
2. Check [tests/test_logging_advanced.py](tests/test_logging_advanced.py) for usage patterns
3. Read the API documentation in each module's docstrings

## Questions?

- For zen-mcp-server specific questions, check the utils/structured_logging.py source
- For observability-kit questions, check the observability/logging/ modules
- All components maintain backward compatibility with the original API
