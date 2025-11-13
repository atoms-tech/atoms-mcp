"""Input validation and sanitization for security."""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class InputValidator:
    """Validate and sanitize user inputs to prevent injection attacks."""

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(;|--|#|/\*|\*/)",  # SQL control characters
        r"\b(DROP|DELETE|INSERT|UPDATE|UNION|SELECT|TRUNCATE)\b",
        r"xp_\w+",  # SQL Server extended procs
        r"sp_\w+",  # SQL Server stored procs
        r"'\s*(OR|AND)\s*'",  # OR/AND with quotes
        r'"\s*(OR|AND)\s*"',  # Double quote OR/AND injection
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    # Field length limits by type
    FIELD_LENGTHS = {
        "name": 255,
        "title": 500,
        "description": 5000,
        "content": 50000,
        "email": 255,
        "url": 2000,
        "id": 100,
        "slug": 100,
        "status": 50,
    }

    # Allowed characters for IDs/slugs
    ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    URL_PATTERN = re.compile(r"^https?://[^\s]+$")

    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        max_length: Optional[int] = None,
        allow_empty: bool = False,
        allow_html: bool = False,
    ) -> str:
        """Validate and sanitize string fields.

        Args:
            value: Value to validate
            field_name: Field name for error messages
            max_length: Maximum length (uses defaults if not provided)
            allow_empty: Whether empty strings are allowed
            allow_html: Whether HTML/JS is allowed (dangerous)

        Returns:
            Sanitized string

        Raises:
            ValueError: If validation fails
            TypeError: If value is wrong type
        """
        if value is None:
            if allow_empty:
                return ""
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string, got {type(value).__name__}")

        # Remove leading/trailing whitespace
        value = value.strip()

        # Check empty
        if not value and not allow_empty:
            raise ValueError(f"{field_name} cannot be empty")

        # Check length
        if max_length is None:
            max_length = InputValidator.FIELD_LENGTHS.get(field_name.lower(), 1000)

        if len(value) > max_length:
            raise ValueError(
                f"{field_name} exceeds maximum length {max_length} (got {len(value)})"
            )

        # Check for SQL injection
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError(
                    f"{field_name} contains potentially dangerous SQL characters"
                )

        # Check for XSS
        if not allow_html:
            for pattern in InputValidator.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValueError(
                        f"{field_name} contains potentially dangerous HTML/JS characters"
                    )

        # Check for null bytes
        if "\x00" in value:
            raise ValueError(f"{field_name} contains invalid null bytes")

        return value

    @staticmethod
    def validate_id(value: Any, field_name: str = "id") -> str:
        """Validate ID field (UUID or alphanumeric slug).

        Args:
            value: Value to validate
            field_name: Field name for error messages

        Returns:
            Validated ID

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string, got {type(value).__name__}")

        value = value.strip()

        # UUID format or slug format
        if not InputValidator.ID_PATTERN.match(value):
            raise ValueError(
                f"{field_name} contains invalid characters (must be alphanumeric, dash, underscore)"
            )

        if len(value) < 1 or len(value) > 100:
            raise ValueError(f"{field_name} invalid length (must be 1-100 characters)")

        return value

    @staticmethod
    def validate_email(value: Any, field_name: str = "email") -> str:
        """Validate email address.

        Args:
            value: Value to validate
            field_name: Field name for error messages

        Returns:
            Validated email

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        value = value.strip().lower()

        if not InputValidator.EMAIL_PATTERN.match(value):
            raise ValueError(f"{field_name} is not a valid email address")

        if len(value) > 255:
            raise ValueError(f"{field_name} exceeds maximum length 255")

        return value

    @staticmethod
    def validate_url(value: Any, field_name: str = "url") -> str:
        """Validate URL.

        Args:
            value: Value to validate
            field_name: Field name for error messages

        Returns:
            Validated URL

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        value = value.strip()

        if not InputValidator.URL_PATTERN.match(value):
            raise ValueError(f"{field_name} is not a valid URL (must start with http:// or https://)")

        if len(value) > 2000:
            raise ValueError(f"{field_name} exceeds maximum length 2000")

        return value

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_val: int = 0,
        max_val: int = 1000000,
    ) -> int:
        """Validate integer fields.

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be an integer, got {type(value).__name__}")

        if int_val < min_val or int_val > max_val:
            raise ValueError(
                f"{field_name} out of range [{min_val}, {max_val}] (got {int_val})"
            )

        return int_val

    @staticmethod
    def validate_boolean(value: Any, field_name: str = "boolean") -> bool:
        """Validate boolean fields.

        Args:
            value: Value to validate
            field_name: Field name for error messages

        Returns:
            Validated boolean

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            if value.lower() in ("false", "0", "no", "off"):
                return False

        if isinstance(value, int):
            if value == 1:
                return True
            if value == 0:
                return False

        raise ValueError(f"{field_name} must be a boolean, got {type(value).__name__}")

    @staticmethod
    def validate_enum(
        value: Any,
        field_name: str,
        allowed_values: List[str],
    ) -> str:
        """Validate enum/choice fields.

        Args:
            value: Value to validate
            field_name: Field name for error messages
            allowed_values: List of allowed values

        Returns:
            Validated enum value

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        value = value.strip()

        if value not in allowed_values:
            raise ValueError(
                f"{field_name} must be one of {allowed_values}, got '{value}'"
            )

        return value

    @staticmethod
    def validate_dict(
        value: Any,
        field_name: str,
        required_keys: Optional[List[str]] = None,
        allowed_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate dictionary/JSON fields.

        Args:
            value: Value to validate
            field_name: Field name for error messages
            required_keys: List of required keys
            allowed_keys: Whitelist of allowed keys

        Returns:
            Validated dictionary

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, dict):
            raise TypeError(f"{field_name} must be a dictionary")

        required_keys = required_keys or []
        allowed_keys = allowed_keys or list(value.keys())

        # Check required keys
        missing = set(required_keys) - set(value.keys())
        if missing:
            raise ValueError(
                f"{field_name} missing required keys: {missing}"
            )

        # Check for unknown keys
        unknown = set(value.keys()) - set(allowed_keys)
        if unknown:
            raise ValueError(
                f"{field_name} contains unknown keys: {unknown}"
            )

        return value

    @staticmethod
    def validate_list(
        value: Any,
        field_name: str,
        min_items: int = 0,
        max_items: int = 1000,
    ) -> List[Any]:
        """Validate list fields.

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_items: Minimum number of items
            max_items: Maximum number of items

        Returns:
            Validated list

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        if not isinstance(value, list):
            raise TypeError(f"{field_name} must be a list")

        if len(value) < min_items:
            raise ValueError(
                f"{field_name} has too few items (min {min_items}, got {len(value)})"
            )

        if len(value) > max_items:
            raise ValueError(
                f"{field_name} has too many items (max {max_items}, got {len(value)})"
            )

        return value


def validate_entity_data(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize entity creation/update data.

    Args:
        entity_type: Type of entity
        data: Entity data to validate

    Returns:
        Validated and sanitized data

    Raises:
        ValueError: If validation fails
    """
    validated = {}

    # Sanitize common fields
    if "name" in data:
        validated["name"] = InputValidator.validate_string(
            data["name"], "name", max_length=255
        )

    if "title" in data:
        validated["title"] = InputValidator.validate_string(
            data["title"], "title", max_length=500
        )

    if "description" in data:
        validated["description"] = InputValidator.validate_string(
            data["description"], "description", max_length=5000, allow_html=False
        )

    if "status" in data:
        status_values = ["draft", "active", "archived", "deleted", "pending", "review"]
        validated["status"] = InputValidator.validate_enum(
            data["status"], "status", status_values
        )

    if "priority" in data:
        priority_values = ["low", "medium", "high", "critical"]
        validated["priority"] = InputValidator.validate_enum(
            data["priority"], "priority", priority_values
        )

    if "email" in data:
        validated["email"] = InputValidator.validate_email(data["email"])

    if "external_id" in data and data["external_id"]:
        validated["external_id"] = InputValidator.validate_id(
            data["external_id"], "external_id"
        )

    # Pass through validated fields without modification
    for key in data:
        if key not in validated:
            validated[key] = data[key]

    return validated
