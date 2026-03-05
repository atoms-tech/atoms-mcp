"""
Domain models for entities.

This module defines the core entity models for the Atoms MCP system.
All models are pure dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class EntityStatus(Enum):
    """Status enumeration for entities."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class EntityType(Enum):
    """Type enumeration for entities."""

    WORKSPACE = "workspace"
    PROJECT = "project"
    TASK = "task"
    DOCUMENT = "document"
    REQUIREMENT = "requirement"
    TEST_CASE = "test_case"
    USER = "user"


@dataclass
class Entity:
    """
    Base entity class with common attributes.

    All domain entities inherit from this class. It provides
    common tracking fields and identity management.

    Attributes:
        id: Unique identifier for the entity
        created_at: Timestamp when entity was created
        updated_at: Timestamp when entity was last updated
        status: Current status of the entity
        metadata: Additional flexible metadata
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: EntityStatus = EntityStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_updated(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive this entity."""
        self.status = EntityStatus.ARCHIVED
        self.mark_updated()

    def delete(self) -> None:
        """Soft delete this entity."""
        self.status = EntityStatus.DELETED
        self.mark_updated()

    def restore(self) -> None:
        """Restore this entity to active status."""
        self.status = EntityStatus.ACTIVE
        self.mark_updated()

    def is_active(self) -> bool:
        """Check if entity is active."""
        return self.status == EntityStatus.ACTIVE

    def is_deleted(self) -> bool:
        """Check if entity is deleted."""
        return self.status == EntityStatus.DELETED

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key.

        Args:
            key: Metadata key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value.

        Args:
            key: Metadata key to set
            value: Value to store
        """
        self.metadata[key] = value
        self.mark_updated()


@dataclass
class WorkspaceEntity(Entity):
    """
    Workspace entity representing an organizational workspace.

    A workspace is the top-level organizational unit that contains
    projects and other entities.

    Attributes:
        name: Workspace name
        description: Detailed description
        owner_id: ID of the workspace owner
        settings: Workspace-specific settings
    """

    name: str = ""
    description: str = ""
    owner_id: Optional[str] = None
    settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate workspace after initialization."""
        if not self.name:
            raise ValueError("Workspace name cannot be empty")

    def update_settings(self, settings: dict[str, Any]) -> None:
        """
        Update workspace settings.

        Args:
            settings: Settings to merge with existing settings
        """
        self.settings.update(settings)
        self.mark_updated()

    def change_owner(self, new_owner_id: str) -> None:
        """
        Transfer workspace ownership.

        Args:
            new_owner_id: ID of the new owner
        """
        if not new_owner_id:
            raise ValueError("Owner ID cannot be empty")
        self.owner_id = new_owner_id
        self.mark_updated()


@dataclass
class ProjectEntity(Entity):
    """
    Project entity representing a project within a workspace.

    A project contains tasks, documents, and other project-specific
    entities.

    Attributes:
        name: Project name
        description: Detailed description
        workspace_id: Parent workspace ID
        start_date: Project start date
        end_date: Project end date
        priority: Project priority (1-5, where 5 is highest)
        tags: Project tags for categorization
    """

    name: str = ""
    description: str = ""
    workspace_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    priority: int = 3
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate project after initialization."""
        if not self.name:
            raise ValueError("Project name cannot be empty")
        if self.priority < 1 or self.priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")

    def set_priority(self, priority: int) -> None:
        """
        Set project priority.

        Args:
            priority: Priority level (1-5)
        """
        if priority < 1 or priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        self.priority = priority
        self.mark_updated()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the project.

        Args:
            tag: Tag to add
        """
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.mark_updated()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the project.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_updated()

    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        if self.end_date and datetime.utcnow() > self.end_date:
            return self.status != EntityStatus.COMPLETED
        return False


@dataclass
class TaskEntity(Entity):
    """
    Task entity representing a unit of work.

    Tasks are the atomic units of work within projects.

    Attributes:
        title: Task title
        description: Detailed description
        project_id: Parent project ID
        assignee_id: ID of assigned user
        due_date: Task due date
        priority: Task priority (1-5)
        estimated_hours: Estimated effort in hours
        actual_hours: Actual effort spent in hours
        tags: Task tags
        dependencies: IDs of tasks this task depends on
    """

    title: str = ""
    description: str = ""
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 3
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate task after initialization."""
        if not self.title:
            raise ValueError("Task title cannot be empty")
        if self.priority < 1 or self.priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        if self.estimated_hours < 0:
            raise ValueError("Estimated hours cannot be negative")
        if self.actual_hours < 0:
            raise ValueError("Actual hours cannot be negative")

    def assign_to(self, assignee_id: str) -> None:
        """
        Assign task to a user.

        Args:
            assignee_id: ID of user to assign to
        """
        self.assignee_id = assignee_id
        self.mark_updated()

    def unassign(self) -> None:
        """Unassign task from current assignee."""
        self.assignee_id = None
        self.mark_updated()

    def add_dependency(self, task_id: str) -> None:
        """
        Add a task dependency.

        Args:
            task_id: ID of task this task depends on
        """
        if task_id == self.id:
            raise ValueError("Task cannot depend on itself")
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.mark_updated()

    def remove_dependency(self, task_id: str) -> None:
        """
        Remove a task dependency.

        Args:
            task_id: ID of task to remove dependency on
        """
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            self.mark_updated()

    def log_time(self, hours: float) -> None:
        """
        Log time spent on task.

        Args:
            hours: Hours to add to actual hours
        """
        if hours < 0:
            raise ValueError("Hours cannot be negative")
        self.actual_hours += hours
        self.mark_updated()

    def complete(self) -> None:
        """Mark task as completed."""
        self.status = EntityStatus.COMPLETED
        self.mark_updated()

    def block(self, reason: str) -> None:
        """
        Mark task as blocked.

        Args:
            reason: Reason for blocking
        """
        self.status = EntityStatus.BLOCKED
        self.set_metadata("block_reason", reason)
        self.mark_updated()

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and datetime.utcnow() > self.due_date:
            return self.status not in (EntityStatus.COMPLETED, EntityStatus.BLOCKED)
        return False


@dataclass
class DocumentEntity(Entity):
    """
    Document entity representing a document or artifact.

    Documents can be requirements, designs, specifications, or
    any other text-based artifact.

    Attributes:
        title: Document title
        content: Document content
        project_id: Parent project ID
        author_id: ID of document author
        version: Document version
        document_type: Type of document (requirements, design, etc.)
        tags: Document tags
    """

    title: str = ""
    content: str = ""
    project_id: Optional[str] = None
    author_id: Optional[str] = None
    version: str = "1.0.0"
    document_type: str = "general"
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate document after initialization."""
        if not self.title:
            raise ValueError("Document title cannot be empty")

    def update_content(self, content: str, increment_version: bool = True) -> None:
        """
        Update document content.

        Args:
            content: New content
            increment_version: Whether to increment version number
        """
        self.content = content
        if increment_version:
            self._increment_version()
        self.mark_updated()

    def _increment_version(self) -> None:
        """Increment the patch version number."""
        try:
            major, minor, patch = self.version.split(".")
            self.version = f"{major}.{minor}.{int(patch) + 1}"
        except (ValueError, AttributeError):
            self.version = "1.0.1"

    def set_version(self, version: str) -> None:
        """
        Manually set document version.

        Args:
            version: Version string (e.g., "2.1.0")
        """
        if not version:
            raise ValueError("Version cannot be empty")
        self.version = version
        self.mark_updated()

    def get_word_count(self) -> int:
        """Get approximate word count of content."""
        return len(self.content.split()) if self.content else 0
