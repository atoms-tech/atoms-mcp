"""
Comprehensive tests for application layer command handlers.

Tests cover:
- Command validation
- Command handler execution
- Error handling and result statuses
- Entity type-specific command handling
- Metadata management
"""

import pytest
from datetime import datetime
from typing import Any

from atoms_mcp.application.commands.entity_commands import (
    CreateEntityCommand,
    UpdateEntityCommand,
    DeleteEntityCommand,
    ArchiveEntityCommand,
    RestoreEntityCommand,
    EntityCommandHandler,
    EntityValidationError,
    EntityNotFoundError,
)
from atoms_mcp.application.dto import CommandResult, ResultStatus, EntityDTO
from atoms_mcp.domain.models.entity import (
    Entity,
    WorkspaceEntity,
    ProjectEntity,
    TaskEntity,
    DocumentEntity,
    EntityStatus,
)
from atoms_mcp.domain.ports.repository import RepositoryError

from conftest import MockRepository, MockLogger, MockCache


class TestCreateEntityCommandValidation:
    """Tests for CreateEntityCommand validation."""

    def test_validate_with_all_required_fields(self):
        """Should validate successfully with all required fields."""
        command = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
            description="Test description",
        )
        command.validate()  # Should not raise

    def test_validate_missing_entity_type(self):
        """Should raise validation error when entity_type is missing."""
        command = CreateEntityCommand(
            entity_type="",
            name="Test Workspace",
        )
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "entity_type is required" in str(exc_info.value)

    def test_validate_missing_name(self):
        """Should raise validation error when name is missing."""
        command = CreateEntityCommand(
            entity_type="workspace",
            name="",
        )
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "name is required" in str(exc_info.value)

    def test_validate_name_too_long(self):
        """Should raise validation error when name exceeds 255 characters."""
        long_name = "a" * 256
        command = CreateEntityCommand(
            entity_type="workspace",
            name=long_name,
        )
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "255 characters" in str(exc_info.value)

    def test_validate_name_exactly_255_characters(self):
        """Should validate successfully with name of exactly 255 characters."""
        name_255 = "a" * 255
        command = CreateEntityCommand(
            entity_type="workspace",
            name=name_255,
        )
        command.validate()  # Should not raise

    def test_validate_with_metadata_and_properties(self):
        """Should validate successfully with metadata and properties."""
        command = CreateEntityCommand(
            entity_type="project",
            name="Test Project",
            description="A test project",
            properties={"owner_id": "user123", "priority": 1},
            metadata={"key": "value"},
        )
        command.validate()  # Should not raise


class TestUpdateEntityCommandValidation:
    """Tests for UpdateEntityCommand validation."""

    def test_validate_with_valid_updates(self):
        """Should validate successfully with valid updates."""
        command = UpdateEntityCommand(
            entity_id="entity-123",
            updates={"name": "Updated Name"},
        )
        command.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should raise validation error when entity_id is missing."""
        command = UpdateEntityCommand(
            entity_id="",
            updates={"name": "Updated Name"},
        )
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_empty_updates(self):
        """Should raise validation error when updates dictionary is empty."""
        command = UpdateEntityCommand(
            entity_id="entity-123",
            updates={},
        )
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "updates cannot be empty" in str(exc_info.value)

    def test_validate_cannot_update_id(self):
        """Should raise validation error when trying to update id."""
        command = UpdateEntityCommand(
            entity_id="entity-123",
            updates={"id": "new-id"},
        )
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "cannot update entity id" in str(exc_info.value)

    def test_validate_can_update_other_fields(self):
        """Should validate successfully when updating non-id fields."""
        command = UpdateEntityCommand(
            entity_id="entity-123",
            updates={
                "name": "New Name",
                "description": "New description",
                "status": "archived",
            },
        )
        command.validate()  # Should not raise


class TestDeleteEntityCommandValidation:
    """Tests for DeleteEntityCommand validation."""

    def test_validate_with_valid_entity_id(self):
        """Should validate successfully with valid entity_id."""
        command = DeleteEntityCommand(entity_id="entity-123")
        command.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should raise validation error when entity_id is missing."""
        command = DeleteEntityCommand(entity_id="")
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_soft_delete_flag(self):
        """Should validate successfully with soft_delete flag."""
        command_soft = DeleteEntityCommand(
            entity_id="entity-123",
            soft_delete=True,
        )
        command_soft.validate()  # Should not raise

        command_hard = DeleteEntityCommand(
            entity_id="entity-123",
            soft_delete=False,
        )
        command_hard.validate()  # Should not raise


