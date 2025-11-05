"""
Workflow commands for the application layer.

This module implements command handlers for workflow operations.
Commands orchestrate workflow execution and publish events.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...domain.models.workflow import (
    Action,
    ActionType,
    Trigger,
    TriggerType,
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
)
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.workflow_service import WorkflowService
from ..dto import CommandResult, ResultStatus, WorkflowDTO, WorkflowExecutionDTO


class WorkflowCommandError(Exception):
    """Base exception for workflow command errors."""

    pass


class WorkflowValidationError(WorkflowCommandError):
    """Exception raised for workflow validation failures."""

    pass


class WorkflowNotFoundError(WorkflowCommandError):
    """Exception raised when workflow is not found."""

    pass


@dataclass
class CreateWorkflowCommand:
    """
    Command to create a new workflow.

    Attributes:
        name: Workflow name
        description: Workflow description
        trigger_type: Type of trigger
        trigger_config: Trigger configuration
        steps: List of workflow steps
        enabled: Whether workflow is enabled
        created_by: ID of user creating the workflow
    """

    name: str
    description: str = ""
    trigger_type: str = "manual"
    trigger_config: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            WorkflowValidationError: If validation fails
        """
        if not self.name:
            raise WorkflowValidationError("name is required")
        if len(self.name) > 255:
            raise WorkflowValidationError("name must be 255 characters or less")

        try:
            TriggerType(self.trigger_type)
        except ValueError:
            raise WorkflowValidationError(
                f"Invalid trigger_type: {self.trigger_type}"
            )


@dataclass
class UpdateWorkflowCommand:
    """
    Command to update an existing workflow.

    Attributes:
        workflow_id: ID of workflow to update
        updates: Dictionary of field updates
    """

    workflow_id: str
    updates: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            WorkflowValidationError: If validation fails
        """
        if not self.workflow_id:
            raise WorkflowValidationError("workflow_id is required")
        if not self.updates:
            raise WorkflowValidationError("updates cannot be empty")
        if "id" in self.updates:
            raise WorkflowValidationError("cannot update workflow id")


@dataclass
class ExecuteWorkflowCommand:
    """
    Command to execute a workflow.

    Attributes:
        workflow_id: ID of workflow to execute
        context: Execution context data
        triggered_by: ID of user triggering the workflow
    """

    workflow_id: str
    context: dict[str, Any] = field(default_factory=dict)
    triggered_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            WorkflowValidationError: If validation fails
        """
        if not self.workflow_id:
            raise WorkflowValidationError("workflow_id is required")


