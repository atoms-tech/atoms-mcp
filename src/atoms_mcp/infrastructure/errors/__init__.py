"""Error handling module."""

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
from .handlers import (
    create_error_response,
    exception_to_http_status,
    handle_application_exception,
    handle_generic_exception,
    log_exception,
)

__all__ = [
    # Exceptions
    "ApplicationException",
    "CacheException",
    "ConfigurationException",
    "EntityNotFoundException",
    "ErrorCode",
    "RelationshipConflictException",
    "RepositoryException",
    "ValidationException",
    "WorkflowException",
    # Handlers
    "create_error_response",
    "exception_to_http_status",
    "handle_application_exception",
    "handle_generic_exception",
    "log_exception",
]
