"""Unified Error Handler for Atoms MCP - Consistent error responses.

Provides centralized error handling with categorization, suggestions,
and recovery actions.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    SERVER = "server"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"


class ErrorHandler:
    """Unified error handler for consistent error responses."""

    # Error code mapping
    ERROR_CODES = {
        ErrorCategory.VALIDATION: 400,
        ErrorCategory.AUTHENTICATION: 401,
        ErrorCategory.AUTHORIZATION: 403,
        ErrorCategory.NOT_FOUND: 404,
        ErrorCategory.CONFLICT: 409,
        ErrorCategory.RATE_LIMIT: 429,
        ErrorCategory.SERVER: 500
    }

    @staticmethod
    def handle_error(
        error: Exception,
        category: ErrorCategory = ErrorCategory.SERVER,
        suggestions: Optional[List[str]] = None,
        recovery_actions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle error and return consistent response.
        
        Args:
            error: Exception that occurred
            category: Error category
            suggestions: Suggestions for fixing the error
            recovery_actions: Actions to recover from error
            context: Additional context
            
        Returns:
            Consistent error response dict
        """
        trace_id = str(uuid.uuid4())
        error_code = ErrorHandler.ERROR_CODES.get(category, 500)

        response = {
            "success": False,
            "error": str(error),
            "error_code": error_code,
            "error_category": category.value,
            "trace_id": trace_id,
            "suggestions": suggestions or [],
            "recovery_actions": recovery_actions or []
        }

        if context:
            response["context"] = context

        # Log error
        logger.error(
            f"Error [{trace_id}] ({category.value}): {error}",
            extra={"trace_id": trace_id, "category": category.value}
        )

        return response

    @staticmethod
    def validation_error(
        message: str,
        field: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create validation error response.
        
        Args:
            message: Error message
            field: Field that failed validation
            suggestions: Suggestions for fixing
            
        Returns:
            Validation error response
        """
        error = ValueError(message)
        context = {"field": field} if field else None
        
        return ErrorHandler.handle_error(
            error,
            category=ErrorCategory.VALIDATION,
            suggestions=suggestions or [f"Check {field} field" if field else "Check input"],
            context=context
        )

    @staticmethod
    def authentication_error(
        message: str = "Authentication failed",
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create authentication error response.
        
        Args:
            message: Error message
            suggestions: Suggestions for fixing
            
        Returns:
            Authentication error response
        """
        error = PermissionError(message)
        
        return ErrorHandler.handle_error(
            error,
            category=ErrorCategory.AUTHENTICATION,
            suggestions=suggestions or [
                "Verify authentication token is valid",
                "Check token expiration",
                "Re-authenticate if needed"
            ]
        )

    @staticmethod
    def authorization_error(
        message: str = "Permission denied",
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create authorization error response.
        
        Args:
            message: Error message
            suggestions: Suggestions for fixing
            
        Returns:
            Authorization error response
        """
        error = PermissionError(message)
        
        return ErrorHandler.handle_error(
            error,
            category=ErrorCategory.AUTHORIZATION,
            suggestions=suggestions or [
                "Check user permissions",
                "Verify workspace access",
                "Contact workspace admin"
            ]
        )

    @staticmethod
    def not_found_error(
        entity_type: str,
        entity_id: str,
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create not found error response.
        
        Args:
            entity_type: Type of entity not found
            entity_id: ID of entity not found
            suggestions: Suggestions for fixing
            
        Returns:
            Not found error response
        """
        message = f"{entity_type} with ID '{entity_id}' not found"
        error = KeyError(message)
        
        return ErrorHandler.handle_error(
            error,
            category=ErrorCategory.NOT_FOUND,
            suggestions=suggestions or [
                f"Verify {entity_type} ID is correct",
                f"List {entity_type}s to find correct ID",
                "Check if entity was deleted"
            ],
            context={"entity_type": entity_type, "entity_id": entity_id}
        )

    @staticmethod
    def conflict_error(
        message: str,
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create conflict error response.
        
        Args:
            message: Error message
            suggestions: Suggestions for fixing
            
        Returns:
            Conflict error response
        """
        error = ValueError(message)
        
        return ErrorHandler.handle_error(
            error,
            category=ErrorCategory.CONFLICT,
            suggestions=suggestions or [
                "Check for duplicate entries",
                "Verify entity state",
                "Retry operation"
            ]
        )

    @staticmethod
    def rate_limit_error(
        retry_after: int = 60,
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create rate limit error response.
        
        Args:
            retry_after: Seconds to wait before retry
            suggestions: Suggestions for fixing
            
        Returns:
            Rate limit error response
        """
        message = f"Rate limit exceeded. Retry after {retry_after} seconds"
        error = RuntimeError(message)
        
        response = ErrorHandler.handle_error(
            error,
            category=ErrorCategory.RATE_LIMIT,
            suggestions=suggestions or [
                f"Wait {retry_after} seconds before retrying",
                "Reduce request frequency",
                "Use batch operations"
            ]
        )
        
        response["retry_after"] = retry_after
        return response

    @staticmethod
    def server_error(
        message: str = "Internal server error",
        suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create server error response.
        
        Args:
            message: Error message
            suggestions: Suggestions for fixing
            
        Returns:
            Server error response
        """
        error = RuntimeError(message)
        
        return ErrorHandler.handle_error(
            error,
            category=ErrorCategory.SERVER,
            suggestions=suggestions or [
                "Try again later",
                "Contact support if problem persists",
                "Check system status"
            ]
        )


def get_error_handler() -> ErrorHandler:
    """Get error handler instance."""
    return ErrorHandler()

