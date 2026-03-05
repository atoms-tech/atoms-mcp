"""
Comprehensive tests for workflow command handlers.

Tests cover:
- CreateWorkflowCommand validation and execution
- UpdateWorkflowCommand validation and execution
- ExecuteWorkflowCommand validation and execution
- CancelWorkflowExecutionCommand validation and execution
- WorkflowCommandHandler all command methods
- Error handling, workflow validation
- Step execution, cancellation scenarios
"""

import pytest
from datetime import datetime
from uuid import uuid4

from atoms_mcp.application.commands.workflow_commands import (
    CreateWorkflowCommand,
    UpdateWorkflowCommand,
    ExecuteWorkflowCommand,
    CancelWorkflowExecutionCommand,
    WorkflowCommandHandler,
    WorkflowCommandError,
    WorkflowValidationError,
    WorkflowNotFoundError,
)
from atoms_mcp.application.dto import CommandResult, ResultStatus, WorkflowDTO, WorkflowExecutionDTO
from atoms_mcp.domain.models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
    Action,
    ActionType,
    Trigger,
    TriggerType,
)
from conftest import MockRepository, MockLogger, MockCache


class TestCreateWorkflowCommandValidation:
    """Tests for CreateWorkflowCommand validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            description="A test workflow",
        )
        command.validate()  # Should not raise

    def test_validate_missing_name(self):
        """Should reject missing name."""
        command = CreateWorkflowCommand(name="")
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "name is required" in str(exc_info.value)

    def test_validate_name_too_long(self):
        """Should reject name exceeding 255 characters."""
        long_name = "a" * 256
        command = CreateWorkflowCommand(name=long_name)
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "255 characters" in str(exc_info.value)

    def test_validate_name_exactly_255_characters(self):
        """Should accept name of exactly 255 characters."""
        name_255 = "a" * 255
        command = CreateWorkflowCommand(name=name_255)
        command.validate()  # Should not raise

    def test_validate_invalid_trigger_type(self):
        """Should reject invalid trigger type."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            trigger_type="invalid_trigger",
        )
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "Invalid trigger_type" in str(exc_info.value)

    def test_validate_valid_trigger_types(self):
        """Should accept all valid trigger types."""
        # Updated to match actual TriggerType enum values
        valid_types = [
            "entity_created",
            "entity_updated",
            "entity_deleted",
            "status_changed",
            "field_changed",
            "scheduled",
            "manual",
            "webhook",
        ]
        for trigger_type in valid_types:
            command = CreateWorkflowCommand(
                name="Test Workflow",
                trigger_type=trigger_type,
            )
            command.validate()  # Should not raise

    def test_validate_with_steps(self):
        """Should validate successfully with workflow steps."""
        steps = [
            {
                "name": "Step 1",
                "description": "First step",
                "action": {
                    "action_type": "execute_script",
                    "config": {"script": "test.sh"},
                },
            }
        ]
        command = CreateWorkflowCommand(
            name="Test Workflow",
            steps=steps,
        )
        command.validate()  # Should not raise

    def test_validate_with_all_fields(self):
        """Should validate with all optional fields."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            description="Test description",
            trigger_type="scheduled",
            trigger_config={"cron": "0 0 * * *"},
            steps=[],
            enabled=False,
            created_by="user-123",
        )
        command.validate()  # Should not raise


class TestUpdateWorkflowCommandValidation:
    """Tests for UpdateWorkflowCommand validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        command = UpdateWorkflowCommand(
            workflow_id="workflow-123",
            updates={"name": "Updated Name"},
        )
        command.validate()  # Should not raise

    def test_validate_missing_workflow_id(self):
        """Should reject missing workflow_id."""
        command = UpdateWorkflowCommand(
            workflow_id="",
            updates={"name": "Updated Name"},
        )
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "workflow_id is required" in str(exc_info.value)

    def test_validate_empty_updates(self):
        """Should reject empty updates dictionary."""
        command = UpdateWorkflowCommand(
            workflow_id="workflow-123",
            updates={},
        )
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "updates cannot be empty" in str(exc_info.value)

    def test_validate_cannot_update_id(self):
        """Should reject updating workflow id."""
        command = UpdateWorkflowCommand(
            workflow_id="workflow-123",
            updates={"id": "new-id"},
        )
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "cannot update workflow id" in str(exc_info.value)

    def test_validate_can_update_other_fields(self):
        """Should accept updating non-id fields."""
        command = UpdateWorkflowCommand(
            workflow_id="workflow-123",
            updates={
                "name": "New Name",
                "description": "New description",
                "enabled": False,
            },
        )
        command.validate()  # Should not raise


