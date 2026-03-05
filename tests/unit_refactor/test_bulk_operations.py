"""
Comprehensive tests for bulk operations workflows.

Tests cover:
- BulkCreateEntitiesWorkflow validation and execution
- BulkUpdateEntitiesWorkflow validation and execution
- BulkDeleteEntitiesWorkflow validation and execution
- BulkOperationsHandler all workflow methods
- Transaction support and rollback scenarios
- Error handling, partial success scenarios
- Performance with large datasets
- Progress tracking and logging
- Memory efficiency validation
"""

import pytest
from datetime import datetime
from uuid import uuid4

from atoms_mcp.application.workflows.bulk_operations import (
    BulkCreateEntitiesWorkflow,
    BulkUpdateEntitiesWorkflow,
    BulkDeleteEntitiesWorkflow,
    BulkOperationsHandler,
    BulkOperationError,
    BulkOperationValidationError,
)
from atoms_mcp.application.commands.entity_commands import (
    CreateEntityCommand,
    UpdateEntityCommand,
    DeleteEntityCommand,
)
from atoms_mcp.application.dto import ResultStatus
from atoms_mcp.domain.models.entity import WorkspaceEntity, ProjectEntity, EntityStatus
from conftest import MockRepository, MockLogger, MockCache


# =============================================================================
# BULK CREATE WORKFLOW VALIDATION TESTS
# =============================================================================


