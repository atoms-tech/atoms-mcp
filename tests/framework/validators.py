"""
Response Validators

Provides validation helpers for test assertions.
"""

from typing import Any, Dict, List, Optional


class ResponseValidator:
    """Validates MCP tool responses."""

    @staticmethod
    def has_fields(response: Dict[str, Any], required_fields: List[str]) -> bool:
        """Check if response has all required fields."""
        if not isinstance(response, dict):
            return False
        return all(field in response for field in required_fields)

    @staticmethod
    def has_any_fields(response: Dict[str, Any], fields: List[str]) -> bool:
        """Check if response has any of the specified fields."""
        if not isinstance(response, dict):
            return False
        return any(field in response for field in fields)

    @staticmethod
    def validate_pagination(response: Dict[str, Any]) -> bool:
        """Validate pagination structure."""
        required = ["total", "limit", "offset"]
        return ResponseValidator.has_fields(response, required)

    @staticmethod
    def validate_list_response(response: Dict[str, Any], data_key: str = "data") -> bool:
        """Validate list response structure."""
        if not isinstance(response, dict):
            return False
        if data_key not in response:
            return False
        return isinstance(response[data_key], list)

    @staticmethod
    def validate_success_response(result: Dict[str, Any]) -> bool:
        """Validate standard success response."""
        return result.get("success", False) and result.get("error") is None


class FieldValidator:
    """Validates specific field types and values."""

    @staticmethod
    def is_uuid(value: Any) -> bool:
        """Check if value is a valid UUID string."""
        if not isinstance(value, str):
            return False
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value, re.IGNORECASE))

    @staticmethod
    def is_iso_timestamp(value: Any) -> bool:
        """Check if value is ISO 8601 timestamp."""
        if not isinstance(value, str):
            return False
        try:
            from datetime import datetime
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except:
            return False

    @staticmethod
    def is_in_range(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
        """Check if value is within range."""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except:
            return False

    @staticmethod
    def extract_id(response: Dict[str, Any]) -> Optional[str]:
        """Extract ID from response, handling multiple formats.
        
        Handles:
        - {"id": "..."}
        - {"data": {"id": "..."}}
        """
        if not isinstance(response, dict):
            return None
        
        # Direct id field
        if "id" in response:
            return response["id"]
        
        # Nested in data
        if "data" in response and isinstance(response["data"], dict):
            return response["data"].get("id")
        
        return None
