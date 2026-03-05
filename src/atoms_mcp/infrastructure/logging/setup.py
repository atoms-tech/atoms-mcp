"""
Logging setup and configuration.

This module provides centralized logging configuration using Python's
standard library logging module. Supports both text and JSON output,
file rotation, and context variables for request/user tracking.

No pheno-sdk dependencies - pure stdlib logging.
"""

import json
import logging
import logging.handlers
import sys
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config.settings import LogFormat, LogLevel, LoggingSettings

# Context variables for request/user tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
organization_id_var: ContextVar[Optional[str]] = ContextVar("organization_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs as JSON objects with timestamp, level, message,
    and any additional context fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string representation of the log record
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables if present
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        org_id = organization_id_var.get()
        if org_id:
            log_data["organization_id"] = org_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add caller information if requested
        if hasattr(record, "pathname") and hasattr(record, "lineno"):
            log_data["caller"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """
    Text log formatter with context variables.

    Formats logs in human-readable text format with optional
    timestamp, level, and caller information.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_caller: bool = False,
    ):
        """
        Initialize text formatter.

        Args:
            include_timestamp: Include timestamp in output
            include_caller: Include caller information (file, line)
        """
        self.include_timestamp = include_timestamp
        self.include_caller = include_caller

        # Build format string
        format_parts = []
        if include_timestamp:
            format_parts.append("%(asctime)s")
        format_parts.append("[%(levelname)s]")
        format_parts.append("%(name)s:")
        format_parts.append("%(message)s")

        if include_caller:
            format_parts.append("(%(pathname)s:%(lineno)d)")

        format_string = " ".join(format_parts)
        super().__init__(fmt=format_string, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as text.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        # Add context variables to message
        context_parts = []
        request_id = request_id_var.get()
        if request_id:
            context_parts.append(f"request_id={request_id}")

        user_id = user_id_var.get()
        if user_id:
            context_parts.append(f"user_id={user_id}")

        org_id = organization_id_var.get()
        if org_id:
            context_parts.append(f"org_id={org_id}")

        if context_parts:
            original_msg = record.getMessage()
            record.msg = f"{original_msg} [{', '.join(context_parts)}]"
            record.args = ()

        return super().format(record)


def setup_logging(config: LoggingSettings) -> None:
    """
    Configure application logging based on settings.

    Args:
        config: Logging configuration settings
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level.value)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter based on format setting
    if config.format == LogFormat.JSON:
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(
            include_timestamp=config.include_timestamp,
            include_caller=config.include_caller,
        )

    # Setup console handler if enabled
    if config.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(config.level.value)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Setup file handler if enabled
    if config.file_enabled:
        # Ensure log directory exists
        log_file = Path(config.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=config.file_max_bytes,
            backupCount=config.file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(config.level.value)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set third-party library log levels
    _configure_library_loggers(config.level)


def _configure_library_loggers(level: LogLevel) -> None:
    """
    Configure log levels for third-party libraries.

    Args:
        level: Global log level
    """
    # Reduce noise from verbose libraries
    library_loggers = {
        "httpx": logging.WARNING,
        "httpcore": logging.WARNING,
        "urllib3": logging.WARNING,
        "asyncio": logging.WARNING,
        "werkzeug": logging.WARNING,
        "google": logging.WARNING,
        "supabase": logging.INFO,
    }

    # If debug mode, show more library logs
    if level == LogLevel.DEBUG:
        library_loggers["supabase"] = logging.DEBUG
        library_loggers["httpx"] = logging.INFO

    for logger_name, logger_level in library_loggers.items():
        logging.getLogger(logger_name).setLevel(logger_level)


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> None:
    """
    Set context variables for the current request/operation.

    Args:
        request_id: Unique request identifier
        user_id: User identifier
        organization_id: Organization identifier
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if organization_id:
        organization_id_var.set(organization_id)


def clear_request_context() -> None:
    """Clear all request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
    organization_id_var.set(None)


def get_request_context() -> dict[str, Optional[str]]:
    """
    Get current request context.

    Returns:
        Dictionary with request_id, user_id, organization_id
    """
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
        "organization_id": organization_id_var.get(),
    }
