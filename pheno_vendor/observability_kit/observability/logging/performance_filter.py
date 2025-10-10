"""Performance filter for tracking request and operation duration.

Provides automatic timing and performance metrics for structured logging.
"""

import contextvars
import datetime as dt
import logging
import time
from typing import Dict, Optional


# Context variable for tracking operation start times
_operation_start_times: contextvars.ContextVar[Dict[str, float]] = contextvars.ContextVar(
    "operation_start_times", default={}
)


class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records.

    This filter automatically tracks timing for operations and requests,
    adding duration information to log records.

    Features:
    - Automatic duration calculation for request/response pairs
    - Start time tracking per correlation ID
    - Performance metrics injection into log records
    - Configurable performance thresholds

    Example:
        >>> import logging
        >>> from observability.logging.structured import StructuredFormatter
        >>> from observability.logging.performance_filter import PerformanceFilter
        >>>
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(StructuredFormatter())
        >>> handler.addFilter(PerformanceFilter())
        >>> logger = logging.getLogger(__name__)
        >>> logger.addHandler(handler)
        >>>
        >>> # Log request start
        >>> logger.info("Request started", extra={"event_type": "request_start", "correlation_id": "123"})
        >>> # ... do work ...
        >>> # Log request end (duration automatically calculated)
        >>> logger.info("Request ended", extra={"event_type": "request_end", "correlation_id": "123"})
    """

    def __init__(
        self,
        *,
        slow_threshold_ms: Optional[float] = None,
        warn_threshold_ms: Optional[float] = None,
    ):
        """Initialize performance filter.

        Args:
            slow_threshold_ms: Add 'is_slow' flag if duration exceeds this (milliseconds)
            warn_threshold_ms: Upgrade log level to WARNING if duration exceeds this (milliseconds)
        """
        super().__init__()
        self.slow_threshold_ms = slow_threshold_ms
        self.warn_threshold_ms = warn_threshold_ms
        self.start_times: Dict[str, float] = {}

    def _get_correlation_id(self, record: logging.LogRecord) -> Optional[str]:
        """Extract correlation ID from log record."""
        # Try to get from extra attributes
        if hasattr(record, "correlation_id"):
            return record.correlation_id

        # Try to get from context
        if hasattr(record, "context") and isinstance(record.context, dict):
            return record.context.get("correlation_id")

        return None

    def _get_event_type(self, record: logging.LogRecord) -> Optional[str]:
        """Extract event type from log record."""
        if hasattr(record, "event_type"):
            return record.event_type
        return None

    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance context to log record.

        Args:
            record: Log record to filter

        Returns:
            True to allow the record to be logged
        """
        correlation_id = self._get_correlation_id(record)
        event_type = self._get_event_type(record)

        if not correlation_id or not event_type:
            return True

        # Track timing for start/end events
        if event_type in ("request_start", "operation_start"):
            # Record start time
            self.start_times[correlation_id] = time.perf_counter()
            record.timestamp_start = dt.datetime.now(dt.timezone.utc).isoformat()

        elif event_type in ("request_end", "operation_end") and correlation_id in self.start_times:
            # Calculate duration
            start_time = self.start_times.pop(correlation_id)
            duration_seconds = time.perf_counter() - start_time
            duration_ms = duration_seconds * 1000

            # Add duration to record
            record.duration = duration_seconds
            record.duration_ms = duration_ms
            record.timestamp_end = dt.datetime.now(dt.timezone.utc).isoformat()

            # Add performance flags
            if self.slow_threshold_ms and duration_ms >= self.slow_threshold_ms:
                record.is_slow = True

            # Upgrade log level for very slow operations
            if self.warn_threshold_ms and duration_ms >= self.warn_threshold_ms:
                record.levelno = logging.WARNING
                record.levelname = "WARNING"
                record.performance_warning = True

        return True

    def clear_stale_timers(self, max_age_seconds: float = 300) -> int:
        """Clear stale start times that were never completed.

        Args:
            max_age_seconds: Maximum age for a timer before considering it stale

        Returns:
            Number of stale timers cleared
        """
        current_time = time.perf_counter()
        stale_keys = [
            key
            for key, start_time in self.start_times.items()
            if (current_time - start_time) > max_age_seconds
        ]

        for key in stale_keys:
            del self.start_times[key]

        return len(stale_keys)


class OperationTimer:
    """Context manager for timing operations with automatic logging.

    This is a simpler alternative to using PerformanceFilter directly.

    Example:
        >>> with OperationTimer("database_query", logger=logger):
        ...     # do work
        ...     pass
    """

    def __init__(
        self,
        operation_name: str,
        *,
        logger: Optional[logging.Logger] = None,
        correlation_id: Optional[str] = None,
        **extra_context,
    ):
        """Initialize operation timer.

        Args:
            operation_name: Name of the operation being timed
            logger: Logger to use for timing logs
            correlation_id: Correlation ID for the operation
            **extra_context: Additional context to include in logs
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.correlation_id = correlation_id
        self.extra_context = extra_context
        self.start_time: Optional[float] = None
        self.duration_ms: Optional[float] = None

    def __enter__(self) -> "OperationTimer":
        """Start timing the operation."""
        self.start_time = time.perf_counter()

        # Log operation start
        self.logger.info(
            f"Operation started: {self.operation_name}",
            extra={
                "event_type": "operation_start",
                "operation": self.operation_name,
                "correlation_id": self.correlation_id,
                **self.extra_context,
            },
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log the operation completion."""
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.duration_ms = duration * 1000

            # Determine log level based on success/failure
            if exc_type is None:
                log_level = logging.INFO
                status = "completed"
            else:
                log_level = logging.ERROR
                status = "failed"

            # Log operation end
            self.logger.log(
                log_level,
                f"Operation {status}: {self.operation_name} ({self.duration_ms:.2f}ms)",
                extra={
                    "event_type": "operation_end",
                    "operation": self.operation_name,
                    "correlation_id": self.correlation_id,
                    "duration": duration,
                    "duration_ms": self.duration_ms,
                    "success": exc_type is None,
                    **self.extra_context,
                },
            )

    def get_duration_ms(self) -> Optional[float]:
        """Get the operation duration in milliseconds."""
        return self.duration_ms


def create_performance_filter(
    *,
    slow_threshold_ms: float = 1000,
    warn_threshold_ms: float = 5000,
) -> PerformanceFilter:
    """Factory function to create a configured performance filter.

    Args:
        slow_threshold_ms: Threshold for marking operations as slow (default: 1000ms)
        warn_threshold_ms: Threshold for upgrading to WARNING level (default: 5000ms)

    Returns:
        Configured PerformanceFilter instance

    Example:
        >>> filter = create_performance_filter(slow_threshold_ms=500)
        >>> handler.addFilter(filter)
    """
    return PerformanceFilter(
        slow_threshold_ms=slow_threshold_ms,
        warn_threshold_ms=warn_threshold_ms,
    )


__all__ = [
    "PerformanceFilter",
    "OperationTimer",
    "create_performance_filter",
]
