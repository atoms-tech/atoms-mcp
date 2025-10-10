"""Correlation ID utilities for distributed tracing and request tracking.

This module provides correlation ID functionality for tracking requests
across multiple components, tools, and providers in the Zen MCP Server.
"""

import contextvars
import logging
import threading
import uuid

# Context variable for async correlation ID tracking
_correlation_id_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("correlation_id", default=None)

# Thread-local storage for sync correlation ID tracking
_thread_local = threading.local()

logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context/thread.

    Args:
        correlation_id: The correlation ID to set
    """
    # Set in async context
    _correlation_id_context.set(correlation_id)

    # Set in thread-local storage for sync contexts
    _thread_local.correlation_id = correlation_id

    logger.debug(f"Set correlation ID: {correlation_id}")


def get_correlation_id() -> str | None:
    """Get the correlation ID for the current context/thread.

    Returns:
        The current correlation ID or None if not set
    """
    # Try async context first
    try:
        correlation_id = _correlation_id_context.get()
        if correlation_id:
            return correlation_id
    except LookupError:
        pass

    # Fall back to thread-local storage
    try:
        return getattr(_thread_local, "correlation_id", None)
    except AttributeError:
        return None


def get_or_create_correlation_id() -> str:
    """Get the current correlation ID or create a new one if none exists.

    Returns:
        The current or newly created correlation ID
    """
    correlation_id = get_correlation_id()
    if not correlation_id:
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)

    return correlation_id


def clear_correlation_id() -> None:
    """Clear the correlation ID for the current context/thread."""
    # Clear async context
    _correlation_id_context.set(None)

    # Clear thread-local storage
    if hasattr(_thread_local, "correlation_id"):
        delattr(_thread_local, "correlation_id")

    logger.debug("Cleared correlation ID")


class CorrelationIdFilter(logging.Filter):
    """Logging filter to add correlation IDs to log records."""

    def filter(self, record):
        """Add correlation ID to log record if available."""
        correlation_id = get_correlation_id()
        record.correlation_id = correlation_id or "no-correlation-id"
        return True


def setup_correlation_logging():
    """Setup correlation ID logging for the root logger."""
    # Add correlation ID filter to all handlers
    root_logger = logging.getLogger()
    correlation_filter = CorrelationIdFilter()

    for handler in root_logger.handlers:
        handler.addFilter(correlation_filter)

    # Update log format to include correlation ID if not already present
    for handler in root_logger.handlers:
        if hasattr(handler, "formatter") and handler.formatter:
            current_format = handler.formatter._fmt
            if "correlation_id" not in current_format:
                # Add correlation ID to the format
                new_format = current_format.replace("%(message)s", "%(message)s [correlation_id=%(correlation_id)s]")
                handler.setFormatter(logging.Formatter(new_format))


# Context manager for scoped correlation IDs
class correlation_context:
    """Context manager for scoped correlation ID management."""

    def __init__(self, correlation_id: str | None = None):
        """Initialize context manager.

        Args:
            correlation_id: Specific correlation ID to use, or None to generate one
        """
        self.correlation_id = correlation_id or generate_correlation_id()
        self.previous_id = None

    def __enter__(self):
        """Enter the correlation context."""
        self.previous_id = get_correlation_id()
        set_correlation_id(self.correlation_id)
        return self.correlation_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the correlation context."""
        if self.previous_id:
            set_correlation_id(self.previous_id)
        else:
            clear_correlation_id()