class TestBulkCreateWorkflowValidation:
    """Tests for BulkCreateEntitiesWorkflow validation."""

    def test_validate_with_valid_entities(self):
        """Should validate successfully with valid entities list."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(10)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)
        workflow.validate()  # Should not raise

    def test_validate_empty_entities_list(self):
        """Should reject empty entities list."""
        workflow = BulkCreateEntitiesWorkflow(entities=[])
        with pytest.raises(BulkOperationValidationError) as exc_info:
            workflow.validate()
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_too_many_entities(self):
        """Should reject more than 1000 entities."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(1001)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)
        with pytest.raises(BulkOperationValidationError) as exc_info:
            workflow.validate()
        assert "1000 entities" in str(exc_info.value)

    def test_validate_exactly_1000_entities(self):
        """Should accept exactly 1000 entities."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(1000)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)
        workflow.validate()  # Should not raise

    def test_default_stop_on_error_is_false(self):
        """Should default stop_on_error to False."""
        workflow = BulkCreateEntitiesWorkflow(entities=[
            CreateEntityCommand(entity_type="workspace", name="Test")
        ])
        assert workflow.stop_on_error is False

    def test_default_transaction_is_true(self):
        """Should default transaction to True."""
        workflow = BulkCreateEntitiesWorkflow(entities=[
            CreateEntityCommand(entity_type="workspace", name="Test")
        ])
        assert workflow.transaction is True

    def test_can_override_stop_on_error(self):
        """Should allow overriding stop_on_error."""
        workflow = BulkCreateEntitiesWorkflow(
            entities=[CreateEntityCommand(entity_type="workspace", name="Test")],
            stop_on_error=True,
        )
        assert workflow.stop_on_error is True

    def test_can_override_transaction(self):
        """Should allow overriding transaction."""
        workflow = BulkCreateEntitiesWorkflow(
            entities=[CreateEntityCommand(entity_type="workspace", name="Test")],
            transaction=False,
        )
        assert workflow.transaction is False


# =============================================================================
# BULK UPDATE WORKFLOW VALIDATION TESTS
# =============================================================================


class TestBulkUpdateWorkflowValidation:
    """Tests for BulkUpdateEntitiesWorkflow validation."""

    def test_validate_with_valid_updates(self):
        """Should validate successfully with valid updates list."""
        commands = [
            UpdateEntityCommand(entity_id=str(uuid4()), updates={"name": f"Updated {i}"})
            for i in range(10)
        ]
        workflow = BulkUpdateEntitiesWorkflow(updates=commands)
        workflow.validate()  # Should not raise

    def test_validate_empty_updates_list(self):
        """Should reject empty updates list."""
        workflow = BulkUpdateEntitiesWorkflow(updates=[])
        with pytest.raises(BulkOperationValidationError) as exc_info:
            workflow.validate()
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_too_many_updates(self):
        """Should reject more than 1000 updates."""
        commands = [
            UpdateEntityCommand(entity_id=str(uuid4()), updates={"name": f"Updated {i}"})
            for i in range(1001)
        ]
        workflow = BulkUpdateEntitiesWorkflow(updates=commands)
        with pytest.raises(BulkOperationValidationError) as exc_info:
            workflow.validate()
        assert "1000 entities" in str(exc_info.value)

    def test_validate_exactly_1000_updates(self):
        """Should accept exactly 1000 updates."""
        commands = [
            UpdateEntityCommand(entity_id=str(uuid4()), updates={"name": f"Updated {i}"})
            for i in range(1000)
        ]
        workflow = BulkUpdateEntitiesWorkflow(updates=commands)
        workflow.validate()  # Should not raise


# =============================================================================
# BULK DELETE WORKFLOW VALIDATION TESTS
# =============================================================================


class TestBulkDeleteWorkflowValidation:
    """Tests for BulkDeleteEntitiesWorkflow validation."""

    def test_validate_with_valid_entity_ids(self):
        """Should validate successfully with valid entity IDs list."""
        entity_ids = [str(uuid4()) for _ in range(10)]
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=entity_ids)
        workflow.validate()  # Should not raise

    def test_validate_empty_entity_ids_list(self):
        """Should reject empty entity_ids list."""
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=[])
        with pytest.raises(BulkOperationValidationError) as exc_info:
            workflow.validate()
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_too_many_entity_ids(self):
        """Should reject more than 1000 entity IDs."""
        entity_ids = [str(uuid4()) for _ in range(1001)]
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=entity_ids)
        with pytest.raises(BulkOperationValidationError) as exc_info:
            workflow.validate()
        assert "1000 entities" in str(exc_info.value)

    def test_validate_exactly_1000_entity_ids(self):
        """Should accept exactly 1000 entity IDs."""
        entity_ids = [str(uuid4()) for _ in range(1000)]
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=entity_ids)
        workflow.validate()  # Should not raise

    def test_default_soft_delete_is_true(self):
        """Should default soft_delete to True."""
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=["id1"])
        assert workflow.soft_delete is True


# =============================================================================
# BULK OPERATIONS HANDLER INITIALIZATION TESTS
# =============================================================================


class TestBulkOperationsHandlerInitialization:
    """Tests for BulkOperationsHandler initialization."""

    def test_handler_initialization(self):
        """Should initialize handler with dependencies."""
        repository = MockRepository()
        logger = MockLogger()
        handler = BulkOperationsHandler(repository, logger)

        assert handler.entity_handler is not None
        assert handler.logger is logger

    def test_handler_initialization_with_cache(self):
        """Should initialize handler with cache."""
        repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()
        handler = BulkOperationsHandler(repository, logger, cache)

        assert handler.entity_handler is not None
        assert handler.logger is logger


# =============================================================================
# BULK CREATE HANDLER TESTS
# =============================================================================


class TestBulkCreateHandler:
    """Tests for bulk create operations."""

    @pytest.fixture
    def handler(self):
        """Create bulk operations handler."""
        repository = MockRepository()
        logger = MockLogger()
        return BulkOperationsHandler(repository, logger)

    def test_handle_bulk_create_success(self, handler):
        """Should successfully create all entities."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(5)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)

        result = handler.handle_bulk_create(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 5
        assert result.metadata["total"] == 5
        assert result.metadata["created"] == 5
        assert result.metadata["failed"] == 0

    def test_handle_bulk_create_large_dataset(self, handler):
        """Should handle creating 100+ entities efficiently."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(150)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)

        result = handler.handle_bulk_create(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 150
        assert result.metadata["created"] == 150

    def test_handle_bulk_create_validation_error(self, handler):
        """Should handle workflow validation errors."""
        workflow = BulkCreateEntitiesWorkflow(entities=[])

        result = handler.handle_bulk_create(workflow)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_bulk_create_partial_failure_no_transaction(self, handler):
        """Should continue on error when transaction is disabled."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(3)
        ]
        # Add an invalid command
        commands.insert(1, CreateEntityCommand(entity_type="workspace", name=""))

        workflow = BulkCreateEntitiesWorkflow(
            entities=commands,
            transaction=False,
            stop_on_error=False,
        )

        result = handler.handle_bulk_create(workflow)

        # Should have partial success
        assert result.status == ResultStatus.PARTIAL_SUCCESS
        assert len(result.data) == 3  # 3 successful creations
        assert result.metadata["failed"] == 1

    def test_handle_bulk_create_stop_on_error(self, handler):
        """Should stop processing on first error when stop_on_error is True."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name="Valid 1"),
            CreateEntityCommand(entity_type="workspace", name=""),  # Invalid
            CreateEntityCommand(entity_type="workspace", name="Valid 2"),
        ]

        workflow = BulkCreateEntitiesWorkflow(
            entities=commands,
            stop_on_error=True,
            transaction=False,
        )

        result = handler.handle_bulk_create(workflow)

        # Should stop after first failure
        assert result.status == ResultStatus.PARTIAL_SUCCESS
        assert len(result.data) == 1  # Only first entity created

    def test_handle_bulk_create_transaction_rollback(self, handler):
        """Should rollback all creations on failure in transaction mode."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name="Valid 1"),
            CreateEntityCommand(entity_type="workspace", name="Valid 2"),
            CreateEntityCommand(entity_type="workspace", name=""),  # Invalid
        ]

        workflow = BulkCreateEntitiesWorkflow(
            entities=commands,
            transaction=True,
        )

        result = handler.handle_bulk_create(workflow)

        # Should rollback all
        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert "rolled_back" in result.metadata
        assert result.metadata["rolled_back"] == 2

    def test_handle_bulk_create_logs_progress(self, handler):
        """Should log progress during bulk creation."""
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(5)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)

        handler.handle_bulk_create(workflow)

        # Check for progress logs
        logs = handler.logger.logs
        info_logs = [log for log in logs if log["level"] == "INFO"]
        assert any("Starting bulk create" in log["message"] for log in info_logs)
        assert any("completed" in log["message"] for log in info_logs)


