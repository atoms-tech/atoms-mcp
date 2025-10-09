"""
Schema validation utilities to ensure MCP data strictly matches database schema.

This module provides validation functions that enforce:
- Correct field names and types
- Valid enum values matching database enums
- Required field presence
- Field constraints (e.g., slug format, UUID format)
"""

import re
from typing import Any, Dict, List, Set
from uuid import UUID

from schemas.enums import (
    OrganizationType,
    EntityStatus,
    Priority,
    TestStatus,
    MemberRole,
    InvitationStatus,
)
from schemas.constants import REQUIRED_FIELDS, ENTITY_TABLE_MAP, Fields


class ValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


class SchemaValidator:
    """Validates entity data against database schema constraints."""

    # Regex patterns matching database constraints
    SLUG_PATTERN = re.compile(r'^[a-z][a-z0-9-]*$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

    @staticmethod
    def validate_uuid(value: str, field_name: str) -> None:
        """Validate UUID format."""
        if not SchemaValidator.UUID_PATTERN.match(value):
            raise ValidationError(f"{field_name} must be a valid UUID, got: {value}")

    @staticmethod
    def validate_slug(value: str) -> None:
        """Validate slug format: starts with letter, contains only lowercase letters, numbers, hyphens."""
        if not SchemaValidator.SLUG_PATTERN.match(value):
            raise ValidationError(
                f"Slug must match pattern ^[a-z][a-z0-9-]*$ (start with letter, "
                f"only lowercase letters/numbers/hyphens), got: {value}"
            )

    @staticmethod
    def validate_organization_type(value: str) -> None:
        """Validate organization type matches database enum."""
        try:
            OrganizationType(value)
        except ValueError:
            valid_values = [t.value for t in OrganizationType]
            raise ValidationError(
                f"Invalid organization type: '{value}'. "
                f"Must be one of: {valid_values}. "
                f"Note: 'business' is NOT a valid type in the database."
            )

    @staticmethod
    def validate_entity_status(value: str) -> None:
        """Validate entity status matches allowed values."""
        try:
            EntityStatus(value)
        except ValueError:
            valid_values = [s.value for s in EntityStatus]
            raise ValidationError(
                f"Invalid entity status: '{value}'. Must be one of: {valid_values}"
            )

    @staticmethod
    def validate_priority(value: str) -> None:
        """Validate priority matches allowed values."""
        try:
            Priority(value)
        except ValueError:
            valid_values = [p.value for p in Priority]
            raise ValidationError(
                f"Invalid priority: '{value}'. Must be one of: {valid_values}"
            )

    @staticmethod
    def validate_test_status(value: str) -> None:
        """Validate test status matches allowed values."""
        try:
            TestStatus(value)
        except ValueError:
            valid_values = [s.value for s in TestStatus]
            raise ValidationError(
                f"Invalid test status: '{value}'. Must be one of: {valid_values}"
            )

    @staticmethod
    def validate_required_fields(entity_type: str, data: Dict[str, Any]) -> None:
        """Validate all required fields are present."""
        required = REQUIRED_FIELDS.get(entity_type, set())
        missing = required - set(data.keys())

        if missing:
            raise ValidationError(
                f"Missing required fields for {entity_type}: {missing}"
            )

    @staticmethod
    def validate_organization_data(data: Dict[str, Any]) -> None:
        """Validate organization data matches database schema."""
        # Required fields
        SchemaValidator.validate_required_fields("organization", data)

        # Slug format
        if "slug" in data:
            SchemaValidator.validate_slug(data["slug"])

        # Organization type enum
        if "type" in data:
            SchemaValidator.validate_organization_type(data["type"])

        # UUID fields
        if "id" in data and data["id"]:
            SchemaValidator.validate_uuid(data["id"], "id")

    @staticmethod
    def validate_project_data(data: Dict[str, Any]) -> None:
        """Validate project data matches database schema."""
        SchemaValidator.validate_required_fields("project", data)

        # UUID fields
        if "organization_id" in data:
            SchemaValidator.validate_uuid(data["organization_id"], "organization_id")
        if "id" in data and data["id"]:
            SchemaValidator.validate_uuid(data["id"], "id")

        # Slug format (optional)
        if "slug" in data and data["slug"]:
            SchemaValidator.validate_slug(data["slug"])

        # Status (optional)
        if "status" in data and data["status"]:
            SchemaValidator.validate_entity_status(data["status"])

    @staticmethod
    def validate_document_data(data: Dict[str, Any]) -> None:
        """Validate document data matches database schema."""
        SchemaValidator.validate_required_fields("document", data)

        # UUID fields
        if "project_id" in data:
            SchemaValidator.validate_uuid(data["project_id"], "project_id")
        if "id" in data and data["id"]:
            SchemaValidator.validate_uuid(data["id"], "id")

        # Status (optional)
        if "status" in data and data["status"]:
            SchemaValidator.validate_entity_status(data["status"])

    @staticmethod
    def validate_requirement_data(data: Dict[str, Any]) -> None:
        """Validate requirement data matches database schema."""
        SchemaValidator.validate_required_fields("requirement", data)

        # UUID fields
        if "document_id" in data:
            SchemaValidator.validate_uuid(data["document_id"], "document_id")
        if "id" in data and data["id"]:
            SchemaValidator.validate_uuid(data["id"], "id")

        # Priority (optional)
        if "priority" in data and data["priority"]:
            SchemaValidator.validate_priority(data["priority"])

        # Status (optional)
        if "status" in data and data["status"]:
            SchemaValidator.validate_entity_status(data["status"])

    @staticmethod
    def validate_test_data(data: Dict[str, Any]) -> None:
        """Validate test data matches database schema."""
        SchemaValidator.validate_required_fields("test", data)

        # UUID fields
        if "project_id" in data:
            SchemaValidator.validate_uuid(data["project_id"], "project_id")
        if "id" in data and data["id"]:
            SchemaValidator.validate_uuid(data["id"], "id")

        # Priority (optional)
        if "priority" in data and data["priority"]:
            SchemaValidator.validate_priority(data["priority"])

        # Test status (optional)
        if "status" in data and data["status"]:
            SchemaValidator.validate_test_status(data["status"])

    @staticmethod
    def validate_entity_data(entity_type: str, data: Dict[str, Any]) -> None:
        """
        Validate entity data based on type.

        Args:
            entity_type: Type of entity (organization, project, etc.)
            data: Entity data to validate

        Raises:
            ValidationError: If data doesn't match schema
        """
        validators = {
            "organization": SchemaValidator.validate_organization_data,
            "project": SchemaValidator.validate_project_data,
            "document": SchemaValidator.validate_document_data,
            "requirement": SchemaValidator.validate_requirement_data,
            "test": SchemaValidator.validate_test_data,
        }

        validator = validators.get(entity_type)
        if not validator:
            raise ValidationError(f"Unknown entity type: {entity_type}")

        validator(data)


def validate_before_create(entity_type: str, data: Dict[str, Any]) -> None:
    """
    Validate data before creating entity in database.

    Use this in tool handlers before sending data to Supabase.

    Args:
        entity_type: Type of entity
        data: Entity data to validate

    Raises:
        ValidationError: If validation fails
    """
    SchemaValidator.validate_entity_data(entity_type, data)


def validate_before_update(entity_type: str, data: Dict[str, Any]) -> None:
    """
    Validate data before updating entity in database.

    Args:
        entity_type: Type of entity
        data: Entity data to validate (partial updates allowed)

    Raises:
        ValidationError: If validation fails
    """
    # For updates, we don't require all fields, just validate what's present

    # Validate enums if present
    if entity_type == "organization" and "type" in data:
        SchemaValidator.validate_organization_type(data["type"])

    if "status" in data and data["status"]:
        if entity_type == "test":
            SchemaValidator.validate_test_status(data["status"])
        else:
            SchemaValidator.validate_entity_status(data["status"])

    if "priority" in data and data["priority"]:
        SchemaValidator.validate_priority(data["priority"])

    # Validate UUIDs if present
    uuid_fields = ["id", "organization_id", "project_id", "document_id", "requirement_id", "test_id"]
    for field in uuid_fields:
        if field in data and data[field]:
            SchemaValidator.validate_uuid(data[field], field)
