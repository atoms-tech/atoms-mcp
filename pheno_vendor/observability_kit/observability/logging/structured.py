"""Structured logging with JSON output and correlation ID support.

Based on 2025 Python best practices:
- JSON structured output for log aggregation (Loki, ELK, etc.)
- Automatic correlation ID injection for distributed tracing
- Context-aware logging with request/trace metadata
- Performance-optimized with lazy evaluation
- Type-safe with Pydantic models
- Integration with Python's logging module via StructuredFormatter
"""

import contextvars
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Standard log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogRecord(BaseModel):
    """Structured log record model."""
    timestamp: str = Field(description="ISO 8601 timestamp in UTC")
    level: LogLevel
    message: str
    logger_name: str
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    extra: Dict[str, Any] = Field(default_factory=dict)

    # Exception details
    exception: Optional[str] = None
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None

    # Service/deployment metadata
    service_name: Optional[str] = None
    environment: Optional[str] = None
    version: Optional[str] = None
    hostname: Optional[str] = None

    # Performance
    duration_ms: Optional[float] = None


# Context variables for async-safe correlation ID and trace context
_correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "trace_id", default=None
)
_span_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "span_id", default=None
)
_context_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "log_context", default={}
)

# Thread-local storage for sync contexts
_thread_local = threading.local()


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging compatible with Python logging module.

    This formatter integrates with the standard logging module while providing
    structured JSON output and automatic context injection.

    Example:
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(StructuredFormatter(service_name="my-service"))
        >>> logger = logging.getLogger(__name__)
        >>> logger.addHandler(handler)
    """

    def __init__(
        self,
        *,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_context: bool = True,
        service_name: Optional[str] = None,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        extra_fields: Optional[Dict[str, str]] = None,
    ):
        """Initialize structured formatter.

        Args:
            include_timestamp: Include ISO timestamp in output
            include_level: Include log level information
            include_logger: Include logger metadata (name, module, function, line)
            include_context: Include correlation IDs and context variables
            service_name: Service name (defaults to SERVICE_NAME env var)
            environment: Environment name (defaults to ENVIRONMENT env var)
            version: Service version (defaults to SERVICE_VERSION env var)
            extra_fields: Additional static fields to include in all logs
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_context = include_context
        self.extra_fields = extra_fields or {}

        # Service information from environment or parameters
        self.service_name = service_name or os.getenv("SERVICE_NAME", "unknown")
        self.service_version = version or os.getenv("SERVICE_VERSION", "1.0.0")
        self.environment = environment or os.getenv("ENVIRONMENT", "development")

        # Get hostname
        try:
            import socket
            self.hostname = socket.gethostname()
        except Exception:
            self.hostname = os.getenv("HOSTNAME", "localhost")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry: Dict[str, Any] = {
            "message": record.getMessage(),
            "service": {
                "name": self.service_name,
                "version": self.service_version,
                "environment": self.environment,
                "hostname": self.hostname,
            },
        }

        # Add timestamp
        if self.include_timestamp:
            log_entry["@timestamp"] = datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat()

        # Add log level
        if self.include_level:
            log_entry["level"] = record.levelname
            log_entry["level_value"] = record.levelno

        # Add logger information
        if self.include_logger:
            log_entry["logger"] = {
                "name": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "file": record.pathname,
            }

        # Add context information
        if self.include_context:
            context: Dict[str, Any] = {}

            # Correlation and tracing IDs from context vars
            correlation_id = _correlation_id_var.get()
            if correlation_id:
                context["correlation_id"] = correlation_id

            trace_id = _trace_id_var.get()
            if trace_id:
                context["trace_id"] = trace_id

            span_id = _span_id_var.get()
            if span_id:
                context["span_id"] = span_id

            # Additional context from context var
            log_context = _context_var.get()
            if log_context:
                context.update(log_context)

            # Thread and process information
            context["thread"] = {"name": record.threadName, "id": record.thread}
            context["process"] = {"name": record.processName, "id": record.process}

            if context:
                log_entry["context"] = context

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record (custom fields passed via extra={})
        excluded_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "lineno", "funcName", "created", "msecs",
            "relativeCreated", "thread", "threadName", "processName", "process",
            "getMessage", "exc_info", "exc_text", "stack_info", "message",
        }

        for key, value in record.__dict__.items():
            if key not in excluded_keys:
                # Handle complex objects
                try:
                    if isinstance(value, (str, int, float, bool, type(None))):
                        log_entry[key] = value
                    elif isinstance(value, (list, dict)):
                        log_entry[key] = value
                    else:
                        log_entry[key] = str(value)
                except Exception:
                    log_entry[key] = f"<unserializable: {type(value).__name__}>"

        # Add configured extra fields
        for field_name, field_value in self.extra_fields.items():
            log_entry[field_name] = field_value

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class StructuredLogger:
    """Production-grade structured logger with JSON output and correlation tracking.

    Features:
    - JSON structured output for log aggregation systems
    - Automatic correlation ID injection from pydevkit if available
    - Context management for request/trace metadata
    - Performance tracking with duration measurement
    - Thread-safe and async-safe context propagation

    Example:
        >>> logger = StructuredLogger("my-service", service_name="api", environment="prod")
        >>> logger.info("User logged in", user_id="123", action="login")
        >>> with logger.context(request_id="req-456"):
        ...     logger.info("Processing request")
        >>> with logger.timing() as timer:
        ...     # do work
        ...     logger.info("Task completed", **timer.metrics())
    """

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
        """Initialize structured logger.

        Args:
            name: Logger name (typically module or component name)
            service_name: Service/application name for filtering
            environment: Deployment environment (dev, staging, prod)
            version: Application version
            level: Minimum log level
            output_stream: Output stream (defaults to stdout)
        """
        self.name = name
        self.service_name = service_name
        self.environment = environment
        self.version = version
        self.level = level
        self.output_stream = output_stream or sys.stdout

        # Try to import hostname
        try:
            import socket
            self.hostname = socket.gethostname()
        except Exception:
            self.hostname = None

    def _get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from context or pydevkit if available."""
        # Try context variable first
        correlation_id = _correlation_id_var.get()
        if correlation_id:
            return correlation_id

        # Try thread-local
        try:
            correlation_id = getattr(_thread_local, "correlation_id", None)
            if correlation_id:
                return correlation_id
        except AttributeError:
            pass

        # Try pydevkit if available
        try:
            from pydevkit.tracing.correlation_id import get_correlation_id
            correlation_id = get_correlation_id()
            if correlation_id:
                return correlation_id
        except ImportError:
            pass

        return None

    def _get_trace_context(self) -> tuple[Optional[str], Optional[str]]:
        """Get trace and span IDs from context."""
        trace_id = _trace_id_var.get()
        span_id = _span_id_var.get()

        # Fall back to thread-local
        if not trace_id:
            try:
                trace_id = getattr(_thread_local, "trace_id", None)
                span_id = getattr(_thread_local, "span_id", None)
            except AttributeError:
                pass

        return trace_id, span_id

    def _get_context(self) -> Dict[str, Any]:
        """Get current logging context."""
        context = _context_var.get()

        # Merge with thread-local context if available
        try:
            thread_context = getattr(_thread_local, "context", {})
            if thread_context:
                context = {**thread_context, **context}
        except AttributeError:
            pass

        return context

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on level."""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_order[level] >= level_order[self.level]

    def _log(
        self,
        level: LogLevel,
        message: str,
        *,
        exc_info: Optional[Exception] = None,
        duration_ms: Optional[float] = None,
        **extra: Any,
    ) -> None:
        """Internal logging method."""
        if not self._should_log(level):
            return

        trace_id, span_id = self._get_trace_context()

        # Build log record
        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            message=message,
            logger_name=self.name,
            correlation_id=self._get_correlation_id(),
            trace_id=trace_id,
            span_id=span_id,
            context=self._get_context(),
            extra=extra,
            service_name=self.service_name,
            environment=self.environment,
            version=self.version,
            hostname=self.hostname,
            duration_ms=duration_ms,
        )

        # Add exception info if provided
        if exc_info:
            import traceback
            record.exception = str(exc_info)
            record.exception_type = type(exc_info).__name__
            record.stack_trace = "".join(traceback.format_exception(
                type(exc_info), exc_info, exc_info.__traceback__
            ))

        # Output as JSON
        json_output = record.model_dump_json(exclude_none=True)
        self.output_stream.write(json_output + "\n")
        self.output_stream.flush()

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **extra)

    def error(
        self, message: str, *, exc_info: Optional[Exception] = None, **extra: Any
    ) -> None:
        """Log error message with optional exception info."""
        self._log(LogLevel.ERROR, message, exc_info=exc_info, **extra)

    def critical(
        self, message: str, *, exc_info: Optional[Exception] = None, **extra: Any
    ) -> None:
        """Log critical message with optional exception info."""
        self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **extra)

    def context(self, **context_data: Any) -> "LogContext":
        """Create a context manager that adds context to all logs within scope.

        Example:
            >>> with logger.context(request_id="123", user_id="456"):
            ...     logger.info("Processing")  # Will include request_id and user_id
        """
        return LogContext(**context_data)

    def timing(self, message: Optional[str] = None) -> "TimingContext":
        """Create a context manager for timing operations.

        Example:
            >>> with logger.timing("Database query") as timer:
            ...     # do work
            ...     pass
            >>> # Automatically logs duration on exit
        """
        return TimingContext(self, message)

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current context/thread."""
        _correlation_id_var.set(correlation_id)
        _thread_local.correlation_id = correlation_id

    def set_trace_context(self, trace_id: str, span_id: str) -> None:
        """Set trace context for current context/thread."""
        _trace_id_var.set(trace_id)
        _span_id_var.set(span_id)
        _thread_local.trace_id = trace_id
        _thread_local.span_id = span_id

    def clear_context(self) -> None:
        """Clear all context variables."""
        _correlation_id_var.set(None)
        _trace_id_var.set(None)
        _span_id_var.set(None)
        _context_var.set({})

        # Clear thread-local
        for attr in ["correlation_id", "trace_id", "span_id", "context"]:
            if hasattr(_thread_local, attr):
                delattr(_thread_local, attr)

    # Event-specific logging methods
    def audit(self, event: str, **extra: Any) -> None:
        """Log audit event.

        Audit logs track important actions for compliance and security.

        Example:
            >>> logger.audit("user_login", user_id="123", ip="192.168.1.1")
        """
        self._log(LogLevel.INFO, f"AUDIT: {event}", event_type="audit", **extra)

    def security(self, event: str, **extra: Any) -> None:
        """Log security event.

        Security logs track authentication, authorization, and security-related events.

        Example:
            >>> logger.security("failed_auth", user="admin", attempts=3)
        """
        self._log(LogLevel.WARNING, f"SECURITY: {event}", event_type="security", **extra)

    def business(self, event: str, **extra: Any) -> None:
        """Log business event.

        Business events track key business metrics and KPIs.

        Example:
            >>> logger.business("order_completed", order_id="ORD-123", amount=99.99)
        """
        self._log(LogLevel.INFO, f"BUSINESS: {event}", event_type="business", **extra)

    def performance(self, operation: str, duration: float, **extra: Any) -> None:
        """Log performance metric.

        Track operation performance and timing.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            **extra: Additional context

        Example:
            >>> logger.performance("database_query", 0.150, query="SELECT * FROM users")
        """
        self._log(
            LogLevel.INFO,
            f"PERFORMANCE: {operation} completed in {duration:.3f}s",
            event_type="performance",
            operation=operation,
            duration=duration,
            duration_ms=duration * 1000,
            **extra,
        )

    def request_start(self, method: str, path: str, **extra: Any) -> None:
        """Log HTTP request start.

        Example:
            >>> logger.request_start("GET", "/api/users")
        """
        self._log(
            LogLevel.INFO,
            f"Request started: {method} {path}",
            event_type="request_start",
            http_method=method,
            http_path=path,
            **extra,
        )

    def request_end(
        self, method: str, path: str, status_code: int, **extra: Any
    ) -> None:
        """Log HTTP request completion.

        Example:
            >>> logger.request_end("GET", "/api/users", 200, duration_ms=145.3)
        """
        self._log(
            LogLevel.INFO,
            f"Request completed: {method} {path} -> {status_code}",
            event_type="request_end",
            http_method=method,
            http_path=path,
            http_status=status_code,
            **extra,
        )

    def tool_call(self, tool_name: str, **extra: Any) -> None:
        """Log MCP tool call.

        Example:
            >>> logger.tool_call("execute_code", language="python")
        """
        self._log(
            LogLevel.INFO,
            f"Tool called: {tool_name}",
            event_type="tool_call",
            tool_name=tool_name,
            **extra,
        )

    def tool_result(
        self, tool_name: str, success: bool, duration: Optional[float] = None, **extra: Any
    ) -> None:
        """Log MCP tool result.

        Example:
            >>> logger.tool_result("execute_code", success=True, duration=0.523)
        """
        status = "success" if success else "error"
        message = f"Tool {status}: {tool_name}"
        if duration:
            message += f" ({duration:.3f}s)"

        level = LogLevel.INFO if success else LogLevel.ERROR
        self._log(
            level,
            message,
            event_type="tool_result",
            tool_name=tool_name,
            success=success,
            duration=duration,
            duration_ms=duration * 1000 if duration else None,
            **extra,
        )


class LogContext:
    """Context manager for scoped logging context."""

    def __init__(self, **context_data: Any):
        self.context_data = context_data
        self.previous_context: Optional[Dict[str, Any]] = None
        self.previous_thread_context: Optional[Dict[str, Any]] = None

    def __enter__(self) -> "LogContext":
        # Save previous context
        self.previous_context = _context_var.get()

        # Merge with new context
        new_context = {**self.previous_context, **self.context_data}
        _context_var.set(new_context)

        # Also set in thread-local
        try:
            self.previous_thread_context = getattr(_thread_local, "context", {})
            _thread_local.context = {**self.previous_thread_context, **self.context_data}
        except AttributeError:
            _thread_local.context = self.context_data

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self.previous_context is not None:
            _context_var.set(self.previous_context)

        if self.previous_thread_context is not None:
            _thread_local.context = self.previous_thread_context
        elif hasattr(_thread_local, "context"):
            delattr(_thread_local, "context")


class TimingContext:
    """Context manager for timing operations with automatic logging."""

    def __init__(self, logger: StructuredLogger, message: Optional[str] = None):
        self.logger = logger
        self.message = message
        self.start_time: Optional[float] = None
        self.duration_ms: Optional[float] = None

    def __enter__(self) -> "TimingContext":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.duration_ms = (time.perf_counter() - self.start_time) * 1000

            if self.message:
                self.logger.info(
                    self.message,
                    duration_ms=self.duration_ms,
                    success=exc_type is None,
                )

    def metrics(self) -> Dict[str, float]:
        """Get timing metrics for manual logging."""
        return {"duration_ms": self.duration_ms} if self.duration_ms else {}


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_global_correlation_id(correlation_id: str) -> None:
    """Set correlation ID globally for current context/thread."""
    _correlation_id_var.set(correlation_id)
    _thread_local.correlation_id = correlation_id

    # Also set in pydevkit if available
    try:
        from pydevkit.tracing.correlation_id import set_correlation_id
        set_correlation_id(correlation_id)
    except ImportError:
        pass
