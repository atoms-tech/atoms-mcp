"""Entity schema definitions.

Defines the structure and metadata for all entity types in the system.
"""

from typing import Dict, Any


def get_entity_schema(entity_type: str) -> Dict[str, Any]:
    """Get schema information for entity type.

    Uses manual schemas which define auto_slug and other logic.
    Pydantic models are strict and don't understand our auto-generation patterns.
    """
    # Manual schemas - source of truth for our auto-generation patterns
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