class TestExecuteWorkflowCommandValidation:
    """Tests for ExecuteWorkflowCommand validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        command = ExecuteWorkflowCommand(workflow_id="workflow-123")
        command.validate()  # Should not raise

    def test_validate_missing_workflow_id(self):
        """Should reject missing workflow_id."""
        command = ExecuteWorkflowCommand(workflow_id="")
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "workflow_id is required" in str(exc_info.value)

    def test_validate_with_context(self):
        """Should validate with execution context."""
        command = ExecuteWorkflowCommand(
            workflow_id="workflow-123",
            context={"key": "value"},
        )
        command.validate()  # Should not raise

    def test_validate_with_triggered_by(self):
        """Should validate with triggered_by field."""
        command = ExecuteWorkflowCommand(
            workflow_id="workflow-123",
            triggered_by="user-456",
        )
        command.validate()  # Should not raise


class TestCancelWorkflowExecutionCommandValidation:
    """Tests for CancelWorkflowExecutionCommand validation."""

    def test_validate_with_valid_parameters(self):
        """Should validate successfully with valid parameters."""
        command = CancelWorkflowExecutionCommand(execution_id="execution-123")
        command.validate()  # Should not raise

    def test_validate_missing_execution_id(self):
        """Should reject missing execution_id."""
        command = CancelWorkflowExecutionCommand(execution_id="")
        with pytest.raises(WorkflowValidationError) as exc_info:
            command.validate()
        assert "execution_id is required" in str(exc_info.value)

    def test_validate_with_cancelled_by(self):
        """Should validate with cancelled_by field."""
        command = CancelWorkflowExecutionCommand(
            execution_id="execution-123",
            cancelled_by="user-456",
        )
        command.validate()  # Should not raise


class TestWorkflowCommandHandler:
    """Tests for WorkflowCommandHandler."""

    @pytest.fixture
    def handler(self):
        """Create a workflow command handler with mock dependencies."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()

        # Use workflow_repository for the service initialization
        # The service expects (workflow_repo, execution_repo, logger)
        from atoms_mcp.domain.services.workflow_service import WorkflowService

        handler = WorkflowCommandHandler(workflow_repository, logger, cache)
        # Override the service's execution_repository to use our mock
        handler.workflow_service.execution_repository = execution_repository
        return handler

    def test_handler_initialization(self, handler):
        """Should initialize handler with dependencies."""
        assert handler.workflow_service is not None
        assert handler.logger is not None

    def test_handle_create_workflow_success(self, handler):
        """Should successfully create a workflow."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            description="A test workflow",
            trigger_type="manual",
            enabled=True,
            created_by="user-123",
        )

        result = handler.handle_create_workflow(command)

        assert isinstance(result, CommandResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, WorkflowDTO)
        assert result.data.name == "Test Workflow"
        assert "workflow_id" in result.metadata

    def test_handle_create_workflow_with_steps(self, handler):
        """Should create workflow with steps."""
        steps = [
            {
                "name": "Step 1",
                "description": "First step",
                "action": {
                    "action_type": "execute_script",
                    "config": {"script": "test.sh"},
                },
            }
        ]
        command = CreateWorkflowCommand(
            name="Test Workflow",
            steps=steps,
        )

        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.SUCCESS
        assert len(result.data.steps) == 1
        assert result.data.steps[0]["name"] == "Step 1"

    def test_handle_create_workflow_validation_error(self, handler):
        """Should handle validation errors."""
        command = CreateWorkflowCommand(name="")

        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.ERROR
        assert result.error is not None
        assert "Validation error" in result.error

    def test_handle_create_workflow_invalid_workflow(self, handler):
        """Should handle workflow validation failures."""
        # Create workflow with invalid steps (missing required fields)
        steps = [
            {
                "name": "",  # Empty name - should fail validation
                "action": {
                    "action_type": "execute_script",
                    "config": {},
                },
            }
        ]
        command = CreateWorkflowCommand(
            name="Test Workflow",
            steps=steps,
        )

        result = handler.handle_create_workflow(command)

        # Should fail during workflow validation
        assert result.status == ResultStatus.ERROR

    def test_handle_update_workflow_success(self, handler):
        """Should successfully update a workflow."""
        # First create a workflow
        create_cmd = CreateWorkflowCommand(name="Original Name")
        create_result = handler.handle_create_workflow(create_cmd)
        workflow_id = create_result.data.id

        # Now update it
        update_cmd = UpdateWorkflowCommand(
            workflow_id=workflow_id,
            updates={"name": "Updated Name"},
        )
        result = handler.handle_update_workflow(update_cmd)

        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert "workflow_id" in result.metadata

    def test_handle_update_workflow_not_found(self, handler):
        """Should handle workflow not found."""
        command = UpdateWorkflowCommand(
            workflow_id="nonexistent-id",
            updates={"name": "Updated Name"},
        )

        result = handler.handle_update_workflow(command)

        assert result.status == ResultStatus.ERROR
        assert "not found" in result.error.lower()

    def test_handle_update_workflow_validation_error(self, handler):
        """Should handle validation errors."""
        command = UpdateWorkflowCommand(
            workflow_id="",
            updates={"name": "Updated Name"},
        )

        result = handler.handle_update_workflow(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_execute_workflow_success(self, handler):
        """Should successfully execute a workflow."""
        # First create a workflow
        create_cmd = CreateWorkflowCommand(
            name="Test Workflow",
            enabled=True,
        )
        create_result = handler.handle_create_workflow(create_cmd)
        workflow_id = create_result.data.id

        # Now execute it
        execute_cmd = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            context={"test": "data"},
            triggered_by="user-123",
        )
        result = handler.handle_execute_workflow(execute_cmd)

        assert isinstance(result, CommandResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is not None
        assert isinstance(result.data, WorkflowExecutionDTO)
        assert "execution_id" in result.metadata

    def test_handle_execute_workflow_with_context(self, handler):
        """Should execute workflow with context data."""
        create_cmd = CreateWorkflowCommand(name="Test Workflow", enabled=True)
        create_result = handler.handle_create_workflow(create_cmd)

        execute_cmd = ExecuteWorkflowCommand(
            workflow_id=create_result.data.id,
            context={"key1": "value1", "key2": 123},
        )
        result = handler.handle_execute_workflow(execute_cmd)

        assert result.status == ResultStatus.SUCCESS
        assert result.data.workflow_id == create_result.data.id

    def test_handle_execute_workflow_not_found(self, handler):
        """Should handle workflow not found."""
        command = ExecuteWorkflowCommand(workflow_id="nonexistent-id")

        result = handler.handle_execute_workflow(command)

        assert result.status == ResultStatus.ERROR
        assert "not found" in result.error.lower()

    def test_handle_execute_workflow_validation_error(self, handler):
        """Should handle validation errors."""
        command = ExecuteWorkflowCommand(workflow_id="")

        result = handler.handle_execute_workflow(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error

    def test_handle_cancel_workflow_execution_success(self, handler):
        """Should successfully cancel a workflow execution."""
        # Create and execute a workflow
        create_cmd = CreateWorkflowCommand(name="Test Workflow", enabled=True)
        create_result = handler.handle_create_workflow(create_cmd)

        execute_cmd = ExecuteWorkflowCommand(workflow_id=create_result.data.id)
        execute_result = handler.handle_execute_workflow(execute_cmd)
        execution_id = execute_result.data.id

        # Now cancel it
        cancel_cmd = CancelWorkflowExecutionCommand(
            execution_id=execution_id,
            cancelled_by="user-456",
        )
        result = handler.handle_cancel_workflow_execution(cancel_cmd)

        assert isinstance(result, CommandResult)
        assert result.status == ResultStatus.SUCCESS
        assert result.data is True
        assert "execution_id" in result.metadata

    def test_handle_cancel_workflow_execution_not_found(self, handler):
        """Should handle execution not found."""
        command = CancelWorkflowExecutionCommand(execution_id="nonexistent-id")

        result = handler.handle_cancel_workflow_execution(command)

        assert result.status == ResultStatus.ERROR
        assert "not found" in result.error.lower()

    def test_handle_cancel_workflow_execution_validation_error(self, handler):
        """Should handle validation errors."""
        command = CancelWorkflowExecutionCommand(execution_id="")

        result = handler.handle_cancel_workflow_execution(command)

        assert result.status == ResultStatus.ERROR
        assert "Validation error" in result.error


class TestWorkflowCommandHandlerEventPublishing:
    """Tests for event publishing in workflow command handler."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()

        handler = WorkflowCommandHandler(workflow_repository, logger, cache)
        handler.workflow_service.execution_repository = execution_repository
        return handler

    def test_create_workflow_publishes_event(self, handler):
        """Should publish workflow.created event."""
        command = CreateWorkflowCommand(name="Test Workflow")
        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.SUCCESS
        # Check logs for event publishing
        info_logs = [log for log in handler.logger.logs if log["level"] == "INFO"]
        assert any("workflow.created" in log["message"] for log in info_logs)

    def test_update_workflow_publishes_event(self, handler):
        """Should publish workflow.updated event."""
        create_cmd = CreateWorkflowCommand(name="Test Workflow")
        create_result = handler.handle_create_workflow(create_cmd)

        handler.logger.clear_logs()  # Clear previous logs

        update_cmd = UpdateWorkflowCommand(
            workflow_id=create_result.data.id,
            updates={"description": "Updated"},
        )
        result = handler.handle_update_workflow(update_cmd)

        assert result.status == ResultStatus.SUCCESS
        info_logs = [log for log in handler.logger.logs if log["level"] == "INFO"]
        assert any("workflow.updated" in log["message"] for log in info_logs)

    def test_execute_workflow_publishes_event(self, handler):
        """Should publish workflow.execution.started event."""
        create_cmd = CreateWorkflowCommand(name="Test Workflow", enabled=True)
        create_result = handler.handle_create_workflow(create_cmd)

        handler.logger.clear_logs()

        execute_cmd = ExecuteWorkflowCommand(workflow_id=create_result.data.id)
        result = handler.handle_execute_workflow(execute_cmd)

        assert result.status == ResultStatus.SUCCESS
        info_logs = [log for log in handler.logger.logs if log["level"] == "INFO"]
        assert any("workflow.execution.started" in log["message"] for log in info_logs)

    def test_cancel_execution_publishes_event(self, handler):
        """Should publish workflow.execution.cancelled event."""
        create_cmd = CreateWorkflowCommand(name="Test Workflow", enabled=True)
        create_result = handler.handle_create_workflow(create_cmd)

        execute_cmd = ExecuteWorkflowCommand(workflow_id=create_result.data.id)
        execute_result = handler.handle_execute_workflow(execute_cmd)

        handler.logger.clear_logs()

        cancel_cmd = CancelWorkflowExecutionCommand(
            execution_id=execute_result.data.id
        )
        result = handler.handle_cancel_workflow_execution(cancel_cmd)

        assert result.status == ResultStatus.SUCCESS
        info_logs = [log for log in handler.logger.logs if log["level"] == "INFO"]
        assert any(
            "workflow.execution.cancelled" in log["message"] for log in info_logs
        )


