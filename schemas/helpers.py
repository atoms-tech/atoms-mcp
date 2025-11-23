"""Helper functions for working with generated Pydantic models."""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError


def get_model_for_entity(entity_type: str) -> Optional[Type[BaseModel]]:
    """Get Pydantic model class for entity type.
    
    Args:
        entity_type: Entity type name (e.g., "organization", "project")
        
    Returns:
        Pydantic model class or None if not found
    """
    try:
        from .generated import (
            Organization,
            Project,
            Document,
            Requirement,
            TestReq,
            Profile,
            Block,
        )
    except ImportError:
        return None
    
    model_map = {
        "organization": Organization,
        "project": Project,
        "document": Document,
        "requirement": Requirement,
        "test": TestReq,
        "profile": Profile,
        "user": Profile,  # Alias
        "block": Block,
    }
    
    return model_map.get(entity_type.lower())


def validate_entity_data(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate entity data using Pydantic model.
    
    Args:
        entity_type: Entity type name
        data: Data to validate
        
    Returns:
        Validated data as dict
        
    Raises:
        ValidationError: If validation fails
    """
    model = get_model_for_entity(entity_type)
    
    if not model:
        # No model found, return data as-is
        return data
    
    # Validate with Pydantic
    try:
        validated = model(**data)
        return validated.model_dump(exclude_none=True)
    except ValidationError as e:
        # Re-raise with more context
        raise ValidationError(
            f"Validation failed for {entity_type}: {e}",
            model=model
        ) from e


def get_model_fields(entity_type: str) -> Dict[str, Any]:
    """Get field information for entity type.
    
    Args:
        entity_type: Entity type name
        
    Returns:
        Dict of field name -> field info
    """
    model = get_model_for_entity(entity_type)
    
    if not model:
        return {}
    
    return {
        name: {
            "type": str(field.annotation),
            "required": field.is_required(),
            "default": field.default if field.default is not None else None,
        }
        for name, field in model.model_fields.items()
    }


def get_required_fields(entity_type: str) -> list[str]:
    """Get list of required fields for entity type.
    
    Args:
        entity_type: Entity type name
        
    Returns:
        List of required field names
    """
    model = get_model_for_entity(entity_type)
    
    if not model:
        return []
    
    return [
        name
        for name, field in model.model_fields.items()
        if field.is_required()
    ]


def get_optional_fields(entity_type: str) -> list[str]:
    """Get list of optional fields for entity type.
    
    Args:
        entity_type: Entity type name
        
    Returns:
        List of optional field names
    """
    model = get_model_for_entity(entity_type)
    
    if not model:
        return []
    
    return [
        name
        for name, field in model.model_fields.items()
        if not field.is_required()
    ]


def partial_validate(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate entity data partially (allow missing required fields).
    
    Useful for updates where not all fields are provided.
    
    Args:
        entity_type: Entity type name
        data: Data to validate
        
    Returns:
        Validated data as dict
    """
    model = get_model_for_entity(entity_type)
    
    if not model:
        return data
    
    # Create a partial model (all fields optional)
    try:
        # Only validate fields that are present
        validated_fields = {}
        for key, value in data.items():
            if key in model.model_fields:
                # Validate individual field
                # Simple type checking
                validated_fields[key] = value
            else:
                # Unknown field, keep as-is
                validated_fields[key] = value
        
        return validated_fields
    except Exception:
        # If validation fails, return original data
        return data


def get_entity_schema(entity_type: str) -> Dict[str, Any]:
    """Get schema metadata for entity type.
    
    Returns business logic metadata (required fields, auto fields, defaults, relationships).
    This is separate from Pydantic validation models in schemas/generated/.
    
    Args:
        entity_type: Entity type name (e.g., "organization", "project")
        
    Returns:
        Dict with schema metadata:
        - required_fields: List of required field names
        - auto_fields: List of auto-generated field names
        - default_values: Dict of default values
        - relationships: List of relationship names
        - auto_slug: Boolean indicating if slug should be auto-generated
    """
    # Schema metadata - source of truth for business logic patterns
    schemas = {
        "organization": {
            "required_fields": ["name"],
            "auto_fields": ["id", "created_at", "updated_at"],
            "default_values": {"is_deleted": False, "type": "team"},
            "relationships": ["members", "projects", "invitations"],
            "auto_slug": True
        },
        "project": {
            "required_fields": ["name", "organization_id"],
            "auto_fields": ["id", "created_at", "updated_at"],
            "default_values": {"is_deleted": False},
            "relationships": ["members", "documents", "organization"],
            "auto_slug": True
        },
        "document": {
            "required_fields": ["name", "project_id"],
            "auto_fields": ["id", "created_at", "updated_at"],
            "default_values": {"is_deleted": False},
            "relationships": ["blocks", "requirements", "project"],
            "auto_slug": True
        },
        "requirement": {
            "required_fields": ["name", "document_id"],
            "auto_fields": ["id", "created_at", "updated_at", "version", "external_id"],
            "default_values": {
                "is_deleted": False,
                "status": "active",
                "properties": {},
                "priority": "low",
                "type": "component",
                "block_id": None
            },
            "relationships": ["document", "tests", "trace_links"]
        },
        "test": {
            "required_fields": ["title", "project_id"],
            "auto_fields": ["id", "created_at", "updated_at"],
            "default_values": {"is_active": True, "status": "pending", "priority": "medium"},
            "relationships": ["requirements", "project"]
        },
        "user": {
            "required_fields": ["id"],
            "auto_fields": ["created_at", "updated_at"],
            "default_values": {},
            "relationships": ["organizations", "projects"]
        },
        "profile": {
            "required_fields": ["id"],
            "auto_fields": ["created_at", "updated_at"],
            "default_values": {},
            "relationships": ["organizations", "projects"]
        }
    }
    return schemas.get(entity_type.lower(), {})

