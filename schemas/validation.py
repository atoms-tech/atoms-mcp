"""
Schema validation utilities for runtime type checking.

This module provides validation functions to ensure data matches
the expected database schema before sending to Supabase.
"""

from typing import Any

from schemas.constants import (
    AUTO_FIELDS,
)
from schemas.enums import (
    DocumentType,
    EntityStatus,
    InvitationStatus,
    MemberRole,
    OrganizationType,
    Priority,
    TestStatus,
    TestType,
)


class ValidationError(Exception):
    """Raised when schema validation fails."""


class SchemaValidator:
    """Validates data against database schema."""

    @staticmethod
    def validate_organization(data: dict[str, Any], operation: str = "create") -> list[str]:
        """
        Validate organization data against schema.
        
        Args:
            data: Organization data to validate
            operation: Operation type (create, update)
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required fields for create
        if operation == "create":
            if not data.get("name"):
                errors.append("Missing required field: name")
            if not data.get("slug"):
                errors.append("Missing required field: slug")
            if not data.get("type"):
                errors.append("Missing required field: type")

        # Validate type enum
        if "type" in data:
            try:
                OrganizationType(data["type"])
            except ValueError:
                valid_types = [t.value for t in OrganizationType]
                errors.append(
                    f"Invalid organization type: '{data['type']}'. "
                    f"Valid values: {valid_types}"
                )

        # Validate slug format
        if "slug" in data:
            slug = data["slug"]
            if not isinstance(slug, str):
                errors.append(f"Slug must be string, got {type(slug).__name__}")
            elif not slug:
                errors.append("Slug cannot be empty")
            elif not slug[0].isalpha():
                errors.append(f"Slug must start with letter, got: '{slug}'")
            elif not all(c.isalnum() or c == "-" for c in slug):
                errors.append(f"Slug can only contain lowercase letters, numbers, and hyphens, got: '{slug}'")
            elif slug != slug.lower():
                errors.append(f"Slug must be lowercase, got: '{slug}'")

        # Check for auto-generated fields
        for field in AUTO_FIELDS:
            if field in data and operation == "create":
                errors.append(f"Cannot set auto-generated field: {field}")

        return errors

    @staticmethod
    def validate_project(data: dict[str, Any], operation: str = "create") -> list[str]:
        """Validate project data against schema."""
        errors = []

        if operation == "create":
            if not data.get("name"):
                errors.append("Missing required field: name")
            if not data.get("organization_id"):
                errors.append("Missing required field: organization_id")

        # Validate status if present
        if "status" in data:
            try:
                EntityStatus(data["status"])
            except ValueError:
                valid_statuses = [s.value for s in EntityStatus]
                errors.append(
                    f"Invalid status: '{data['status']}'. "
                    f"Valid values: {valid_statuses}"
                )

        return errors

    @staticmethod
    def validate_document(data: dict[str, Any], operation: str = "create") -> list[str]:
        """Validate document data against schema."""
        errors = []

        if operation == "create":
            if not data.get("name"):
                errors.append("Missing required field: name")
            if not data.get("project_id"):
                errors.append("Missing required field: project_id")

        # Validate doc_type if present
        if "doc_type" in data:
            try:
                DocumentType(data["doc_type"])
            except ValueError:
                valid_types = [t.value for t in DocumentType]
                errors.append(
                    f"Invalid document type: '{data['doc_type']}'. "
                    f"Valid values: {valid_types}"
                )

        return errors

    @staticmethod
    def validate_requirement(data: dict[str, Any], operation: str = "create") -> list[str]:
        """Validate requirement data against schema."""
        errors = []

        if operation == "create":
            if not data.get("name"):
                errors.append("Missing required field: name")
            if not data.get("document_id"):
                errors.append("Missing required field: document_id")

        # Validate priority if present
        if "priority" in data:
            try:
                Priority(data["priority"])
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                errors.append(
                    f"Invalid priority: '{data['priority']}'. "
                    f"Valid values: {valid_priorities}"
                )

        # Validate status if present
        if "status" in data:
            try:
                EntityStatus(data["status"])
            except ValueError:
                valid_statuses = [s.value for s in EntityStatus]
                errors.append(
                    f"Invalid status: '{data['status']}'. "
                    f"Valid values: {valid_statuses}"
                )

        return errors

    @staticmethod
    def validate_test(data: dict[str, Any], operation: str = "create") -> list[str]:
        """Validate test data against schema."""
        errors = []

        if operation == "create":
            if not data.get("title"):
                errors.append("Missing required field: title")
            if not data.get("project_id"):
                errors.append("Missing required field: project_id")

        # Validate test_type if present
        if "test_type" in data:
            try:
                TestType(data["test_type"])
            except ValueError:
                valid_types = [t.value for t in TestType]
                errors.append(
                    f"Invalid test type: '{data['test_type']}'. "
                    f"Valid values: {valid_types}"
                )

        # Validate status if present
        if "status" in data:
            try:
                TestStatus(data["status"])
            except ValueError:
                valid_statuses = [s.value for s in TestStatus]
                errors.append(
                    f"Invalid status: '{data['status']}'. "
                    f"Valid values: {valid_statuses}"
                )

        # Validate priority if present
        if "priority" in data:
            try:
                Priority(data["priority"])
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                errors.append(
                    f"Invalid priority: '{data['priority']}'. "
                    f"Valid values: {valid_priorities}"
                )

        return errors

    @staticmethod
    def validate_entity(entity_type: str, data: dict[str, Any], operation: str = "create") -> list[str]:
        """
        Validate entity data against schema.
        
        Args:
            entity_type: Type of entity (organization, project, etc.)
            data: Entity data to validate
            operation: Operation type (create, update)
            
        Returns:
            List of validation error messages (empty if valid)
            
        Raises:
            ValidationError: If validation fails
        """
        validators = {
            "organization": SchemaValidator.validate_organization,
            "project": SchemaValidator.validate_project,
            "document": SchemaValidator.validate_document,
            "requirement": SchemaValidator.validate_requirement,
            "test": SchemaValidator.validate_test,
        }

        validator = validators.get(entity_type)
        if not validator:
            return [f"Unknown entity type: {entity_type}"]

        return validator(data, operation)

    @staticmethod
    def validate_and_raise(entity_type: str, data: dict[str, Any], operation: str = "create") -> None:
        """
        Validate entity data and raise exception if invalid.
        
        Args:
            entity_type: Type of entity
            data: Entity data to validate
            operation: Operation type
            
        Raises:
            ValidationError: If validation fails
        """
        errors = SchemaValidator.validate_entity(entity_type, data, operation)
        if errors:
            error_msg = f"Schema validation failed for {entity_type}:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValidationError(error_msg)


def get_valid_enum_values(enum_name: str) -> list[str]:
    """
    Get list of valid values for an enum.
    
    Args:
        enum_name: Name of enum (e.g., "OrganizationType", "Priority")
        
    Returns:
        List of valid string values
    """
    enums = {
        "OrganizationType": OrganizationType,
        "EntityStatus": EntityStatus,
        "Priority": Priority,
        "TestStatus": TestStatus,
        "DocumentType": DocumentType,
        "TestType": TestType,
        "MemberRole": MemberRole,
        "InvitationStatus": InvitationStatus,
    }

    enum_class = enums.get(enum_name)
    if not enum_class:
        return []

    return [e.value for e in enum_class]


__all__ = [
    "SchemaValidator",
    "ValidationError",
    "get_valid_enum_values",
]