class TestWorkflowCommandHandlerEdgeCases:
    """Tests for edge cases in workflow command handling."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()

        handler = WorkflowCommandHandler(workflow_repository, logger, cache)
        handler.workflow_service.execution_repository = execution_repository
        return handler

    def test_create_workflow_with_empty_steps_list(self, handler):
        """Should handle workflow with empty steps list."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            steps=[],
        )

        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data.steps == []

    def test_create_workflow_with_scheduled_trigger(self, handler):
        """Should create workflow with scheduled trigger."""
        command = CreateWorkflowCommand(
            name="Scheduled Workflow",
            trigger_type="scheduled",
            trigger_config={"cron": "0 0 * * *"},
        )

        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.data.trigger_type == "scheduled"

    def test_create_workflow_preserves_metadata(self, handler):
        """Should preserve workflow metadata."""
        command = CreateWorkflowCommand(
            name="Test Workflow",
            created_by="user-123",
        )

        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.SUCCESS
        assert result.metadata["workflow_id"] is not None

    def test_execute_disabled_workflow_fails(self, handler):
        """Should fail to execute disabled workflow."""
        # Create disabled workflow
        create_cmd = CreateWorkflowCommand(
            name="Disabled Workflow",
            enabled=False,
        )
        create_result = handler.handle_create_workflow(create_cmd)

        # Try to execute it
        execute_cmd = ExecuteWorkflowCommand(workflow_id=create_result.data.id)
        result = handler.handle_execute_workflow(execute_cmd)

        # Should fail because workflow is disabled
        assert result.status == ResultStatus.ERROR


