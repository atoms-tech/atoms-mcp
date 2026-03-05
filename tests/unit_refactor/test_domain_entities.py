"""
Comprehensive unit tests for domain entities achieving 100% code coverage.

Tests all entity types, validation, lifecycle methods, relationships,
and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from atoms_mcp.domain.models.entity import (
    Entity,
    EntityStatus,
    EntityType,
    WorkspaceEntity,
    ProjectEntity,
    TaskEntity,
    DocumentEntity,
)


class TestBaseEntity:
    """Test the base Entity class."""

    def test_entity_creation_with_defaults(self):
        """Test entity is created with default values."""
        entity = Entity()

        assert entity.id is not None
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)
        assert entity.status == EntityStatus.ACTIVE
        assert entity.metadata == {}

    def test_entity_creation_with_custom_values(self):
        """Test entity creation with custom values."""
        entity_id = str(uuid4())
        created = datetime(2024, 1, 1)
        updated = datetime(2024, 1, 2)
        metadata = {"key": "value"}

        entity = Entity(
            id=entity_id,
            created_at=created,
            updated_at=updated,
            status=EntityStatus.ARCHIVED,
            metadata=metadata,
        )

        assert entity.id == entity_id
        assert entity.created_at == created
        assert entity.updated_at == updated
        assert entity.status == EntityStatus.ARCHIVED
        assert entity.metadata == metadata

    def test_mark_updated(self):
        """Test mark_updated updates the timestamp."""
        entity = Entity()
        original_updated = entity.updated_at

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.001)

        entity.mark_updated()

        assert entity.updated_at > original_updated

    def test_archive(self):
        """Test archiving an entity."""
        entity = Entity()
        original_updated = entity.updated_at

        entity.archive()

        assert entity.status == EntityStatus.ARCHIVED
        assert entity.updated_at > original_updated

    def test_delete(self):
        """Test soft deleting an entity."""
        entity = Entity()
        original_updated = entity.updated_at

        entity.delete()

        assert entity.status == EntityStatus.DELETED
        assert entity.updated_at > original_updated

    def test_restore(self):
        """Test restoring a deleted entity."""
        entity = Entity(status=EntityStatus.DELETED)
        original_updated = entity.updated_at

        entity.restore()

        assert entity.status == EntityStatus.ACTIVE
        assert entity.updated_at > original_updated

    def test_is_active(self):
        """Test is_active method."""
        entity = Entity(status=EntityStatus.ACTIVE)
        assert entity.is_active() is True

        entity.status = EntityStatus.DELETED
        assert entity.is_active() is False

    def test_is_deleted(self):
        """Test is_deleted method."""
        entity = Entity(status=EntityStatus.DELETED)
        assert entity.is_deleted() is True

        entity.status = EntityStatus.ACTIVE
        assert entity.is_deleted() is False

    def test_get_metadata(self):
        """Test getting metadata values."""
        entity = Entity(metadata={"key1": "value1", "key2": "value2"})

        assert entity.get_metadata("key1") == "value1"
        assert entity.get_metadata("key2") == "value2"
        assert entity.get_metadata("nonexistent") is None
        assert entity.get_metadata("nonexistent", "default") == "default"

    def test_set_metadata(self):
        """Test setting metadata values."""
        entity = Entity()
        original_updated = entity.updated_at

        entity.set_metadata("key1", "value1")

        assert entity.metadata["key1"] == "value1"
        assert entity.updated_at > original_updated

    def test_set_metadata_overwrites_existing(self):
        """Test that setting metadata overwrites existing values."""
        entity = Entity(metadata={"key": "old_value"})

        entity.set_metadata("key", "new_value")

        assert entity.metadata["key"] == "new_value"


class TestWorkspaceEntity:
    """Test WorkspaceEntity class."""

    def test_workspace_creation(self):
        """Test workspace entity creation."""
        workspace = WorkspaceEntity(
            name="Test Workspace",
            description="Test description",
            owner_id="owner_123",
            settings={"theme": "dark"},
        )

        assert workspace.name == "Test Workspace"
        assert workspace.description == "Test description"
        assert workspace.owner_id == "owner_123"
        assert workspace.settings == {"theme": "dark"}
        assert workspace.status == EntityStatus.ACTIVE

    def test_workspace_empty_name_raises_error(self):
        """Test that empty workspace name raises ValueError."""
        with pytest.raises(ValueError, match="Workspace name cannot be empty"):
            WorkspaceEntity(name="")

    def test_workspace_update_settings(self):
        """Test updating workspace settings."""
        workspace = WorkspaceEntity(
            name="Test",
            settings={"theme": "dark", "notifications": True},
        )

        workspace.update_settings({"notifications": False, "language": "en"})

        assert workspace.settings["theme"] == "dark"
        assert workspace.settings["notifications"] is False
        assert workspace.settings["language"] == "en"

    def test_workspace_change_owner(self):
        """Test changing workspace owner."""
        workspace = WorkspaceEntity(name="Test", owner_id="owner_1")

        workspace.change_owner("owner_2")

        assert workspace.owner_id == "owner_2"

    def test_workspace_change_owner_empty_raises_error(self):
        """Test that empty owner ID raises ValueError."""
        workspace = WorkspaceEntity(name="Test")

        with pytest.raises(ValueError, match="Owner ID cannot be empty"):
            workspace.change_owner("")


class TestProjectEntity:
    """Test ProjectEntity class."""

    def test_project_creation(self):
        """Test project entity creation."""
        project = ProjectEntity(
            name="Test Project",
            description="Test description",
            workspace_id="workspace_123",
            priority=4,
            tags=["tag1", "tag2"],
        )

        assert project.name == "Test Project"
        assert project.description == "Test description"
        assert project.workspace_id == "workspace_123"
        assert project.priority == 4
        assert project.tags == ["tag1", "tag2"]

    def test_project_empty_name_raises_error(self):
        """Test that empty project name raises ValueError."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            ProjectEntity(name="")

    def test_project_invalid_priority_raises_error(self):
        """Test that invalid priority raises ValueError."""
        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            ProjectEntity(name="Test", priority=0)

        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            ProjectEntity(name="Test", priority=6)

    def test_project_end_before_start_raises_error(self):
        """Test that end date before start date raises ValueError."""
        start = datetime.utcnow()
        end = start - timedelta(days=1)

        with pytest.raises(ValueError, match="End date cannot be before start date"):
            ProjectEntity(name="Test", start_date=start, end_date=end)

    def test_project_set_priority(self):
        """Test setting project priority."""
        project = ProjectEntity(name="Test", priority=3)

        project.set_priority(5)

        assert project.priority == 5

    def test_project_set_invalid_priority_raises_error(self):
        """Test that setting invalid priority raises ValueError."""
        project = ProjectEntity(name="Test")

        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            project.set_priority(0)

    def test_project_add_tag(self):
        """Test adding tags to project."""
        project = ProjectEntity(name="Test", tags=["tag1"])

        project.add_tag("tag2")

        assert "tag2" in project.tags
        assert len(project.tags) == 2

    def test_project_add_duplicate_tag_ignored(self):
        """Test that adding duplicate tag is ignored."""
        project = ProjectEntity(name="Test", tags=["tag1"])

        project.add_tag("tag1")

        assert project.tags.count("tag1") == 1

    def test_project_add_empty_tag_ignored(self):
        """Test that adding empty tag is ignored."""
        project = ProjectEntity(name="Test")

        project.add_tag("")

        assert len(project.tags) == 0

    def test_project_remove_tag(self):
        """Test removing tags from project."""
        project = ProjectEntity(name="Test", tags=["tag1", "tag2"])

        project.remove_tag("tag1")

        assert "tag1" not in project.tags
        assert "tag2" in project.tags

    def test_project_is_overdue(self):
        """Test checking if project is overdue."""
        past_date = datetime.utcnow() - timedelta(days=1)
        future_date = datetime.utcnow() + timedelta(days=1)

        # Overdue project
        project1 = ProjectEntity(name="Test", end_date=past_date)
        assert project1.is_overdue() is True

        # Not overdue project
        project2 = ProjectEntity(name="Test", end_date=future_date)
        assert project2.is_overdue() is False

        # Completed project is not overdue
        project3 = ProjectEntity(name="Test", end_date=past_date, status=EntityStatus.COMPLETED)
        assert project3.is_overdue() is False

        # No end date is not overdue
        project4 = ProjectEntity(name="Test")
        assert project4.is_overdue() is False


