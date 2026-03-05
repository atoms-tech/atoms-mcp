"""
Application exceptions with error codes and serialization.

This module defines the exception hierarchy for the application,
including error codes, structured messages, and JSON serialization
for error responses.
"""

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    """Error code enumeration for categorizing exceptions."""

    # General errors (1000-1099)
    UNKNOWN_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    CONFIGURATION_ERROR = "ERR_1002"
    INTERNAL_ERROR = "ERR_1003"

    # Entity errors (1100-1199)
    ENTITY_NOT_FOUND = "ERR_1100"
    ENTITY_ALREADY_EXISTS = "ERR_1101"
    ENTITY_INVALID_STATE = "ERR_1102"

    # Relationship errors (1200-1299)
    RELATIONSHIP_NOT_FOUND = "ERR_1200"
    RELATIONSHIP_CONFLICT = "ERR_1201"
    RELATIONSHIP_INVALID_TYPE = "ERR_1202"
    CIRCULAR_DEPENDENCY = "ERR_1203"

    # Repository errors (1300-1399)
    REPOSITORY_ERROR = "ERR_1300"
    DATABASE_CONNECTION_ERROR = "ERR_1301"
    QUERY_ERROR = "ERR_1302"
    TRANSACTION_ERROR = "ERR_1303"

    # Cache errors (1400-1499)
    CACHE_ERROR = "ERR_1400"
    CACHE_CONNECTION_ERROR = "ERR_1401"
    CACHE_SERIALIZATION_ERROR = "ERR_1402"

    # Workflow errors (1500-1599)
    WORKFLOW_ERROR = "ERR_1500"
    WORKFLOW_NOT_FOUND = "ERR_1501"
    WORKFLOW_EXECUTION_ERROR = "ERR_1502"
    WORKFLOW_VALIDATION_ERROR = "ERR_1503"

    # Authentication/Authorization errors (1600-1699)
    AUTHENTICATION_ERROR = "ERR_1600"
    AUTHORIZATION_ERROR = "ERR_1601"
    TOKEN_EXPIRED = "ERR_1602"
    INVALID_CREDENTIALS = "ERR_1603"


class ApplicationException(Exception):
    """
    Base exception for all application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and serialization.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize application exception.

        Args:
            message: Human-readable error message
            error_code: Categorized error code
            details: Additional error details (no sensitive data)
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize exception to dictionary.

        Returns:
            Dictionary representation of the exception
        """
        result: dict[str, Any] = {
            "error": True,
            "error_code": self.error_code.value,
            "message": self.message,
        }

        if self.details:
            result["details"] = self.details

        if self.cause:
            result["cause_type"] = type(self.cause).__name__
            # Don't include full cause message to avoid leaking sensitive info
            result["cause"] = str(self.cause)[:200]  # Truncate

        return result

    def __str__(self) -> str:
        """String representation of the exception."""
        base = f"[{self.error_code.value}] {self.message}"
        if self.details:
            base += f" (details: {self.details})"
        return base


class ValidationException(ApplicationException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize validation exception.

        Args:
            message: Validation error message
            field: Field name that failed validation
            value: Invalid value (sanitized)
            details: Additional validation details
        """
        validation_details = details or {}
        if field:
            validation_details["field"] = field
        if value is not None:
            # Sanitize value to avoid leaking sensitive data
            validation_details["value"] = str(value)[:100]

        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=validation_details,
        )


class EntityNotFoundException(ApplicationException):
    """Exception raised when an entity is not found."""

    def __init__(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize entity not found exception.

        Args:
            entity_type: Type of entity (e.g., "organization", "project")
            entity_id: Entity identifier (if known)
            details: Additional details
        """
        message = f"{entity_type} not found"
        if entity_id:
            message += f": {entity_id}"

        entity_details = details or {}
        entity_details["entity_type"] = entity_type
        if entity_id:
            entity_details["entity_id"] = entity_id

        super().__init__(
            message=message,
            error_code=ErrorCode.ENTITY_NOT_FOUND,
            details=entity_details,
        )


class RelationshipConflictException(ApplicationException):
    """Exception raised when a relationship operation conflicts with existing state."""

    def __init__(
        self,
        relationship_type: str,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        conflict_reason: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize relationship conflict exception.

        Args:
            relationship_type: Type of relationship
            source_id: Source entity ID
            target_id: Target entity ID
            conflict_reason: Reason for the conflict
            details: Additional details
        """
        message = f"Relationship conflict: {relationship_type}"
        if conflict_reason:
            message += f" - {conflict_reason}"

        conflict_details = details or {}
        conflict_details["relationship_type"] = relationship_type
        if source_id:
            conflict_details["source_id"] = source_id
        if target_id:
            conflict_details["target_id"] = target_id

        super().__init__(
            message=message,
            error_code=ErrorCode.RELATIONSHIP_CONFLICT,
            details=conflict_details,
        )


class RepositoryException(ApplicationException):
    """Exception raised for repository/database errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        entity_type: Optional[str] = None,
        cause: Optional[Exception] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize repository exception.

        Args:
            message: Error message
            operation: Database operation (e.g., "create", "update", "delete")
            entity_type: Type of entity being operated on
            cause: Original exception
            details: Additional details
        """
        repo_details = details or {}
        if operation:
            repo_details["operation"] = operation
        if entity_type:
            repo_details["entity_type"] = entity_type

        super().__init__(
            message=message,
            error_code=ErrorCode.REPOSITORY_ERROR,
            details=repo_details,
            cause=cause,
        )


class CacheException(ApplicationException):
    """Exception raised for cache errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        cause: Optional[Exception] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize cache exception.

        Args:
            message: Error message
            operation: Cache operation (e.g., "get", "set", "delete")
            key: Cache key
            cause: Original exception
            details: Additional details
        """
        cache_details = details or {}
        if operation:
            cache_details["operation"] = operation
        if key:
            cache_details["key"] = key

        super().__init__(
            message=message,
            error_code=ErrorCode.CACHE_ERROR,
            details=cache_details,
            cause=cause,
        )


class WorkflowException(ApplicationException):
    """Exception raised for workflow execution errors."""

    def __init__(
        self,
        message: str,
        workflow_name: Optional[str] = None,
        step: Optional[str] = None,
        cause: Optional[Exception] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize workflow exception.

        Args:
            message: Error message
            workflow_name: Name of the workflow
            step: Current workflow step
            cause: Original exception
            details: Additional details
        """
        workflow_details = details or {}
        if workflow_name:
            workflow_details["workflow_name"] = workflow_name
        if step:
            workflow_details["step"] = step

        super().__init__(
            message=message,
            error_code=ErrorCode.WORKFLOW_ERROR,
            details=workflow_details,
            cause=cause,
        )


class ConfigurationException(ApplicationException):
    """Exception raised for configuration errors."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize configuration exception.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
            details: Additional details
        """
        config_details = details or {}
        if config_key:
            config_details["config_key"] = config_key

        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details=config_details,
        )
