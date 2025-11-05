"""
Error handlers for FastAPI/FastMCP integration.

This module provides error handler functions that convert domain
exceptions into HTTP responses with proper status codes and secure
error messages (no sensitive data leakage).
"""

import traceback
from typing import Any, Optional

from .exceptions import (
    ApplicationException,
    CacheException,
    ConfigurationException,
    EntityNotFoundException,
    ErrorCode,
    RelationshipConflictException,
    RepositoryException,
    ValidationException,
    WorkflowException,
)


def exception_to_http_status(error_code: ErrorCode) -> int:
    """
    Map error code to HTTP status code.

    Args:
        error_code: Application error code

    Returns:
        HTTP status code
    """
    status_map = {
        ErrorCode.VALIDATION_ERROR: 400,
        ErrorCode.ENTITY_NOT_FOUND: 404,
        ErrorCode.RELATIONSHIP_NOT_FOUND: 404,
        ErrorCode.WORKFLOW_NOT_FOUND: 404,
        ErrorCode.ENTITY_ALREADY_EXISTS: 409,
        ErrorCode.RELATIONSHIP_CONFLICT: 409,
        ErrorCode.CIRCULAR_DEPENDENCY: 409,
        ErrorCode.AUTHENTICATION_ERROR: 401,
        ErrorCode.AUTHORIZATION_ERROR: 403,
        ErrorCode.TOKEN_EXPIRED: 401,
        ErrorCode.INVALID_CREDENTIALS: 401,
        ErrorCode.CONFIGURATION_ERROR: 500,
        ErrorCode.REPOSITORY_ERROR: 500,
        ErrorCode.DATABASE_CONNECTION_ERROR: 503,
        ErrorCode.CACHE_ERROR: 500,
        ErrorCode.CACHE_CONNECTION_ERROR: 503,
        ErrorCode.WORKFLOW_ERROR: 500,
        ErrorCode.WORKFLOW_EXECUTION_ERROR: 500,
        ErrorCode.INTERNAL_ERROR: 500,
    }
    return status_map.get(error_code, 500)


def handle_application_exception(
    exc: ApplicationException,
    include_traceback: bool = False,
) -> dict[str, Any]:
    """
    Handle application exception and convert to error response.

    Args:
        exc: Application exception
        include_traceback: Include stack trace (only for debugging)

    Returns:
        Error response dictionary
    """
    response = {
        "error": True,
        "error_code": exc.error_code.value,
        "message": exc.message,
        "status_code": exception_to_http_status(exc.error_code),
    }

    # Include sanitized details (no sensitive data)
    if exc.details:
        response["details"] = _sanitize_details(exc.details)

    # Include traceback only in debug mode
    if include_traceback:
        response["traceback"] = traceback.format_exc()

    return response


def handle_generic_exception(
    exc: Exception,
    include_traceback: bool = False,
) -> dict[str, Any]:
    """
    Handle generic exception and convert to error response.

    Args:
        exc: Generic exception
        include_traceback: Include stack trace (only for debugging)

    Returns:
        Error response dictionary
    """
    # Don't leak internal error details in production
    message = "An internal error occurred"
    error_code = ErrorCode.INTERNAL_ERROR

    response = {
        "error": True,
        "error_code": error_code.value,
        "message": message,
        "status_code": 500,
    }

    # Include traceback only in debug mode
    if include_traceback:
        response["traceback"] = traceback.format_exc()
        response["exception_type"] = type(exc).__name__
        response["exception_message"] = str(exc)

    return response


def _sanitize_details(details: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize error details to prevent sensitive data leakage.

    Args:
        details: Original details dictionary

    Returns:
        Sanitized details dictionary
    """
    # List of keys that should never be included in error responses
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "api_key",
        "private_key",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "session",
    }

    sanitized = {}
    for key, value in details.items():
        # Check if key contains sensitive information
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        # Truncate long strings
        elif isinstance(value, str) and len(value) > 500:
            sanitized[key] = value[:500] + "..."
        # Recursively sanitize nested dictionaries
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_details(value)
        else:
            sanitized[key] = value

    return sanitized


def log_exception(
    exc: Exception,
    logger: Optional[Any] = None,
    context: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log exception with context information.

    Args:
        exc: Exception to log
        logger: Logger instance (if available)
        context: Additional context for logging
    """
    if logger is None:
        # If no logger provided, use Python's built-in logging
        import logging
        logger = logging.getLogger("atoms_mcp.errors")

    context = context or {}

    if isinstance(exc, ApplicationException):
        logger.error(
            f"Application error: {exc.message}",
            exception=exc,
            error_code=exc.error_code.value,
            details=exc.details,
            **context,
        )
    else:
        logger.error(
            f"Unexpected error: {type(exc).__name__}",
            exception=exc,
            **context,
        )


def create_error_response(
    message: str,
    error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    details: Optional[dict[str, Any]] = None,
    status_code: Optional[int] = None,
) -> dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        message: Error message
        error_code: Error code
        details: Additional details
        status_code: HTTP status code (auto-determined if not provided)

    Returns:
        Error response dictionary
    """
    response = {
        "error": True,
        "error_code": error_code.value,
        "message": message,
        "status_code": status_code or exception_to_http_status(error_code),
    }

    if details:
        response["details"] = _sanitize_details(details)

    return response