class TestTaskEntity:
    """Test TaskEntity class."""

    def test_task_creation(self):
        """Test task entity creation."""
        task = TaskEntity(
            title="Test Task",
            description="Test description",
            project_id="project_123",
            assignee_id="user_123",
            priority=4,
            estimated_hours=8.0,
            actual_hours=2.0,
        )

        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.project_id == "project_123"
        assert task.assignee_id == "user_123"
        assert task.priority == 4
        assert task.estimated_hours == 8.0
        assert task.actual_hours == 2.0

    def test_task_empty_title_raises_error(self):
        """Test that empty task title raises ValueError."""
        with pytest.raises(ValueError, match="Task title cannot be empty"):
            TaskEntity(title="")

    def test_task_invalid_priority_raises_error(self):
        """Test that invalid priority raises ValueError."""
        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            TaskEntity(title="Test", priority=0)

    def test_task_negative_estimated_hours_raises_error(self):
        """Test that negative estimated hours raises ValueError."""
        with pytest.raises(ValueError, match="Estimated hours cannot be negative"):
            TaskEntity(title="Test", estimated_hours=-1.0)

    def test_task_negative_actual_hours_raises_error(self):
        """Test that negative actual hours raises ValueError."""
        with pytest.raises(ValueError, match="Actual hours cannot be negative"):
            TaskEntity(title="Test", actual_hours=-1.0)

    def test_task_assign_to(self):
        """Test assigning task to user."""
        task = TaskEntity(title="Test")

        task.assign_to("user_123")

        assert task.assignee_id == "user_123"

    def test_task_unassign(self):
        """Test unassigning task."""
        task = TaskEntity(title="Test", assignee_id="user_123")

        task.unassign()

        assert task.assignee_id is None

    def test_task_add_dependency(self):
        """Test adding task dependency."""
        task = TaskEntity(title="Test")

        task.add_dependency("task_123")

        assert "task_123" in task.dependencies

    def test_task_add_self_dependency_raises_error(self):
        """Test that adding self dependency raises ValueError."""
        task = TaskEntity(title="Test")

        with pytest.raises(ValueError, match="Task cannot depend on itself"):
            task.add_dependency(task.id)

    def test_task_add_duplicate_dependency_ignored(self):
        """Test that adding duplicate dependency is ignored."""
        task = TaskEntity(title="Test", dependencies=["task_123"])

        task.add_dependency("task_123")

        assert task.dependencies.count("task_123") == 1

    def test_task_remove_dependency(self):
        """Test removing task dependency."""
        task = TaskEntity(title="Test", dependencies=["task_123", "task_456"])

        task.remove_dependency("task_123")

        assert "task_123" not in task.dependencies
        assert "task_456" in task.dependencies

    def test_task_log_time(self):
        """Test logging time on task."""
        task = TaskEntity(title="Test", actual_hours=2.0)

        task.log_time(3.5)

        assert task.actual_hours == 5.5

    def test_task_log_negative_time_raises_error(self):
        """Test that logging negative time raises ValueError."""
        task = TaskEntity(title="Test")

        with pytest.raises(ValueError, match="Hours cannot be negative"):
            task.log_time(-1.0)

    def test_task_complete(self):
        """Test completing task."""
        task = TaskEntity(title="Test")

        task.complete()

        assert task.status == EntityStatus.COMPLETED

    def test_task_block(self):
        """Test blocking task."""
        task = TaskEntity(title="Test")

        task.block("Waiting for approval")

        assert task.status == EntityStatus.BLOCKED
        assert task.get_metadata("block_reason") == "Waiting for approval"

    def test_task_is_overdue(self):
        """Test checking if task is overdue."""
        past_date = datetime.utcnow() - timedelta(days=1)
        future_date = datetime.utcnow() + timedelta(days=1)

        # Overdue task
        task1 = TaskEntity(title="Test", due_date=past_date)
        assert task1.is_overdue() is True

        # Not overdue task
        task2 = TaskEntity(title="Test", due_date=future_date)
        assert task2.is_overdue() is False

        # Completed task is not overdue
        task3 = TaskEntity(title="Test", due_date=past_date, status=EntityStatus.COMPLETED)
        assert task3.is_overdue() is False

        # Blocked task is not overdue
        task4 = TaskEntity(title="Test", due_date=past_date, status=EntityStatus.BLOCKED)
        assert task4.is_overdue() is False


