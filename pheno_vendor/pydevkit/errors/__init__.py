"""Structured error handling utilities for PyDevKit."""

from .errors import ApiError, create_api_error_internal, normalize_error
from .handler import (
    ZenMCPError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    ConfigurationError,
    ErrorCategory as BasicErrorCategory,
    ErrorContext as BasicErrorContext,
)
from .enhanced import (
    StructuredError,
    ErrorSeverity,
    RetryConfig,
    ErrorHandler,
    CircuitBreaker,
    ErrorCategory as EnhancedErrorCategory,
    ErrorContext as EnhancedErrorContext,
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
