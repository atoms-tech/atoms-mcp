"""
Logger adapter implementing the domain logger port.

This module provides a concrete implementation of the Logger interface
using Python's standard library logging module with performance timing
and context management support.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

from ...domain.ports.logger import Logger


class StdLibLogger(Logger):
    """
    Logger adapter using Python stdlib logging.

    Implements the domain Logger interface using the standard library
    logging module with support for context scoping and performance timing.
    """

    def __init__(self, name: str = "atoms_mcp"):
        """
        Initialize logger adapter.

        Args:
            name: Logger name (typically module or component name)
        """
        self._logger = logging.getLogger(name)
        self._extra_fields: dict[str, Any] = {}

    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        extra = self._build_extra(kwargs)
        self._logger.debug(message, extra=extra)

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log an info message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        extra = self._build_extra(kwargs)
        self._logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log a warning message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        extra = self._build_extra(kwargs)
        self._logger.warning(message, extra=extra)

    def error(
        self, message: str, exception: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """
        Log an error message.

        Args:
            message: Log message
            exception: Optional exception that caused the error
            **kwargs: Additional context fields
        """
        extra = self._build_extra(kwargs)
        if exception:
            extra["exception_type"] = type(exception).__name__
            extra["exception_message"] = str(exception)

        self._logger.error(
            message,
            exc_info=exception is not None,
            extra=extra,
        )

    def critical(
        self, message: str, exception: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """
        Log a critical message.

        Args:
            message: Log message
            exception: Optional exception that caused the critical error
            **kwargs: Additional context fields
        """
        extra = self._build_extra(kwargs)
        if exception:
            extra["exception_type"] = type(exception).__name__
            extra["exception_message"] = str(exception)

        self._logger.critical(
            message,
            exc_info=exception is not None,
            extra=extra,
        )

    def _build_extra(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """
        Build extra fields dictionary for logging.

        Args:
            kwargs: Additional context fields

        Returns:
            Dictionary with extra_fields for log record
        """
        extra_fields = {**self._extra_fields, **kwargs}
        return {"extra_fields": extra_fields} if extra_fields else {}

    @contextmanager
    def context(self, **fields: Any) -> Generator[None, None, None]:
        """
        Context manager for scoped logging context.

        Example:
            with logger.context(user_id="123", operation="create"):
                logger.info("Processing request")  # includes context fields

        Args:
            **fields: Context fields to add to all log messages in scope

        Yields:
            None
        """
        # Save current context
        old_fields = self._extra_fields.copy()

        try:
            # Add new context fields
            self._extra_fields.update(fields)
            yield
        finally:
            # Restore previous context
            self._extra_fields = old_fields

    @contextmanager
    def timer(self, operation: str, **extra: Any) -> Generator[None, None, None]:
        """
        Context manager for timing operations.

        Example:
            with logger.timer("database_query", table="users"):
                # perform operation
                pass
            # Logs: "database_query completed in 0.123s"

        Args:
            operation: Name of the operation being timed
            **extra: Additional context fields

        Yields:
            None
        """
        start_time = time.perf_counter()
        self.debug(f"{operation} started", **extra)

        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.info(
                f"{operation} completed",
                duration_seconds=round(elapsed, 3),
                **extra,
            )

    def with_fields(self, **fields: Any) -> "StdLibLogger":
        """
        Create a new logger instance with additional persistent fields.

        Example:
            user_logger = logger.with_fields(user_id="123")
            user_logger.info("Action")  # always includes user_id

        Args:
            **fields: Fields to add to all log messages

        Returns:
            New logger instance with added fields
        """
        new_logger = StdLibLogger(self._logger.name)
        new_logger._logger = self._logger
        new_logger._extra_fields = {**self._extra_fields, **fields}
        return new_logger


def get_logger(name: str = "atoms_mcp") -> StdLibLogger:
    """
    Get a logger instance for the specified name.

    Args:
        name: Logger name (typically module or component name)

    Returns:
        Logger instance
    """
    return StdLibLogger(name)
