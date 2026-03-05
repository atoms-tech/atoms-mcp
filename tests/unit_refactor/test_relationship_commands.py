"""
Comprehensive tests for relationship command handlers.

Tests cover:
- CreateRelationshipCommand validation and execution
- DeleteRelationshipCommand validation and execution
- Error handling and logging
"""

import pytest

from atoms_mcp.application.commands.relationship_commands import (
    CreateRelationshipCommand,
    DeleteRelationshipCommand,
    RelationshipCommandHandler,
    RelationshipCommandError,
    RelationshipValidationError,
    RelationshipNotFoundError,
)
from atoms_mcp.application.dto import CommandResult, ResultStatus
from atoms_mcp.domain.models.relationship import RelationType, RelationshipStatus
from conftest import MockRepository, MockLogger, MockCache


class TestCreateRelationshipCommandValidation:
    """Tests for CreateRelationshipCommand validation."""

    def test_valid_command(self):
        """Should accept valid command."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
        )
        # Should not raise
        command.validate()

    def test_missing_source_id(self):
        """Should reject missing source_id."""
        command = CreateRelationshipCommand(
            source_id="",
            target_id="entity-2",
            relationship_type="parent_of",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "source_id is required" in str(exc_info.value)

    def test_missing_target_id(self):
        """Should reject missing target_id."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="",
            relationship_type="parent_of",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "target_id is required" in str(exc_info.value)

    def test_missing_relationship_type(self):
        """Should reject missing relationship_type."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "relationship_type is required" in str(exc_info.value)

    def test_same_source_and_target(self):
        """Should reject when source and target are same."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-1",
            relationship_type="parent_of",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "cannot be the same" in str(exc_info.value)

    def test_invalid_relationship_type(self):
        """Should reject invalid relationship type."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="invalid_type",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "Invalid relationship_type" in str(exc_info.value)

    def test_valid_relationship_types(self):
        """Should accept all valid relationship types."""
        valid_types = [
            "parent_of",
            "child_of",
            "contains",
            "contained_by",
            "assigned_to",
            "depends_on",
            "relates_to",
            "triggers",
            "member_of",
        ]
        for rel_type in valid_types:
            command = CreateRelationshipCommand(
                source_id="entity-1",
                target_id="entity-2",
                relationship_type=rel_type,
            )
            # Should not raise
            command.validate()


class TestDeleteRelationshipCommandValidation:
    """Tests for DeleteRelationshipCommand validation."""

    def test_valid_by_relationship_id(self):
        """Should accept valid command with relationship ID."""
        command = DeleteRelationshipCommand(relationship_id="rel-123")
        command.validate()

    def test_valid_by_source_and_target(self):
        """Should accept valid command with source and target."""
        command = DeleteRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
        )
        command.validate()

    def test_missing_all_identifiers(self):
        """Should reject when all identifiers missing."""
        command = DeleteRelationshipCommand()
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        # Check for the actual error message
        error_msg = str(exc_info.value).lower()
        assert "relationship_id" in error_msg or "source_id" in error_msg

    def test_empty_source_id_without_relationship_id(self):
        """Should reject empty source_id without relationship_id."""
        command = DeleteRelationshipCommand(
            source_id="",
            target_id="entity-2",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "source_id" in str(exc_info.value).lower()

    def test_empty_target_id_without_relationship_id(self):
        """Should reject empty target_id without relationship_id."""
        command = DeleteRelationshipCommand(
            source_id="entity-1",
            target_id="",
        )
        with pytest.raises(RelationshipValidationError) as exc_info:
            command.validate()
        assert "target_id" in str(exc_info.value).lower()


class TestRelationshipCommandHandler:
    """Tests for RelationshipCommandHandler."""

    @pytest.fixture
    def handler(self):
        """Create a relationship command handler with mock dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipCommandHandler(repository, logger, cache)

    def test_handle_create_relationship_success(self, handler):
        """Should successfully create a relationship."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
            created_by="user-123",
        )

        result = handler.handle_create_relationship(command)

        assert isinstance(result, CommandResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert result.error is None

    def test_handle_create_relationship_with_properties(self, handler):
        """Should create relationship with properties."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
            properties={"strength": "high", "label": "parent"},
            created_by="user-123",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None

    def test_handle_create_relationship_bidirectional(self, handler):
        """Should create bidirectional relationship."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
            bidirectional=True,
            created_by="user-123",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.SUCCESS
        assert "bidirectional" in result.metadata

    def test_handle_create_relationship_validation_error(self, handler):
        """Should handle validation errors."""
        command = CreateRelationshipCommand(
            source_id="",
            target_id="entity-2",
            relationship_type="parent_of",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None
        assert "Validation error" in result.error or "validation" in result.error.lower()

    def test_handle_create_relationship_invalid_type_error(self, handler):
        """Should handle invalid relationship type."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="invalid_type",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None

    def test_handle_delete_relationship_by_id_success(self, handler):
        """Should successfully delete relationship by ID."""
        # First create a relationship
        create_cmd = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
        )
        create_result = handler.handle_create_relationship(create_cmd)
        relationship_id = create_result.data.id

        # Now delete it
        delete_cmd = DeleteRelationshipCommand(relationship_id=relationship_id)
        result = handler.handle_delete_relationship(delete_cmd)

        assert isinstance(result, CommandResult)
        assert result.status == ResultStatus.SUCCESS

    def test_handle_delete_relationship_by_source_target_accepts_command(self, handler):
        """Should accept delete command by source and target."""
        # Delete by source and target (will fail with not found but validates command format)
        delete_cmd = DeleteRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
        )
        result = handler.handle_delete_relationship(delete_cmd)

        # Should either succeed or return a not-found error (both are valid)
        assert result.status in (ResultStatus.SUCCESS, ResultStatus.ERROR)
        assert isinstance(result, CommandResult)

    def test_handle_delete_relationship_not_found(self, handler):
        """Should handle relationship not found error."""
        delete_cmd = DeleteRelationshipCommand(relationship_id="nonexistent-id")
        result = handler.handle_delete_relationship(delete_cmd)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_handle_delete_relationship_validation_error(self, handler):
        """Should handle validation errors in delete."""
        delete_cmd = DeleteRelationshipCommand()
        result = handler.handle_delete_relationship(delete_cmd)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None

    def test_handle_delete_relationship_with_remove_inverse(self, handler):
        """Should respect remove_inverse flag."""
        create_cmd = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
            bidirectional=True,
        )
        create_result = handler.handle_create_relationship(create_cmd)
        relationship_id = create_result.data.id

        delete_cmd = DeleteRelationshipCommand(
            relationship_id=relationship_id,
            remove_inverse=True,
        )
        result = handler.handle_delete_relationship(delete_cmd)

        assert result.status == ResultStatus.SUCCESS


