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
        return create_api_error_internal(str(err) or fallback_message, details={"cause": repr(err)})
    return create_api_error_internal(fallback_message)

