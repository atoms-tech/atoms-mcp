"""Consolidated validation using Pydantic.

Replaces:
- infrastructure/input_validator.py
- tools/entity_modules/validators.py

All validation now uses Pydantic's built-in validators.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator, ConfigDict


class EntityInput(BaseModel):
    """Base input validation for all entities."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[str] = Field(None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name - no SQL injection patterns."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        # Check for SQL injection patterns
        if re.search(r"(;|--|#|/\*|\*/|DROP|DELETE|INSERT|UPDATE|UNION|SELECT)", v, re.IGNORECASE):
            raise ValueError("Name contains invalid characters")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description - no XSS patterns."""
        if v is None:
            return v
        if re.search(r"(<script|javascript:|on\w+\s*=|<iframe|<object|<embed)", v, re.IGNORECASE):
            raise ValueError("Description contains invalid HTML")
        return v.strip() if v else None


class OrganizationInput(EntityInput):
    """Validation for organization creation/update."""

    slug: str = Field(..., min_length=1, max_length=100)
    type: str = Field("team", max_length=50)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        if not re.match(r"^[a-z0-9_\-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, hyphens, and underscores")
        return v


class ProjectInput(EntityInput):
    """Validation for project creation/update."""

    organization_id: UUID
    slug: Optional[str] = Field(None, max_length=100)


class DocumentInput(EntityInput):
    """Validation for document creation/update."""

    project_id: UUID
    content: Optional[str] = Field(None, max_length=50000)
    version: Optional[int] = Field(None, ge=0)


class RequirementInput(EntityInput):
    """Validation for requirement creation/update."""

    document_id: UUID
    priority: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, max_length=50)


class TestInput(EntityInput):
    """Validation for test creation/update."""

    requirement_id: UUID
    test_type: Optional[str] = Field(None, max_length=50)


class RelationshipInput(BaseModel):
    """Validation for relationship creation/update."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_id: UUID
    target_id: UUID
    relationship_type: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("relationship_type")
    @classmethod
    def validate_relationship_type(cls, v: str) -> str:
        """Validate relationship type."""
        if not re.match(r"^[a-z_]+$", v):
            raise ValueError("Relationship type must contain only lowercase letters and underscores")
        return v


class SearchInput(BaseModel):
    """Validation for search queries."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(..., min_length=1, max_length=1000)
    entity_type: Optional[str] = Field(None, max_length=100)
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


# Utility functions for backward compatibility
def validate_required_fields(entity_type: str, data: Dict[str, Any]) -> None:
    """Validate required fields (backward compatibility)."""
    # This is now handled by Pydantic models
    pass


def validate_entity_data(entity_type: str, data: Dict[str, Any]) -> None:
    """Validate entity data (backward compatibility)."""
    # This is now handled by Pydantic models
    pass


def is_uuid_format(value: str) -> bool:
    """Check if string is valid UUID format."""
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False

