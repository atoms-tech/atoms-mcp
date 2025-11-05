"""
Data Transfer Objects for the application layer.

DTOs provide a clean separation between domain models and API/UI representations.
They are used for serialization and deserialization of data across boundaries.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class ResultStatus(Enum):
    """Status enumeration for command/query results."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class CommandResult(Generic[T]):
    """
    Result wrapper for command execution.

    Attributes:
        status: Execution status
        data: Result data if successful
        error: Error message if failed
        metadata: Additional result metadata
    """

    status: ResultStatus
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if command succeeded."""
        return self.status == ResultStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if command failed."""
        return self.status == ResultStatus.ERROR

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class QueryResult(Generic[T]):
    """
    Result wrapper for query execution.

    Attributes:
        status: Execution status
        data: Query result data
        total_count: Total count for pagination
        page: Current page number
        page_size: Number of items per page
        error: Error message if failed
        metadata: Additional result metadata
    """

    status: ResultStatus
    data: Optional[T] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if query succeeded."""
        return self.status == ResultStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if query failed."""
        return self.status == ResultStatus.ERROR

    @property
    def has_more_pages(self) -> bool:
        """Check if there are more pages available."""
        return (self.page * self.page_size) < self.total_count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "status": self.status.value,
            "data": self.data,
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class EntityDTO:
    """
    Data transfer object for entities.

    Attributes:
        id: Entity ID
        entity_type: Type of entity
        name: Entity name
        description: Entity description
        status: Entity status
        created_at: Creation timestamp
        updated_at: Update timestamp
        metadata: Additional metadata
        properties: Entity-specific properties
    """

    id: str
    entity_type: str
    name: str = ""
    description: str = ""
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityDTO":
        """Create from dictionary representation."""
        return cls(**data)


@dataclass
class RelationshipDTO:
    """
    Data transfer object for relationships.

    Attributes:
        id: Relationship ID
        source_id: Source entity ID
        target_id: Target entity ID
        relationship_type: Type of relationship
        status: Relationship status
        created_at: Creation timestamp
        updated_at: Update timestamp
        created_by: Creator user ID
        properties: Relationship properties
    """

    id: str
    source_id: str
    target_id: str
    relationship_type: str
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationshipDTO":
        """Create from dictionary representation."""
        return cls(**data)


@dataclass
class WorkflowDTO:
    """
    Data transfer object for workflows.

    Attributes:
        id: Workflow ID
        name: Workflow name
        description: Workflow description
        enabled: Whether workflow is enabled
        trigger_type: Type of trigger
        steps: List of workflow steps
        created_at: Creation timestamp
        updated_at: Update timestamp
        metadata: Additional metadata
    """

    id: str
    name: str
    description: str = ""
    enabled: bool = True
    trigger_type: str = "manual"
    steps: list[dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowDTO":
        """Create from dictionary representation."""
        return cls(**data)


@dataclass
class WorkflowExecutionDTO:
    """
    Data transfer object for workflow executions.

    Attributes:
        id: Execution ID
        workflow_id: Workflow ID
        status: Execution status
        started_at: Start timestamp
        completed_at: Completion timestamp
        error_message: Error message if failed
        execution_log: Execution log entries
    """

    id: str
    workflow_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowExecutionDTO":
        """Create from dictionary representation."""
        return cls(**data)


__all__ = [
    "CommandResult",
    "QueryResult",
    "ResultStatus",
    "EntityDTO",
    "RelationshipDTO",
    "WorkflowDTO",
    "WorkflowExecutionDTO",
]