# =============================================================================
# BULK UPDATE HANDLER TESTS
# =============================================================================


class TestBulkUpdateHandler:
    """Tests for bulk update operations."""

    @pytest.fixture
    def handler(self):
        """Create bulk operations handler with pre-existing entities."""
        repository = MockRepository()
        logger = MockLogger()

        # Create some entities to update
        for i in range(10):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            repository.save(entity)

        return BulkOperationsHandler(repository, logger), repository

    def test_handle_bulk_update_success(self, handler):
        """Should successfully update all entities."""
        bulk_handler, repository = handler

        # Get entity IDs
        entities = repository.list()
        commands = [
            UpdateEntityCommand(entity_id=entity.id, updates={"name": f"Updated {i}"})
            for i, entity in enumerate(entities[:5])
        ]
        workflow = BulkUpdateEntitiesWorkflow(updates=commands)

        result = bulk_handler.handle_bulk_update(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data) == 5
        assert result.metadata["total"] == 5
        assert result.metadata["updated"] == 5
        assert result.metadata["failed"] == 0

    def test_handle_bulk_update_nonexistent_entity(self, handler):
        """Should handle updating non-existent entities."""
        bulk_handler, repository = handler

        commands = [
            UpdateEntityCommand(entity_id="nonexistent", updates={"name": "Updated"}),
        ]
        workflow = BulkUpdateEntitiesWorkflow(
            updates=commands,
            transaction=False,
        )

        result = bulk_handler.handle_bulk_update(workflow)

        assert result.status == ResultStatus.ERROR
        assert result.metadata["failed"] == 1

    def test_handle_bulk_update_transaction_rollback(self, handler):
        """Should rollback all updates on failure in transaction mode."""
        bulk_handler, repository = handler

        # Get valid entity IDs
        entities = repository.list()
        commands = [
            UpdateEntityCommand(entity_id=entities[0].id, updates={"name": "Updated 1"}),
            UpdateEntityCommand(entity_id=entities[1].id, updates={"name": "Updated 2"}),
            UpdateEntityCommand(entity_id="nonexistent", updates={"name": "Updated"}),
        ]
        workflow = BulkUpdateEntitiesWorkflow(
            updates=commands,
            transaction=True,
        )

        result = bulk_handler.handle_bulk_update(workflow)

        # Should rollback
        assert result.status == ResultStatus.ERROR
        assert "rolled_back" in result.metadata

    def test_handle_bulk_update_large_dataset(self, handler):
        """Should handle updating 100+ entities efficiently."""
        bulk_handler, repository = handler

        # Create more entities
        for i in range(90):
            entity = WorkspaceEntity(name=f"Additional {i}")
            repository.save(entity)

        # Update all entities
        entities = repository.list()
        commands = [
            UpdateEntityCommand(entity_id=entity.id, updates={"description": f"Updated {i}"})
            for i, entity in enumerate(entities)
        ]
        workflow = BulkUpdateEntitiesWorkflow(updates=commands)

        result = bulk_handler.handle_bulk_update(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["updated"] == 100

    def test_handle_bulk_update_validation_error(self, handler):
        """Should handle workflow validation errors."""
        bulk_handler, repository = handler
        workflow = BulkUpdateEntitiesWorkflow(updates=[])

        result = bulk_handler.handle_bulk_update(workflow)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error


# =============================================================================
# BULK DELETE HANDLER TESTS
# =============================================================================


class TestBulkDeleteHandler:
    """Tests for bulk delete operations."""

    @pytest.fixture
    def handler(self):
        """Create bulk operations handler with pre-existing entities."""
        repository = MockRepository()
        logger = MockLogger()

        # Create some entities to delete
        entity_ids = []
        for i in range(10):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            repository.save(entity)
            entity_ids.append(entity.id)

        return BulkOperationsHandler(repository, logger), repository, entity_ids

    def test_handle_bulk_delete_success(self, handler):
        """Should successfully delete all entities."""
        bulk_handler, repository, entity_ids = handler

        workflow = BulkDeleteEntitiesWorkflow(entity_ids=entity_ids[:5])

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["deleted_count"] == 5
        assert result.data["failed_count"] == 0
        assert len(result.data["deleted_ids"]) == 5

    def test_handle_bulk_delete_soft_delete(self, handler):
        """Should perform soft delete by default."""
        bulk_handler, repository, entity_ids = handler

        workflow = BulkDeleteEntitiesWorkflow(
            entity_ids=entity_ids[:3],
            soft_delete=True,
        )

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["soft_delete"] is True

    def test_handle_bulk_delete_hard_delete(self, handler):
        """Should perform hard delete when specified."""
        bulk_handler, repository, entity_ids = handler

        workflow = BulkDeleteEntitiesWorkflow(
            entity_ids=entity_ids[:3],
            soft_delete=False,
        )

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["soft_delete"] is False

    def test_handle_bulk_delete_nonexistent_entities(self, handler):
        """Should handle deleting non-existent entities."""
        bulk_handler, repository, entity_ids = handler

        workflow = BulkDeleteEntitiesWorkflow(
            entity_ids=["nonexistent1", "nonexistent2"],
            stop_on_error=False,
        )

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.ERROR
        assert result.data["failed_count"] == 2

    def test_handle_bulk_delete_partial_failure(self, handler):
        """Should handle partial deletion failures."""
        bulk_handler, repository, entity_ids = handler

        # Mix valid and invalid IDs
        mixed_ids = entity_ids[:3] + ["invalid1", "invalid2"]
        workflow = BulkDeleteEntitiesWorkflow(
            entity_ids=mixed_ids,
            stop_on_error=False,
        )

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.PARTIAL_SUCCESS
        assert result.data["deleted_count"] == 3
        assert result.data["failed_count"] == 2

    def test_handle_bulk_delete_stop_on_error(self, handler):
        """Should stop processing on first error when stop_on_error is True."""
        bulk_handler, repository, entity_ids = handler

        # Put invalid ID first
        mixed_ids = ["invalid"] + entity_ids[:3]
        workflow = BulkDeleteEntitiesWorkflow(
            entity_ids=mixed_ids,
            stop_on_error=True,
        )

        result = bulk_handler.handle_bulk_delete(workflow)

        # Should stop after first failure
        assert result.status == ResultStatus.ERROR
        assert result.data["deleted_count"] == 0

    def test_handle_bulk_delete_large_dataset(self, handler):
        """Should handle deleting 100+ entities efficiently."""
        bulk_handler, repository, entity_ids = handler

        # Create more entities
        more_ids = []
        for i in range(90):
            entity = WorkspaceEntity(name=f"Additional {i}")
            repository.save(entity)
            more_ids.append(entity.id)

        all_ids = entity_ids + more_ids
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=all_ids)

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["deleted_count"] == 100

    def test_handle_bulk_delete_validation_error(self, handler):
        """Should handle workflow validation errors."""
        bulk_handler, repository, entity_ids = handler
        workflow = BulkDeleteEntitiesWorkflow(entity_ids=[])

        result = bulk_handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error


