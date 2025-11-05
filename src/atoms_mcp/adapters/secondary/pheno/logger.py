"""
Pheno logger adapter.

This module provides an adapter for Pheno's logging system that
conforms to the standard logging interface.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

try:
    from pheno.core.logging import PhenoLogger

    PHENO_LOGGING_AVAILABLE = True
except ImportError:
    PHENO_LOGGING_AVAILABLE = False
    PhenoLogger = None


class PhenoLoggerAdapter(logging.Logger):
    """
    Adapter that wraps Pheno logger to work with standard logging interface.

    This adapter allows Pheno logging to be used transparently in place
    of standard library logging.
    """

    def __init__(self, name: str, level: Optional[str] = None) -> None:
        """
        Initialize Pheno logger adapter.

        Args:
            name: Logger name
            level: Optional log level
        """
        super().__init__(name)

        if not PHENO_LOGGING_AVAILABLE or not PhenoLogger:
            raise RuntimeError("Pheno logging is not available")

        # Create Pheno logger instance
        self._pheno_logger = PhenoLogger(name)

        # Set level if provided
        if level:
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.setLevel(log_level)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Log debug message.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Additional context fields
        """
        if self.isEnabledFor(logging.DEBUG):
            formatted_msg = msg % args if args else msg
            context = {k: v for k, v in kwargs.items() if not k.startswith("_")}
            self._pheno_logger.debug(formatted_msg, **context)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Log info message.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Additional context fields
        """
        if self.isEnabledFor(logging.INFO):
            formatted_msg = msg % args if args else msg
            context = {k: v for k, v in kwargs.items() if not k.startswith("_")}
            self._pheno_logger.info(formatted_msg, **context)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Log warning message.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Additional context fields
        """
        if self.isEnabledFor(logging.WARNING):
            formatted_msg = msg % args if args else msg
            context = {k: v for k, v in kwargs.items() if not k.startswith("_")}
            self._pheno_logger.warning(formatted_msg, **context)

    def error(
        self, msg: str, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """
        Log error message.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            exc_info: Include exception info
            **kwargs: Additional context fields
        """
        if self.isEnabledFor(logging.ERROR):
            formatted_msg = msg % args if args else msg
            context = {k: v for k, v in kwargs.items() if not k.startswith("_")}

            if exc_info:
                import sys
                import traceback

                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_value:
                    context["exception"] = str(exc_value)
                    context["traceback"] = "".join(
                        traceback.format_tb(exc_traceback)
                    )

            self._pheno_logger.error(formatted_msg, **context)

    def critical(
        self, msg: str, *args: Any, exc_info: bool = False, **kwargs: Any
    ) -> None:
        """
        Log critical message.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            exc_info: Include exception info
            **kwargs: Additional context fields
        """
        if self.isEnabledFor(logging.CRITICAL):
            formatted_msg = msg % args if args else msg
            context = {k: v for k, v in kwargs.items() if not k.startswith("_")}

            if exc_info:
                import sys
                import traceback

                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_value:
                    context["exception"] = str(exc_value)
                    context["traceback"] = "".join(
                        traceback.format_tb(exc_traceback)
                    )

            self._pheno_logger.critical(formatted_msg, **context)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Log exception with traceback.

        Args:
            msg: Message to log
            *args: Positional arguments for message formatting
            **kwargs: Additional context fields
        """
        self.error(msg, *args, exc_info=True, **kwargs)
