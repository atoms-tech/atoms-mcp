"""
JSON encoder/decoder for domain models.

This module provides custom JSON serialization for domain objects,
DTOs, enums, datetime, UUID, and other common types.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


class DomainJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for domain models and common types.

    Handles serialization of:
    - UUID
    - datetime/date
    - Enum
    - Decimal
    - Path
    - dataclasses
    - Pydantic models
    - Sets
    """

    def default(self, obj: Any) -> Any:
        """
        Convert object to JSON-serializable type.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        # UUID
        if isinstance(obj, UUID):
            return str(obj)

        # datetime/date
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()

        # Enum
        if isinstance(obj, Enum):
            return obj.value

        # Decimal
        if isinstance(obj, Decimal):
            return float(obj)

        # Path
        if isinstance(obj, Path):
            return str(obj)

        # Set
        if isinstance(obj, set):
            return list(obj)

        # Pydantic models (have dict() method)
        if hasattr(obj, "dict") and callable(obj.dict):
            return obj.dict()

        # Pydantic v2 models (have model_dump() method)
        if hasattr(obj, "model_dump") and callable(obj.model_dump):
            return obj.model_dump()

        # dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            return {
                field: getattr(obj, field)
                for field in obj.__dataclass_fields__
            }

        # Objects with to_dict() method
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()

        # Objects with __dict__
        if hasattr(obj, "__dict__"):
            return obj.__dict__

        # Fall back to default behavior
        return super().default(obj)


def dumps(obj: Any, **kwargs: Any) -> str:
    """
    Serialize object to JSON string.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string
    """
    return json.dumps(obj, cls=DomainJSONEncoder, **kwargs)


def dumps_pretty(obj: Any, **kwargs: Any) -> str:
    """
    Serialize object to formatted JSON string.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        Formatted JSON string
    """
    return json.dumps(obj, cls=DomainJSONEncoder, indent=2, **kwargs)


def loads(s: str, **kwargs: Any) -> Any:
    """
    Deserialize JSON string to object.

    Args:
        s: JSON string
        **kwargs: Additional arguments for json.loads

    Returns:
        Deserialized object
    """
    return json.loads(s, **kwargs)


def safe_dumps(obj: Any, fallback: str = "null", **kwargs: Any) -> str:
    """
    Safely serialize object to JSON string with fallback.

    If serialization fails, returns fallback value instead of raising.

    Args:
        obj: Object to serialize
        fallback: Fallback value if serialization fails
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string or fallback
    """
    try:
        return dumps(obj, **kwargs)
    except (TypeError, ValueError):
        return fallback


def safe_loads(s: str, fallback: Any = None, **kwargs: Any) -> Any:
    """
    Safely deserialize JSON string with fallback.

    If deserialization fails, returns fallback value instead of raising.

    Args:
        s: JSON string
        fallback: Fallback value if deserialization fails
        **kwargs: Additional arguments for json.loads

    Returns:
        Deserialized object or fallback
    """
    try:
        return loads(s, **kwargs)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def serialize_for_cache(obj: Any) -> str:
    """
    Serialize object for cache storage.

    Args:
        obj: Object to serialize

    Returns:
        JSON string suitable for caching
    """
    return dumps(obj)


def deserialize_from_cache(s: str) -> Any:
    """
    Deserialize object from cache storage.

    Args:
        s: JSON string from cache

    Returns:
        Deserialized object
    """
    return loads(s)


def is_json(s: str) -> bool:
    """
    Check if string is valid JSON.

    Args:
        s: String to check

    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(s)
        return True
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
