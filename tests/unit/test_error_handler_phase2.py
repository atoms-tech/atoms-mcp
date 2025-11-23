"""Unit tests for Phase 2 Week 2: Unified Error Handler.

Tests error categorization, suggestions, and recovery actions.
"""

import pytest
from services.error_handler import (
    ErrorHandler,
    ErrorCategory,
    get_error_handler
)


class TestErrorHandlerPhase2:
    """Test Phase 2 unified error handler."""

    def test_validation_error(self):
        """Test validation error response."""
        response = ErrorHandler.validation_error(
            "Invalid email format",
            field="email"
        )

        assert response["success"] is False
        assert response["error_code"] == 400
        assert response["error_category"] == "validation"
        assert "email" in response["context"]["field"]
        assert len(response["suggestions"]) > 0

    def test_authentication_error(self):
        """Test authentication error response."""
        response = ErrorHandler.authentication_error(
            "Invalid token"
        )

        assert response["success"] is False
        assert response["error_code"] == 401
        assert response["error_category"] == "authentication"
        assert len(response["suggestions"]) > 0

    def test_authorization_error(self):
        """Test authorization error response."""
        response = ErrorHandler.authorization_error(
            "User does not have permission"
        )

        assert response["success"] is False
        assert response["error_code"] == 403
        assert response["error_category"] == "authorization"
        assert len(response["suggestions"]) > 0

    def test_not_found_error(self):
        """Test not found error response."""
        response = ErrorHandler.not_found_error(
            entity_type="project",
            entity_id="proj-123"
        )

        assert response["success"] is False
        assert response["error_code"] == 404
        assert response["error_category"] == "not_found"
        assert response["context"]["entity_type"] == "project"
        assert response["context"]["entity_id"] == "proj-123"
        assert len(response["suggestions"]) > 0

    def test_conflict_error(self):
        """Test conflict error response."""
        response = ErrorHandler.conflict_error(
            "Entity already exists"
        )

        assert response["success"] is False
        assert response["error_code"] == 409
        assert response["error_category"] == "conflict"
        assert len(response["suggestions"]) > 0

    def test_rate_limit_error(self):
        """Test rate limit error response."""
        response = ErrorHandler.rate_limit_error(
            retry_after=60
        )

        assert response["success"] is False
        assert response["error_code"] == 429
        assert response["error_category"] == "rate_limit"
        assert response["retry_after"] == 60
        assert len(response["suggestions"]) > 0

    def test_server_error(self):
        """Test server error response."""
        response = ErrorHandler.server_error(
            "Database connection failed"
        )

        assert response["success"] is False
        assert response["error_code"] == 500
        assert response["error_category"] == "server"
        assert len(response["suggestions"]) > 0

    def test_error_has_trace_id(self):
        """Test error response includes trace ID."""
        response = ErrorHandler.validation_error("Test error")

        assert "trace_id" in response
        assert len(response["trace_id"]) > 0

    def test_error_has_suggestions(self):
        """Test error response includes suggestions."""
        response = ErrorHandler.not_found_error(
            entity_type="requirement",
            entity_id="req-1"
        )

        assert "suggestions" in response
        assert len(response["suggestions"]) > 0

    def test_error_has_recovery_actions(self):
        """Test error response includes recovery actions."""
        response = ErrorHandler.handle_error(
            Exception("Test error"),
            category=ErrorCategory.SERVER,
            recovery_actions=["Retry operation", "Contact support"]
        )

        assert "recovery_actions" in response
        assert len(response["recovery_actions"]) == 2

    def test_custom_suggestions(self):
        """Test custom suggestions in error response."""
        custom_suggestions = ["Check database", "Verify connection"]
        response = ErrorHandler.validation_error(
            "Invalid input",
            suggestions=custom_suggestions
        )

        assert response["suggestions"] == custom_suggestions

    def test_error_handler_static_methods(self):
        """Test error handler static methods are callable."""
        # ErrorHandler uses static methods, so we can call them directly
        response1 = ErrorHandler.validation_error("Test 1")
        response2 = ErrorHandler.validation_error("Test 2")

        # Both should return valid error responses
        assert response1["success"] is False
        assert response2["success"] is False
        assert response1["trace_id"] != response2["trace_id"]

    def test_error_response_structure(self):
        """Test error response has required fields."""
        response = ErrorHandler.validation_error("Test error")

        required_fields = [
            "success",
            "error",
            "error_code",
            "error_category",
            "trace_id",
            "suggestions",
            "recovery_actions"
        ]

        for field in required_fields:
            assert field in response

    def test_error_codes_mapping(self):
        """Test error codes are correctly mapped."""
        assert ErrorHandler.ERROR_CODES[ErrorCategory.VALIDATION] == 400
        assert ErrorHandler.ERROR_CODES[ErrorCategory.AUTHENTICATION] == 401
        assert ErrorHandler.ERROR_CODES[ErrorCategory.AUTHORIZATION] == 403
        assert ErrorHandler.ERROR_CODES[ErrorCategory.NOT_FOUND] == 404
        assert ErrorHandler.ERROR_CODES[ErrorCategory.CONFLICT] == 409
        assert ErrorHandler.ERROR_CODES[ErrorCategory.RATE_LIMIT] == 429
        assert ErrorHandler.ERROR_CODES[ErrorCategory.SERVER] == 500

