"""
Abstract logger interface (port).

This module defines the logger interface that infrastructure
implementations must satisfy. Pure ABC with no external dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Logger(ABC):
    """
    Abstract base class for logging.

    Loggers provide a standard interface for recording application events
    without coupling the domain to specific logging implementations.
    """

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log an info message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log a warning message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
