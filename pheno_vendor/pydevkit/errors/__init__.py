"""Structured error handling utilities for PyDevKit."""

from .enhanced import (
    CircuitBreaker,
    ErrorHandler,
    ErrorSeverity,
    RetryConfig,
    StructuredError,
)
from .enhanced import (
    ErrorCategory as EnhancedErrorCategory,
)
from .enhanced import (
    ErrorContext as EnhancedErrorContext,
)
from .errors import ApiError, create_api_error_internal, normalize_error
from .handler import (
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    ValidationError,
    ZenMCPError,
)
from .handler import (
    ErrorCategory as BasicErrorCategory,
)
from .handler import (
    ErrorContext as BasicErrorContext,
)

# Backwards-compatible aliases
ErrorCategory = BasicErrorCategory
ErrorContext = BasicErrorContext

__all__ = [
    "ApiError",
    "create_api_error_internal",
    "normalize_error",
    "ZenMCPError",
    "NetworkError",
    "AuthenticationError",
    "ValidationError",
    "ConfigurationError",
    "ErrorCategory",
    "ErrorContext",
    "BasicErrorCategory",
    "BasicErrorContext",
    "StructuredError",
    "ErrorSeverity",
    "RetryConfig",
    "ErrorHandler",
    "CircuitBreaker",
    "EnhancedErrorCategory",
    "EnhancedErrorContext",
]
