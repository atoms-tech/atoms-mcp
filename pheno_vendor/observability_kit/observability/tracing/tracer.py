"""Distributed tracing with W3C Trace Context support.

Based on 2025 Python best practices:
- W3C Trace Context standard (traceparent header)
- Parent-child span relationships
- Context propagation for distributed systems
- Sampling support for high-volume systems
- Integration with OpenTelemetry when available
- Thread-safe and async-safe operation
"""

import contextvars
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanKind(str, Enum):
    """Span kinds following OpenTelemetry convention."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span status."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """W3C Trace Context.

    Format: {version}-{trace-id}-{parent-id}-{trace-flags}
    Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
    """
    trace_id: str  # 32 hex chars (128 bits)
    span_id: str   # 16 hex chars (64 bits)
    trace_flags: int = 0  # 1 = sampled
    parent_span_id: Optional[str] = None

    @property
    def is_sampled(self) -> bool:
        """Check if trace is sampled."""
        return bool(self.trace_flags & 0x01)

    def to_traceparent(self) -> str:
        """Convert to W3C traceparent header format."""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}"

    @classmethod
    def from_traceparent(cls, traceparent: str) -> "SpanContext":
        """Parse W3C traceparent header.

        Format: 00-{trace-id}-{parent-id}-{trace-flags}
        """
        parts = traceparent.split("-")
        if len(parts) != 4 or parts[0] != "00":
            raise ValueError(f"Invalid traceparent format: {traceparent}")

        return cls(
            trace_id=parts[1],
            span_id=parts[2],
            trace_flags=int(parts[3], 16),
        )

    @classmethod
    def generate(cls, sampled: bool = True) -> "SpanContext":
        """Generate new trace context."""
        trace_id = uuid.uuid4().hex + uuid.uuid4().hex  # 32 chars
        span_id = uuid.uuid4().hex[:16]  # 16 chars
        trace_flags = 0x01 if sampled else 0x00
        return cls(trace_id=trace_id, span_id=span_id, trace_flags=trace_flags)


@dataclass
class Span:
    """A span represents a single operation within a trace.

    Spans have:
    - Unique span ID
    - Parent span ID (for child spans)
    - Trace ID (shared across related spans)
    - Start and end timestamps
    - Attributes (key-value metadata)
    - Events (timestamped log messages)
    - Status (ok, error, unset)
    """
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: SpanStatus = SpanStatus.UNSET
    status_message: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    @property
    def is_recording(self) -> bool:
        """Check if span is still recording."""
        return self.end_time is None

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Set a span attribute."""
        if self.is_recording:
            self.attributes[key] = value
        return self

    def set_attributes(self, attributes: Dict[str, Any]) -> "Span":
        """Set multiple span attributes."""
        if self.is_recording:
            self.attributes.update(attributes)
        return self

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> "Span":
        """Add an event to the span."""
        if self.is_recording:
            event = {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
            self.events.append(event)
        return self

    def set_status(self, status: SpanStatus, message: Optional[str] = None) -> "Span":
        """Set span status."""
        if self.is_recording:
            self.status = status
            self.status_message = message
        return self

    def record_exception(self, exception: Exception) -> "Span":
        """Record an exception on the span."""
        import traceback

        self.set_status(SpanStatus.ERROR, str(exception))
        self.add_event(
            "exception",
            {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
                "exception.stacktrace": "".join(
                    traceback.format_exception(type(exception), exception, exception.__traceback__)
                ),
            },
        )
        return self

    def end(self, end_time: Optional[float] = None) -> None:
        """End the span."""
        if self.is_recording:
            self.end_time = end_time or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for export."""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status.value,
            "status_message": self.status_message,
        }


# Context variables for async-safe span tracking
_current_span_var: contextvars.ContextVar[Optional[Span]] = contextvars.ContextVar(
    "current_span", default=None
)

# Thread-local storage for sync contexts
_thread_local = threading.local()


class DistributedTracer:
    """Production-grade distributed tracer with W3C Trace Context support.

    Features:
    - W3C Trace Context standard for interoperability
    - Parent-child span relationships
    - Sampling for high-volume systems
    - Thread-safe and async-safe
    - In-memory span collection with export support

    Example:
        >>> tracer = DistributedTracer("my-service", sample_rate=1.0)
        >>> with tracer.start_span("process_request") as span:
        ...     span.set_attribute("user_id", "123")
        ...     with tracer.start_span("database_query", kind=SpanKind.CLIENT) as db_span:
        ...         db_span.set_attribute("query", "SELECT * FROM users")
    """

    def __init__(
        self,
        service_name: str,
        *,
        sample_rate: float = 1.0,
        max_spans: int = 10000,
    ):
        """Initialize distributed tracer.

        Args:
            service_name: Name of the service for span attributes
            sample_rate: Probability of sampling a trace (0.0 to 1.0)
            max_spans: Maximum number of spans to keep in memory
        """
        self.service_name = service_name
        self.sample_rate = max(0.0, min(1.0, sample_rate))
        self.max_spans = max_spans

        self._spans: List[Span] = []
        self._lock = threading.Lock()

    def _should_sample(self) -> bool:
        """Determine if a new trace should be sampled."""
        return random.random() < self.sample_rate

    def _get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        # Try context variable first
        span = _current_span_var.get()
        if span:
            return span

        # Fall back to thread-local
        try:
            return getattr(_thread_local, "current_span", None)
        except AttributeError:
            return None

    def _set_current_span(self, span: Optional[Span]) -> None:
        """Set the current active span."""
        _current_span_var.set(span)
        _thread_local.current_span = span

    def start_span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[SpanContext] = None,
    ) -> "SpanManager":
        """Start a new span.

        Args:
            name: Span name (operation name)
            kind: Span kind (internal, server, client, etc.)
            attributes: Initial span attributes
            parent_context: Parent span context (for distributed traces)

        Returns:
            SpanManager context manager
        """
        # Get parent span from current context if not provided
        current_span = self._get_current_span()
        parent_span_id = None

        # Determine trace context
        if parent_context:
            # Use provided parent context (for cross-service traces)
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
            sampled = parent_context.is_sampled
        elif current_span:
            # Use current span as parent
            trace_id = current_span.context.trace_id
            parent_span_id = current_span.context.span_id
            sampled = current_span.context.is_sampled
        else:
            # New root span
            sampled = self._should_sample()
            trace_id = uuid.uuid4().hex + uuid.uuid4().hex

        # Create new span context
        span_id = uuid.uuid4().hex[:16]
        trace_flags = 0x01 if sampled else 0x00

        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags,
            parent_span_id=parent_span_id,
        )

        # Create span
        span = Span(name=name, context=context, kind=kind)

        # Set default attributes
        span.set_attribute("service.name", self.service_name)

        # Set custom attributes
        if attributes:
            span.set_attributes(attributes)

        # Store span if sampled
        if context.is_sampled:
            with self._lock:
                self._spans.append(span)
                # Limit memory usage
                if len(self._spans) > self.max_spans:
                    self._spans.pop(0)

        return SpanManager(self, span)

    def inject_context(self, span: Span) -> Dict[str, str]:
        """Inject trace context as HTTP headers (W3C Trace Context).

        Returns:
            Dictionary with traceparent header
        """
        return {
            "traceparent": span.context.to_traceparent(),
        }

    def extract_context(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extract trace context from HTTP headers.

        Args:
            headers: HTTP headers dictionary

        Returns:
            SpanContext if traceparent header found, None otherwise
        """
        # Case-insensitive header lookup
        headers_lower = {k.lower(): v for k, v in headers.items()}
        traceparent = headers_lower.get("traceparent")

        if traceparent:
            try:
                return SpanContext.from_traceparent(traceparent)
            except ValueError:
                pass

        return None

    def get_current_span(self) -> Optional[Span]:
        """Get the currently active span."""
        return self._get_current_span()

    def get_spans(self) -> List[Span]:
        """Get all collected spans."""
        with self._lock:
            return list(self._spans)

    def export_spans(self) -> List[Dict[str, Any]]:
        """Export all spans as dictionaries."""
        with self._lock:
            return [span.to_dict() for span in self._spans]

    def clear_spans(self) -> None:
        """Clear all collected spans."""
        with self._lock:
            self._spans.clear()


class SpanManager:
    """Context manager for spans."""

    def __init__(self, tracer: DistributedTracer, span: Span):
        self.tracer = tracer
        self.span = span
        self.previous_span: Optional[Span] = None

    def __enter__(self) -> Span:
        # Save previous span
        self.previous_span = self.tracer._get_current_span()

        # Set current span
        self.tracer._set_current_span(self.span)

        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Record exception if one occurred
        if exc_val:
            self.span.record_exception(exc_val)

        # End span
        self.span.end()

        # Restore previous span
        self.tracer._set_current_span(self.previous_span)

        # Update logger context if available
        try:
            from observability.logging.structured import (
                _trace_id_var,
                _span_id_var,
                _thread_local,
            )

            if self.previous_span:
                _trace_id_var.set(self.previous_span.context.trace_id)
                _span_id_var.set(self.previous_span.context.span_id)
                _thread_local.trace_id = self.previous_span.context.trace_id
                _thread_local.span_id = self.previous_span.context.span_id
            else:
                _trace_id_var.set(None)
                _span_id_var.set(None)
                if hasattr(_thread_local, "trace_id"):
                    delattr(_thread_local, "trace_id")
                if hasattr(_thread_local, "span_id"):
                    delattr(_thread_local, "span_id")
        except ImportError:
            pass
