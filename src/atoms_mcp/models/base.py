"""
Base Models for Atoms MCP

Core data models for the Atoms workspace management system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4


class BaseEntity(BaseModel):
    """Base entity class with common fields."""
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_deleted: bool = False
    
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
    description: Optional[str] = None
    domain: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"  # active, inactive, suspended


class Project(BaseEntity):
    """Project model."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    organization_id: UUID
    settings: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"  # active, inactive, archived
    tags: List[str] = Field(default_factory=list)


class Document(BaseEntity):
    """Document model."""
    
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    project_id: UUID
    document_type: str = "document"  # document, specification, design, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"  # draft, review, approved, published
    version: str = "1.0"
    tags: List[str] = Field(default_factory=list)


class Requirement(BaseEntity):
    """Requirement model."""
    
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    document_id: UUID
    priority: str = "medium"  # low, medium, high, critical
    status: str = "draft"  # draft, review, approved, implemented, rejected
    acceptance_criteria: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class Test(BaseEntity):
    """Test model."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: UUID
    test_type: str = "unit"  # unit, integration, system, acceptance
    status: str = "draft"  # draft, ready, running, passed, failed, skipped
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)