class TestDocumentEntity:
    """Test DocumentEntity class."""

    def test_document_creation(self):
        """Test document entity creation."""
        document = DocumentEntity(
            title="Test Document",
            content="Test content",
            project_id="project_123",
            author_id="user_123",
            document_type="requirements",
            version="1.0.0",
        )

        assert document.title == "Test Document"
        assert document.content == "Test content"
        assert document.project_id == "project_123"
        assert document.author_id == "user_123"
        assert document.document_type == "requirements"
        assert document.version == "1.0.0"

    def test_document_empty_title_raises_error(self):
        """Test that empty document title raises ValueError."""
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            DocumentEntity(title="")

    def test_document_update_content(self):
        """Test updating document content."""
        document = DocumentEntity(title="Test", content="Old content", version="1.0.0")

        document.update_content("New content")

        assert document.content == "New content"
        assert document.version == "1.0.1"

    def test_document_update_content_without_version_increment(self):
        """Test updating content without version increment."""
        document = DocumentEntity(title="Test", content="Old content", version="1.0.0")

        document.update_content("New content", increment_version=False)

        assert document.content == "New content"
        assert document.version == "1.0.0"

    def test_document_increment_version(self):
        """Test version incrementing."""
        document = DocumentEntity(title="Test", version="1.0.0")

        document._increment_version()
        assert document.version == "1.0.1"

        document._increment_version()
        assert document.version == "1.0.2"

    def test_document_increment_version_invalid_format(self):
        """Test version incrementing with invalid format."""
        document = DocumentEntity(title="Test", version="invalid")

        document._increment_version()

        assert document.version == "1.0.1"

    def test_document_set_version(self):
        """Test setting document version manually."""
        document = DocumentEntity(title="Test")

        document.set_version("2.1.0")

        assert document.version == "2.1.0"

    def test_document_set_empty_version_raises_error(self):
        """Test that setting empty version raises ValueError."""
        document = DocumentEntity(title="Test")

        with pytest.raises(ValueError, match="Version cannot be empty"):
            document.set_version("")

    def test_document_get_word_count(self):
        """Test getting document word count."""
        document = DocumentEntity(title="Test", content="This is a test document with words")

        assert document.get_word_count() == 7

    def test_document_get_word_count_empty(self):
        """Test word count for empty document."""
        document = DocumentEntity(title="Test", content="")

        assert document.get_word_count() == 0


class TestEntityEnumerations:
    """Test entity enumeration types."""

    def test_entity_status_enum(self):
        """Test EntityStatus enumeration."""
        assert EntityStatus.ACTIVE.value == "active"
        assert EntityStatus.ARCHIVED.value == "archived"
        assert EntityStatus.DELETED.value == "deleted"
        assert EntityStatus.DRAFT.value == "draft"
        assert EntityStatus.IN_PROGRESS.value == "in_progress"
        assert EntityStatus.COMPLETED.value == "completed"
        assert EntityStatus.BLOCKED.value == "blocked"

    def test_entity_type_enum(self):
        """Test EntityType enumeration."""
        assert EntityType.WORKSPACE.value == "workspace"
        assert EntityType.PROJECT.value == "project"
        assert EntityType.TASK.value == "task"
        assert EntityType.DOCUMENT.value == "document"
        assert EntityType.REQUIREMENT.value == "requirement"
        assert EntityType.TEST_CASE.value == "test_case"
        assert EntityType.USER.value == "user"