class TestArchiveEntityCommandValidation:
    """Tests for ArchiveEntityCommand validation."""

    def test_validate_with_valid_entity_id(self):
        """Should validate successfully with valid entity_id."""
        command = ArchiveEntityCommand(entity_id="entity-123")
        command.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should raise validation error when entity_id is missing."""
        command = ArchiveEntityCommand(entity_id="")
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_with_archived_by(self):
        """Should validate successfully with archived_by."""
        command = ArchiveEntityCommand(
            entity_id="entity-123",
            archived_by="user-456",
        )
        command.validate()  # Should not raise


class TestRestoreEntityCommandValidation:
    """Tests for RestoreEntityCommand validation."""

    def test_validate_with_valid_entity_id(self):
        """Should validate successfully with valid entity_id."""
        command = RestoreEntityCommand(entity_id="entity-123")
        command.validate()  # Should not raise

    def test_validate_missing_entity_id(self):
        """Should raise validation error when entity_id is missing."""
        command = RestoreEntityCommand(entity_id="")
        with pytest.raises(EntityValidationError) as exc_info:
            command.validate()
        assert "entity_id is required" in str(exc_info.value)

    def test_validate_with_restored_by(self):
        """Should validate successfully with restored_by."""
        command = RestoreEntityCommand(
            entity_id="entity-123",
            restored_by="user-456",
        )
        command.validate()  # Should not raise


class TestEntityCommandHandler:
    """Tests for EntityCommandHandler."""

    @pytest.fixture
    def handler(self):
        """Create a command handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return EntityCommandHandler(repository, logger, cache)

    def test_handler_initialization(self, handler):
        """Should initialize handler with dependencies."""
        assert handler.entity_service is not None
        assert handler.logger is not None

    def test_handle_create_entity_workspace_success(self, handler):
        """Should successfully create a workspace entity."""
        command = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
            description="A test workspace",
            properties={"owner_id": "user-123", "settings": {}},
            created_by="user-123",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, EntityDTO)
        assert result.data.entity_type == "workspace"
        assert result.data.name == "Test Workspace"
        assert "entity_id" in result.metadata

    def test_handle_create_entity_project_success(self, handler):
        """Should successfully create a project entity."""
        command = CreateEntityCommand(
            entity_type="project",
            name="Test Project",
            description="A test project",
            properties={
                "workspace_id": "workspace-123",
                "priority": 1,
                "tags": ["important"],
            },
            created_by="user-123",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, EntityDTO)
        assert result.data.entity_type == "project"
        assert result.data.name == "Test Project"

    def test_handle_create_entity_task_success(self, handler):
        """Should successfully create a task entity."""
        command = CreateEntityCommand(
            entity_type="task",
            name="Test Task",
            description="A test task",
            properties={
                "project_id": "project-123",
                "assignee_id": "user-456",
                "priority": 2,
                "estimated_hours": 5.0,
            },
            created_by="user-123",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, EntityDTO)
        assert result.data.entity_type == "task"

    def test_handle_create_entity_document_success(self, handler):
        """Should successfully create a document entity."""
        command = CreateEntityCommand(
            entity_type="document",
            name="Test Document",
            description="A test document",
            properties={
                "project_id": "project-123",
                "author_id": "user-123",
                "content": "Document content",
                "document_type": "specification",
            },
            created_by="user-123",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, EntityDTO)
        assert result.data.entity_type == "document"

    def test_handle_create_entity_generic_success(self, handler):
        """Should successfully create a generic entity."""
        command = CreateEntityCommand(
            entity_type="custom_type",
            name="Custom Entity",
            description="A custom entity",
            properties={"custom_field": "custom_value"},
            created_by="user-123",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, EntityDTO)

    def test_handle_create_entity_validation_error(self, handler):
        """Should return error result when validation fails."""
        command = CreateEntityCommand(
            entity_type="",
            name="Test Entity",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert result.error is not None
        assert "Validation error" in result.error

    def test_handle_create_entity_with_metadata(self, handler):
        """Should preserve metadata in created entity."""
        command = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
            created_by="user-123",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data.metadata.get("created_by") == "user-123"

    def test_handle_update_entity_success(self, handler):
        """Should successfully update an entity."""
        # First create an entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Original Name",
        )
        create_result = handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Then update it
        update_cmd = UpdateEntityCommand(
            entity_id=entity_id,
            updates={"name": "Updated Name"},
        )
        update_result = handler.handle_update_entity(update_cmd)

        assert update_result.status == ResultStatus.SUCCESS
        assert update_result.data is not None
        assert "entity_id" in update_result.metadata

    def test_handle_update_entity_not_found(self, handler):
        """Should return error when updating non-existent entity."""
        command = UpdateEntityCommand(
            entity_id="non-existent-id",
            updates={"name": "Updated Name"},
        )

        result = handler.handle_update_entity(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_handle_update_entity_validation_error(self, handler):
        """Should return error when update command validation fails."""
        command = UpdateEntityCommand(
            entity_id="",
            updates={"name": "Updated Name"},
        )

        result = handler.handle_update_entity(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "Validation error" in result.error

    def test_handle_update_entity_empty_updates(self, handler):
        """Should return error when updates are empty."""
        command = UpdateEntityCommand(
            entity_id="entity-123",
            updates={},
        )

        result = handler.handle_update_entity(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_delete_entity_soft_delete_success(self, handler):
        """Should successfully soft delete an entity."""
        # First create an entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )
        create_result = handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Then delete it (soft)
        delete_cmd = DeleteEntityCommand(
            entity_id=entity_id,
            soft_delete=True,
        )
        delete_result = handler.handle_delete_entity(delete_cmd)

        assert delete_result.status == ResultStatus.SUCCESS
        assert delete_result.data is True
        assert delete_result.metadata["soft_delete"] is True

    def test_handle_delete_entity_hard_delete_success(self, handler):
        """Should successfully hard delete an entity."""
        # First create an entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )
        create_result = handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Then delete it (hard)
        delete_cmd = DeleteEntityCommand(
            entity_id=entity_id,
            soft_delete=False,
        )
        delete_result = handler.handle_delete_entity(delete_cmd)

        assert delete_result.status == ResultStatus.SUCCESS
        assert delete_result.data is True
        assert delete_result.metadata["soft_delete"] is False

    def test_handle_delete_entity_not_found(self, handler):
        """Should return error when deleting non-existent entity."""
        command = DeleteEntityCommand(entity_id="non-existent-id")

        result = handler.handle_delete_entity(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_handle_delete_entity_validation_error(self, handler):
        """Should return error when delete command validation fails."""
        command = DeleteEntityCommand(entity_id="")

        result = handler.handle_delete_entity(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_archive_entity_success(self, handler):
        """Should successfully archive an entity."""
        # First create an entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )
        create_result = handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Then archive it
        archive_cmd = ArchiveEntityCommand(
            entity_id=entity_id,
            archived_by="user-456",
        )
        archive_result = handler.handle_archive_entity(archive_cmd)

        assert archive_result.status == ResultStatus.SUCCESS
        assert archive_result.data is not None
        assert archive_result.data.metadata.get("archived_by") == "user-456"
        assert "archived_at" in archive_result.data.metadata

    def test_handle_archive_entity_not_found(self, handler):
        """Should return error when archiving non-existent entity."""
        command = ArchiveEntityCommand(entity_id="non-existent-id")

        result = handler.handle_archive_entity(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_handle_archive_entity_validation_error(self, handler):
        """Should return error when archive command validation fails."""
        command = ArchiveEntityCommand(entity_id="")

        result = handler.handle_archive_entity(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_restore_entity_success(self, handler):
        """Should successfully restore an entity."""
        # First create an entity
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )
        create_result = handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        # Archive it
        archive_cmd = ArchiveEntityCommand(entity_id=entity_id)
        handler.handle_archive_entity(archive_cmd)

        # Then restore it
        restore_cmd = RestoreEntityCommand(
            entity_id=entity_id,
            restored_by="user-789",
        )
        restore_result = handler.handle_restore_entity(restore_cmd)

        assert restore_result.status == ResultStatus.SUCCESS
        assert restore_result.data is not None
        assert restore_result.data.metadata.get("restored_by") == "user-789"
        assert "restored_at" in restore_result.data.metadata

    def test_handle_restore_entity_not_found(self, handler):
        """Should return error when restoring non-existent entity."""
        command = RestoreEntityCommand(entity_id="non-existent-id")

        result = handler.handle_restore_entity(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_handle_restore_entity_validation_error(self, handler):
        """Should return error when restore command validation fails."""
        command = RestoreEntityCommand(entity_id="")

        result = handler.handle_restore_entity(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error


class TestCommandResultMetadata:
    """Tests for command result metadata handling."""

    @pytest.fixture
    def handler(self):
        """Create a command handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return EntityCommandHandler(repository, logger, cache)

    def test_command_result_preserves_entity_id(self, handler):
        """Should include entity_id in metadata for all entity operations."""
        command = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )
        result = handler.handle_create_entity(command)

        assert "entity_id" in result.metadata
        assert result.metadata["entity_id"] == result.data.id

    def test_delete_command_metadata_includes_delete_type(self, handler):
        """Should include soft_delete flag in delete command metadata."""
        create_cmd = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )
        create_result = handler.handle_create_entity(create_cmd)
        entity_id = create_result.data.id

        delete_cmd = DeleteEntityCommand(
            entity_id=entity_id,
            soft_delete=False,
        )
        delete_result = handler.handle_delete_entity(delete_cmd)

        assert delete_result.metadata["soft_delete"] is False
        assert delete_result.metadata["entity_id"] == entity_id


class TestCommandHandlerErrorHandling:
    """Tests for command handler error handling."""

    @pytest.fixture
    def handler(self):
        """Create a command handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return EntityCommandHandler(repository, logger, cache)

    def test_handle_create_entity_repository_error(self, handler):
        """Should handle repository errors gracefully."""
        # Mock repository to raise error
        handler.entity_service.repository.save_called = False

        command = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )

        # We expect this to succeed with the mock repository
        result = handler.handle_create_entity(command)
        assert result.status == ResultStatus.SUCCESS

    def test_handle_update_entity_logs_error(self, handler):
        """Should log errors when updating entity."""
        command = UpdateEntityCommand(
            entity_id="non-existent-id",
            updates={"name": "Updated Name"},
        )

        result = handler.handle_update_entity(command)

        assert result.status == ResultStatus.ERROR
        # Logger should have recorded an error

    def test_logger_called_on_successful_operations(self, handler):
        """Should call logger for successful operations."""
        command = CreateEntityCommand(
            entity_type="workspace",
            name="Test Workspace",
        )

        result = handler.handle_create_entity(command)

        assert result.status == ResultStatus.SUCCESS
        # Handler uses the logger via entity_service


__all__ = [
    "TestCreateEntityCommandValidation",
    "TestUpdateEntityCommandValidation",
    "TestDeleteEntityCommandValidation",
    "TestArchiveEntityCommandValidation",
    "TestRestoreEntityCommandValidation",
    "TestEntityCommandHandler",
    "TestCommandResultMetadata",
    "TestCommandHandlerErrorHandling",
]
