"""
Base Models for Atoms MCP

Core data models for the Atoms workspace management system.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """Base entity class with common fields."""

    # Core entity fields (used by all entities)
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID | None = None
    updated_by: UUID | None = None
    is_deleted: bool = False

    # Pydantic configuration (used for serialization)
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )


class Organization(BaseEntity):
    """Organization model."""

    name: str = Field(..., min_length=1, max_length=255)
    # Organization-specific fields (used for organization management)
    description: str | None = None
    domain: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"  # active, inactive, suspended


class Project(BaseEntity):
    """Project model."""

    name: str = Field(..., min_length=1, max_length=255)
    # Project-specific fields (used for project management)
    description: str | None = None
    organization_id: UUID
    settings: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"  # active, inactive, archived
    tags: list[str] = Field(default_factory=list)


class Document(BaseEntity):
    """Document model."""

    title: str = Field(..., min_length=1, max_length=500)
    # Document-specific fields (used for document management)
    content: str | None = None
    project_id: UUID
    document_type: str = "document"  # document, specification, design, etc.
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"  # draft, review, approved, published
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)


class Requirement(BaseEntity):
    """Requirement model."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str
    document_id: UUID
    priority: str = "medium"  # low, medium, high, critical
    status: str = "draft"  # draft, review, approved, implemented, rejected
    acceptance_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class Test(BaseEntity):
    """Test model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_id: UUID
    test_type: str = "unit"  # unit, integration, system, acceptance
    status: str = "draft"  # draft, ready, running, passed, failed, skipped
    steps: list[dict[str, Any]] = Field(default_factory=list)
    expected_result: str | None = None
    actual_result: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