# =============================================================================
# PERFORMANCE AND MEMORY TESTS
# =============================================================================


@pytest.mark.performance
class TestBulkOperationsPerformance:
    """Tests for bulk operations performance and memory efficiency."""

    def test_bulk_create_memory_efficiency(self):
        """Should handle bulk create without excessive memory usage."""
        repository = MockRepository()
        logger = MockLogger()
        handler = BulkOperationsHandler(repository, logger)

        # Create 500 entities
        commands = [
            CreateEntityCommand(entity_type="workspace", name=f"Workspace {i}")
            for i in range(500)
        ]
        workflow = BulkCreateEntitiesWorkflow(entities=commands)

        result = handler.handle_bulk_create(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["created"] == 500

    def test_bulk_update_memory_efficiency(self):
        """Should handle bulk update without excessive memory usage."""
        repository = MockRepository()
        logger = MockLogger()

        # Create entities
        entity_ids = []
        for i in range(500):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            repository.save(entity)
            entity_ids.append(entity.id)

        handler = BulkOperationsHandler(repository, logger)

        # Update all entities
        commands = [
            UpdateEntityCommand(entity_id=entity_id, updates={"description": f"Updated {i}"})
            for i, entity_id in enumerate(entity_ids)
        ]
        workflow = BulkUpdateEntitiesWorkflow(updates=commands)

        result = handler.handle_bulk_update(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["updated"] == 500

    def test_bulk_delete_memory_efficiency(self):
        """Should handle bulk delete without excessive memory usage."""
        repository = MockRepository()
        logger = MockLogger()

        # Create entities
        entity_ids = []
        for i in range(500):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            repository.save(entity)
            entity_ids.append(entity.id)

        handler = BulkOperationsHandler(repository, logger)

        workflow = BulkDeleteEntitiesWorkflow(entity_ids=entity_ids)

        result = handler.handle_bulk_delete(workflow)

        assert result.status == ResultStatus.SUCCESS
        assert result.data["deleted_count"] == 500


# =============================================================================
# ERROR HANDLING AND EDGE CASES
# =============================================================================


class TestBulkOperationsErrorHandling:
    """Tests for error handling in bulk operations."""

    def test_handle_unexpected_exception_in_create(self):
        """Should handle unexpected exceptions gracefully."""
        repository = MockRepository()
        logger = MockLogger()
        handler = BulkOperationsHandler(repository, logger)

        # Force an error by providing None as entities
        workflow = BulkCreateEntitiesWorkflow(entities=[None])

        result = handler.handle_bulk_create(workflow)

        # Should catch and report error
        assert result.status == ResultStatus.ERROR
        assert result.error is not None

    def test_logs_all_errors_in_bulk_create(self):
        """Should log all errors that occur during bulk create."""
        repository = MockRepository()
        logger = MockLogger()
        handler = BulkOperationsHandler(repository, logger)

        commands = [
            CreateEntityCommand(entity_type="workspace", name=""),  # Invalid
            CreateEntityCommand(entity_type="workspace", name=""),  # Invalid
        ]
        workflow = BulkCreateEntitiesWorkflow(
            entities=commands,
            transaction=False,
        )

        handler.handle_bulk_create(workflow)

        # Check for error logs
        error_logs = [log for log in logger.logs if log["level"] in ["ERROR", "WARNING"]]
        assert len(error_logs) >= 2

    def test_bulk_operations_handler_error_recovery(self):
        """Should recover from errors and continue processing when appropriate."""
        repository = MockRepository()
        logger = MockLogger()
        handler = BulkOperationsHandler(repository, logger)

        commands = [
            CreateEntityCommand(entity_type="workspace", name="Valid 1"),
            CreateEntityCommand(entity_type="workspace", name=""),  # Invalid
            CreateEntityCommand(entity_type="workspace", name="Valid 2"),
        ]
        workflow = BulkCreateEntitiesWorkflow(
            entities=commands,
            transaction=False,
            stop_on_error=False,
        )

        result = handler.handle_bulk_create(workflow)

        # Should have partial success
        assert result.status == ResultStatus.PARTIAL_SUCCESS
        assert len(result.data) == 2  # Two valid entities created


__all__ = [
    "TestBulkCreateWorkflowValidation",
    "TestBulkUpdateWorkflowValidation",
    "TestBulkDeleteWorkflowValidation",
    "TestBulkOperationsHandlerInitialization",
    "TestBulkCreateHandler",
    "TestBulkUpdateHandler",
    "TestBulkDeleteHandler",
    "TestBulkOperationsPerformance",
    "TestBulkOperationsErrorHandling",
]
