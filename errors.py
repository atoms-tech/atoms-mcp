from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiError(Exception):
    code: str
    message: str
    status: int = 500
    details: Any | None = None

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code}: {self.message}"


def create_api_error_internal(message: str, details: Any | None = None) -> ApiError:
    return ApiError(code="INTERNAL_SERVER_ERROR", message=message, status=500, details=details)


# PostgreSQL error code mappings
POSTGRES_ERRORS = {
    "23514": ("CHECK_CONSTRAINT", "Validation rule failed", 400),
    "23505": ("UNIQUE_CONSTRAINT", "Duplicate value", 409),
    "23503": ("FOREIGN_KEY", "Referenced item not found", 400),
    "23502": ("NOT_NULL", "Required field missing", 400),
    "42501": ("PERMISSION_DENIED", "Permission denied", 403),
}


def normalize_error(err: Exception | str, fallback_message: str) -> ApiError:
    """Normalize exceptions to ApiError with simplified error handling."""
    if isinstance(err, ApiError):
        return err

    if not isinstance(err, Exception):
        return create_api_error_internal(fallback_message)

    error_str = str(err)

    # Check PostgreSQL error codes
    for code, (error_type, message, status) in POSTGRES_ERRORS.items():
        if code in error_str:
            return ApiError(code=error_type, message=message, status=status, details={"error": error_str})

    # Check for RLS policy violations
    if "row-level security" in error_str.lower():
        message = "Permission denied. Check your organization membership."
        if "projects" in error_str:
            message = "You don't have permission to access this organization."
        return ApiError(code="UNAUTHORIZED_ACCESS", message=message, status=403)

    # Default to internal server error
    return create_api_error_internal(error_str or fallback_message, details={"error": error_str})