class TestWorkflowCommandHandlerErrorHandling:
    """Tests for error handling in workflow command handler."""

    @pytest.fixture
    def handler(self):
        """Create handler."""
        workflow_repository = MockRepository()
        execution_repository = MockRepository()
        logger = MockLogger()
        cache = MockCache()

        handler = WorkflowCommandHandler(workflow_repository, logger, cache)
        handler.workflow_service.execution_repository = execution_repository
        return handler

    def test_error_logged_on_validation_failure(self, handler):
        """Should log validation errors."""
        command = CreateWorkflowCommand(name="")
        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.ERROR
        error_logs = [log for log in handler.logger.logs if log["level"] == "ERROR"]
        assert len(error_logs) > 0

    def test_error_logged_on_not_found(self, handler):
        """Should log errors when workflow not found."""
        command = UpdateWorkflowCommand(
            workflow_id="nonexistent-id",
            updates={"name": "Updated"},
        )
        result = handler.handle_update_workflow(command)

        assert result.status == ResultStatus.ERROR
        error_logs = [log for log in handler.logger.logs if log["level"] == "ERROR"]
        assert len(error_logs) > 0

    def test_no_data_on_error(self, handler):
        """Should not include data when error occurs."""
        command = CreateWorkflowCommand(name="")
        result = handler.handle_create_workflow(command)

        assert result.status == ResultStatus.ERROR
        assert result.data is None
        assert result.error is not None


__all__ = [
    "TestCreateWorkflowCommandValidation",
    "TestUpdateWorkflowCommandValidation",
    "TestExecuteWorkflowCommandValidation",
    "TestCancelWorkflowExecutionCommandValidation",
    "TestWorkflowCommandHandler",
    "TestWorkflowCommandHandlerEventPublishing",
    "TestWorkflowCommandHandlerEdgeCases",
    "TestWorkflowCommandHandlerErrorHandling",
]
