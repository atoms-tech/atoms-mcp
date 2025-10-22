"""
Production-ready structured logging with correlation IDs and context injection.

This module provides comprehensive logging capabilities including:
- Structured JSON logging for machine parsing
- Correlation ID tracking across requests
- Automatic context injection (user, session, request)
- Performance tracking integrated with logs
- Log level filtering and formatting
- Thread-safe operation

Author: Atoms MCP Platform
Version: 1.0.0
"""

import json
import logging
import sys
import time
import traceback
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

# Context variables for request tracking
correlation_id_var: ContextVar[str | None] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[str | None] = ContextVar('user_id', default=None)
session_id_var: ContextVar[str | None] = ContextVar('session_id', default=None)
request_path_var: ContextVar[str | None] = ContextVar('request_path', default=None)


class LogLevel(str, Enum):
    """Standard log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PerformanceMetric:
    """Track performance metrics within log context."""

    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = time.perf_counter()
        self.end_time: float | None = None
        self.duration_ms: float | None = None
        self.metadata: dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the performance metric."""
        self.metadata[key] = value

    def stop(self) -> float:
        """Stop timing and return duration in milliseconds."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        return self.duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "start_time": self.start_time,
            "end_time": self.end_time,
            **self.metadata
        }


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(
        self,
        include_context: bool = True,
        include_stack_trace: bool = True,
        timestamp_format: str = "iso8601"
    ):
        super().__init__()
        self.include_context = include_context
        self.include_stack_trace = include_stack_trace
        self.timestamp_format = timestamp_format

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log structure
        log_data: dict[str, Any] = {
            "timestamp": self._format_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation and context data
        if self.include_context:
            context = self._get_context()
            if context:
                log_data["context"] = context

        # Add exception information
        if record.exc_info and self.include_stack_trace:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": self._format_exception(record.exc_info)
            }

        # Add custom fields from extra
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add performance metrics if present
        if hasattr(record, 'performance'):
            log_data["performance"] = record.performance

        return json.dumps(log_data, default=str)

    def _format_timestamp(self, created: float) -> str:
        """Format timestamp according to configuration."""
        dt = datetime.fromtimestamp(created)
        if self.timestamp_format == "iso8601":
            return dt.isoformat()
        elif self.timestamp_format == "unix":
            return str(created)
        else:
            return dt.strftime(self.timestamp_format)

    def _get_context(self) -> dict[str, Any]:
        """Extract context from context variables."""
        context = {}

        correlation_id = correlation_id_var.get()
        if correlation_id:
            context["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            context["user_id"] = user_id

        session_id = session_id_var.get()
        if session_id:
            context["session_id"] = session_id

        request_path = request_path_var.get()
        if request_path:
            context["request_path"] = request_path

        return context

    def _format_exception(self, exc_info) -> list[str]:
        """Format exception stack trace."""
        return traceback.format_exception(*exc_info)


class AtomLogger:
    """
    Enhanced logger with structured logging and context awareness.

    Features:
    - Automatic context injection from ContextVars
    - Performance tracking integration
    - Structured JSON output
    - Thread-safe operation
    - Extra fields support
    """

    def __init__(
        self,
        name: str,
        level: str | LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = False,
        log_file_path: Path | None = None,
        json_format: bool = True
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_level(level))
        self.logger.handlers.clear()  # Clear existing handlers

        # Configure formatters
        if json_format:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if enable_file and log_file_path:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _get_level(self, level: str | LogLevel) -> int:
        """Convert log level to logging constant."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        level_str = level.value if isinstance(level, LogLevel) else level
        return level_map.get(level_str.upper(), logging.INFO)

    def _log(
        self,
        level: int,
        message: str,
        extra_fields: dict[str, Any] | None = None,
        performance: PerformanceMetric | None = None,
        exc_info: bool = False
    ) -> None:
        """Internal logging method with extra fields support."""
        extra = {}
        if extra_fields:
            extra['extra_fields'] = extra_fields
        if performance:
            extra['performance'] = performance.to_dict()

        self.logger.log(level, message, exc_info=exc_info, extra=extra)

    def debug(
        self,
        message: str,
        extra_fields: dict[str, Any] | None = None,
        performance: PerformanceMetric | None = None
    ) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, extra_fields, performance)

    def info(
        self,
        message: str,
        extra_fields: dict[str, Any] | None = None,
        performance: PerformanceMetric | None = None
    ) -> None:
        """Log info message."""
        self._log(logging.INFO, message, extra_fields, performance)

    def warning(
        self,
        message: str,
        extra_fields: dict[str, Any] | None = None,
        performance: PerformanceMetric | None = None
    ) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, extra_fields, performance)

    def error(
        self,
        message: str,
        extra_fields: dict[str, Any] | None = None,
        performance: PerformanceMetric | None = None,
        exc_info: bool = False
    ) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, extra_fields, performance, exc_info)

    def critical(
        self,
        message: str,
        extra_fields: dict[str, Any] | None = None,
        performance: PerformanceMetric | None = None,
        exc_info: bool = False
    ) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, extra_fields, performance, exc_info)

    def exception(
        self,
        message: str,
        extra_fields: dict[str, Any] | None = None
    ) -> None:
        """Log exception with stack trace."""
        self._log(logging.ERROR, message, extra_fields, exc_info=True)


class LogContext:
    """Context manager for setting log context variables."""

    def __init__(
        self,
        correlation_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        request_path: str | None = None,
        auto_generate_correlation_id: bool = True
    ):
        self.correlation_id = correlation_id or (str(uuid4()) if auto_generate_correlation_id else None)
        self.user_id = user_id
        self.session_id = session_id
        self.request_path = request_path

        # Store previous values for restoration
        self._prev_correlation_id = None
        self._prev_user_id = None
        self._prev_session_id = None
        self._prev_request_path = None

    def __enter__(self):
        """Set context variables."""
        self._prev_correlation_id = correlation_id_var.get()
        self._prev_user_id = user_id_var.get()
        self._prev_session_id = session_id_var.get()
        self._prev_request_path = request_path_var.get()

        if self.correlation_id:
            correlation_id_var.set(self.correlation_id)
        if self.user_id:
            user_id_var.set(self.user_id)
        if self.session_id:
            session_id_var.set(self.session_id)
        if self.request_path:
            request_path_var.set(self.request_path)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous context variables."""
        correlation_id_var.set(self._prev_correlation_id)
        user_id_var.set(self._prev_user_id)
        session_id_var.set(self._prev_session_id)
        request_path_var.set(self._prev_request_path)


def get_logger(
    name: str,
    level: str | LogLevel = LogLevel.INFO,
    json_format: bool = True
) -> AtomLogger:
    """
    Factory function to create a configured logger.

    Args:
        name: Logger name (typically module name)
        level: Logging level
        json_format: Whether to use JSON formatting

    Returns:
        Configured AtomLogger instance
    """
    return AtomLogger(
        name=name,
        level=level,
        enable_console=True,
        enable_file=False,
        json_format=json_format
    )


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    """Get correlation ID from current context."""
    return correlation_id_var.get()


def set_user_context(user_id: str, session_id: str | None = None) -> None:
    """Set user context for current request."""
    user_id_var.set(user_id)
    if session_id:
        session_id_var.set(session_id)


def set_request_path(path: str) -> None:
    """Set request path for current context."""
    request_path_var.set(path)


def clear_context() -> None:
    """Clear all context variables."""
    correlation_id_var.set(None)
    user_id_var.set(None)
    session_id_var.set(None)
    request_path_var.set(None)


# Default logger instance
default_logger = get_logger("atoms.observability")
