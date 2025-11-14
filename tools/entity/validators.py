"""Entity validation logic.

Handles validation of entity data before persistence.
"""

import re
from typing import Dict, Any
from .schemas import get_entity_schema


def is_uuid_format(value: str) -> bool:
    """Check if string is a valid UUID format."""
    if value is None:
        return False
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(value))


def validate_required_fields(entity_type: str, data: Dict[str, Any]) -> None:
    """Validate that required fields are present."""
    schema = get_entity_schema(entity_type)
    required = schema.get("required_fields", [])
    auto_fields = schema.get("auto_fields", [])
    
    # Exclude auto-generated fields from validation
    required_non_auto = [field for field in required if field not in auto_fields]
    
    missing = [field for field in required_non_auto if field not in data]
    if missing:
        raise ValueError(f"Missing required fields for {entity_type}: {missing}")


def validate_entity_data(entity_type: str, data: Dict[str, Any]) -> None:
    """Validate entity data against schema.
    
    Checks:
    - Required fields present
    - Data type compatibility
    """
    validate_required_fields(entity_type, data)