@dataclass
class CancelWorkflowExecutionCommand:
    """
    Command to cancel a workflow execution.

    Attributes:
        execution_id: ID of execution to cancel
        cancelled_by: ID of user cancelling the execution
    """

    execution_id: str
    cancelled_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            WorkflowValidationError: If validation fails
        """
        if not self.execution_id:
            raise WorkflowValidationError("execution_id is required")


class WorkflowCommandHandler:
    """
    Handler for workflow commands.

    This class orchestrates workflow operations using the domain service
    and publishes events for workflow state changes.

    Attributes:
        workflow_service: Domain service for workflow operations
        logger: Logger for recording events
    """

    def __init__(
        self,
        repository: Repository[Workflow],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize workflow command handler.

        Args:
            repository: Repository for workflow persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.workflow_service = WorkflowService(repository, logger, cache)
        self.logger = logger

    def handle_create_workflow(
        self, command: CreateWorkflowCommand
    ) -> CommandResult[WorkflowDTO]:
        """
        Handle create workflow command.

        Args:
            command: Create workflow command

        Returns:
            Command result with workflow DTO
        """
        try:
            # Validate command
            command.validate()

            # Create trigger
            trigger = Trigger(
                trigger_type=TriggerType(command.trigger_type),
                config=command.trigger_config,
            )

            # Create workflow
            workflow = Workflow(
                name=command.name,
                description=command.description,
                trigger=trigger,
                enabled=command.enabled,
            )

            # Add steps
            for step_data in command.steps:
                step = self._create_workflow_step(step_data)
                workflow.add_step(step)

            # Validate workflow
            is_valid, errors = workflow.validate()
            if not is_valid:
                raise WorkflowValidationError(f"Workflow validation failed: {errors}")

            # Create workflow using service
            created_workflow = self.workflow_service.create_workflow(workflow)

            # Convert to DTO
            dto = self._workflow_to_dto(created_workflow)

            # Publish event
            self._publish_event("workflow.created", {"workflow_id": created_workflow.id})

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"workflow_id": created_workflow.id},
            )

        except WorkflowValidationError as e:
            self.logger.error(f"Workflow validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during workflow creation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to create workflow: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow creation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_update_workflow(
        self, command: UpdateWorkflowCommand
    ) -> CommandResult[WorkflowDTO]:
        """
        Handle update workflow command.

        Args:
            command: Update workflow command

        Returns:
            Command result with updated workflow DTO
        """
        try:
            # Validate command
            command.validate()

            # Update workflow using service
            updated_workflow = self.workflow_service.update_workflow(
                command.workflow_id, command.updates
            )

            if not updated_workflow:
                raise WorkflowNotFoundError(
                    f"Workflow {command.workflow_id} not found"
                )

            # Convert to DTO
            dto = self._workflow_to_dto(updated_workflow)

            # Publish event
            self._publish_event("workflow.updated", {"workflow_id": updated_workflow.id})

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"workflow_id": updated_workflow.id},
            )

        except WorkflowValidationError as e:
            self.logger.error(f"Workflow validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except WorkflowNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during workflow update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to update workflow: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_execute_workflow(
        self, command: ExecuteWorkflowCommand
    ) -> CommandResult[WorkflowExecutionDTO]:
        """
        Handle execute workflow command.

        Args:
            command: Execute workflow command

        Returns:
            Command result with execution DTO
        """
        try:
            # Validate command
            command.validate()

            # Execute workflow using service
            execution = self.workflow_service.execute_workflow(
                command.workflow_id, command.context
            )

            if not execution:
                raise WorkflowNotFoundError(
                    f"Workflow {command.workflow_id} not found or not enabled"
                )

            # Convert to DTO
            dto = self._execution_to_dto(execution)

            # Publish event
            self._publish_event(
                "workflow.execution.started",
                {
                    "workflow_id": command.workflow_id,
                    "execution_id": execution.id,
                    "triggered_by": command.triggered_by,
                },
            )

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={
                    "workflow_id": command.workflow_id,
                    "execution_id": execution.id,
                },
            )

        except WorkflowValidationError as e:
            self.logger.error(f"Workflow validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except WorkflowNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow execution: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_cancel_workflow_execution(
        self, command: CancelWorkflowExecutionCommand
    ) -> CommandResult[bool]:
        """
        Handle cancel workflow execution command.

        Args:
            command: Cancel workflow execution command

        Returns:
            Command result with success boolean
        """
        try:
            # Validate command
            command.validate()

            # Cancel execution using service
            success = self.workflow_service.cancel_execution(command.execution_id)

            if not success:
                raise WorkflowNotFoundError(
                    f"Workflow execution {command.execution_id} not found or already completed"
                )

            # Publish event
            self._publish_event(
                "workflow.execution.cancelled",
                {
                    "execution_id": command.execution_id,
                    "cancelled_by": command.cancelled_by,
                },
            )

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=True,
                metadata={"execution_id": command.execution_id},
            )

        except WorkflowValidationError as e:
            self.logger.error(f"Workflow validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except WorkflowNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during workflow cancellation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def _create_workflow_step(self, step_data: dict[str, Any]) -> WorkflowStep:
        """
        Create workflow step from data.

        Args:
            step_data: Step configuration

        Returns:
            WorkflowStep instance
        """
        action_data = step_data.get("action", {})
        action = Action(
            action_type=ActionType(action_data.get("action_type", "execute_script")),
            config=action_data.get("config", {}),
            retry_count=action_data.get("retry_count", 0),
            timeout_seconds=action_data.get("timeout_seconds", 300),
        )

        return WorkflowStep(
            name=step_data.get("name", ""),
            description=step_data.get("description", ""),
            action=action,
            next_step_id=step_data.get("next_step_id"),
            on_failure_step_id=step_data.get("on_failure_step_id"),
        )

    def _workflow_to_dto(self, workflow: Workflow) -> WorkflowDTO:
        """
        Convert workflow to DTO.

        Args:
            workflow: Workflow to convert

        Returns:
            WorkflowDTO instance
        """
        steps_data = []
        for step in workflow.steps:
            step_data = {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "action": {
                    "action_type": step.action.action_type.value if step.action else None,
                    "config": step.action.config if step.action else {},
                },
                "next_step_id": step.next_step_id,
            }
            steps_data.append(step_data)

        return WorkflowDTO(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            enabled=workflow.enabled,
            trigger_type=workflow.trigger.trigger_type.value if workflow.trigger else "manual",
            steps=steps_data,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            metadata=workflow.metadata,
        )

    def _execution_to_dto(self, execution: WorkflowExecution) -> WorkflowExecutionDTO:
        """
        Convert workflow execution to DTO.

        Args:
            execution: Execution to convert

        Returns:
            WorkflowExecutionDTO instance
        """
        return WorkflowExecutionDTO(
            id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status.value,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error_message=execution.error_message,
            execution_log=execution.execution_log,
        )

    def _publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Publish an event.

        Args:
            event_type: Type of event
            data: Event data
        """
        self.logger.info(f"Event published: {event_type}", extra=data)
        # In a real implementation, this would publish to an event bus


__all__ = [
    "CreateWorkflowCommand",
    "UpdateWorkflowCommand",
    "ExecuteWorkflowCommand",
    "CancelWorkflowExecutionCommand",
    "WorkflowCommandHandler",
    "WorkflowCommandError",
    "WorkflowValidationError",
    "WorkflowNotFoundError",
]
