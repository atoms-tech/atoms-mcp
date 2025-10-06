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


def normalize_error(err: Exception | str, fallback_message: str) -> ApiError:
    if isinstance(err, ApiError):
        return err
    if isinstance(err, Exception):
        error_str = str(err)

        # Check for permission denied errors (code 42501)
        if "permission denied" in error_str.lower() or "42501" in error_str:
            # Specific handling for tables without RLS policies
            if "test_req" in error_str or "properties" in error_str:
                table_name = "test_req" if "test_req" in error_str else "properties"
                return ApiError(
                    code="TABLE_ACCESS_RESTRICTED",
                    message=f"Access to {table_name} table is restricted. Either missing GRANT or RLS policy USING clause is blocking access.",
                    status=403,
                    details={
                        "cause": error_str,  # Show actual error, not repr
                        "hint": f"Run: GRANT SELECT ON {table_name} TO authenticated; OR fix RLS policy USING clause to allow org member access."
                    }
                )
            else:
                return ApiError(
                    code="PERMISSION_DENIED",
                    message=f"Permission denied: {error_str}",  # Show actual error
                    status=403,
                    details={"cause": error_str, "full_error": repr(err)}
                )

        # Transform common RLS errors into user-friendly messages
        if "row-level security policy" in error_str.lower():
            if "projects" in error_str:
                return ApiError(
                    code="UNAUTHORIZED_ORG_ACCESS",
                    message="You don't have permission to create projects in this organization. Please ensure you're a member of the organization first.",
                    status=403,
                    details={"cause": repr(err), "hint": "Use the workspace_tool to verify your organization membership or contact an organization owner."}
                )
            else:
                return ApiError(
                    code="UNAUTHORIZED_ACCESS",
                    message="You don't have permission to perform this action. Please check your organization membership.",
                    status=403,
                    details={"cause": repr(err)}
                )

        # Transform other common database errors
        if "unique constraint" in error_str.lower():
            return ApiError(
                code="DUPLICATE_ENTRY",
                message="An item with this identifier already exists.",
                status=409,
                details={"cause": repr(err)}
            )

        if "foreign key" in error_str.lower():
            return ApiError(
                code="INVALID_REFERENCE",
                message="Referenced item does not exist.",
                status=400,
                details={"cause": repr(err)}
            )

        return create_api_error_internal(error_str or fallback_message, details={"cause": repr(err)})
    return create_api_error_internal(fallback_message)