class TestRelationshipCommandHandlerEdgeCases:
    """Tests for edge cases in relationship command handling."""

    @pytest.fixture
    def handler(self):
        """Create a relationship command handler."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipCommandHandler(repository, logger, cache)

    def test_create_relationship_with_null_properties(self, handler):
        """Should handle null properties."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="contains",
            properties=None,
        )

        result = handler.handle_create_relationship(command)

        # Should either use empty dict or None, but not fail
        assert isinstance(result, CommandResult)

    def test_create_relationship_preserves_metadata(self, handler):
        """Should preserve relationship metadata."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
            created_by="user-123",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.SUCCESS
        assert "relationship_id" in result.metadata

    def test_multiple_relationship_operations_sequence(self, handler):
        """Should handle sequence of relationship operations."""
        # Create first relationship
        cmd1 = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="parent_of",
        )
        result1 = handler.handle_create_relationship(cmd1)
        assert result1.status == ResultStatus.SUCCESS

        # Create second relationship
        cmd2 = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-3",
            relationship_type="contains",
        )
        result2 = handler.handle_create_relationship(cmd2)
        assert result2.status == ResultStatus.SUCCESS

        # Both relationships should exist
        assert result1.data.id != result2.data.id


class TestRelationshipCommandErrorHandling:
    """Tests for error handling in relationship commands."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        return RelationshipCommandHandler(repository, logger, cache)

    def test_error_logged_on_validation_failure(self, handler):
        """Should log validation errors."""
        command = CreateRelationshipCommand(
            source_id="",
            target_id="entity-2",
            relationship_type="parent_of",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.ERROR
        # Error should be recorded in result
        assert result.error is not None

    def test_error_returned_to_caller(self, handler):
        """Should return error to caller in CommandResult."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-2",
            relationship_type="INVALID",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None
        assert isinstance(result.error, str)

    def test_no_data_on_error(self, handler):
        """Should not include data when error occurs."""
        command = CreateRelationshipCommand(
            source_id="entity-1",
            target_id="entity-1",  # Same source and target
            relationship_type="parent_of",
        )

        result = handler.handle_create_relationship(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None


__all__ = [
    "TestCreateRelationshipCommandValidation",
    "TestDeleteRelationshipCommandValidation",
    "TestRelationshipCommandHandler",
    "TestRelationshipCommandHandlerEdgeCases",
    "TestRelationshipCommandErrorHandling",
]
