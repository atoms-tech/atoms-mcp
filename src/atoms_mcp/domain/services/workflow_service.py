"""
Workflow service - business logic for workflow execution.

This module implements the core business logic for executing and
managing workflows without external dependencies.
"""

from typing import Any, Callable, Optional

from ..models.workflow import (
    Action,
    ActionType,
    Trigger,
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
)
from ..ports.logger import Logger
from ..ports.repository import Repository


class WorkflowService:
    """
    Service for managing workflow execution logic.

    This service implements workflow execution, validation, and scheduling
    using pure business logic without external dependencies.

    Attributes:
        workflow_repository: Repository for workflow definitions
        execution_repository: Repository for workflow executions
        logger: Logger for recording events
    """

    def __init__(
        self,
        workflow_repository: Repository[Workflow],
        execution_repository: Repository[WorkflowExecution],
        logger: Logger,
    ):
        """
        Initialize workflow service.

        Args:
            workflow_repository: Repository for workflow definitions
            execution_repository: Repository for workflow executions
            logger: Logger for recording events
        """
        self.workflow_repository = workflow_repository
        self.execution_repository = execution_repository
        self.logger = logger
        self._action_handlers: dict[ActionType, Callable] = {}

    def register_action_handler(
        self,
        action_type: ActionType,
        handler: Callable[[Action, dict[str, Any]], Any],
    ) -> None:
        """
        Register a handler for a specific action type.

        Args:
            action_type: Type of action to handle
            handler: Callable that executes the action
        """
        self._action_handlers[action_type] = handler
        self.logger.debug(f"Registered handler for {action_type.value}")

    def create_workflow(self, workflow: Workflow) -> Workflow:
        """
        Create a new workflow definition.

        Args:
            workflow: Workflow to create

        Returns:
            Created workflow

        Raises:
            ValueError: If workflow is invalid
        """
        self.logger.info(f"Creating workflow {workflow.name}")

        # Validate workflow
        is_valid, errors = workflow.validate()
        if not is_valid:
            error_msg = "; ".join(errors)
            self.logger.error(f"Workflow validation failed: {error_msg}")
            raise ValueError(f"Workflow validation failed: {error_msg}")

        # Save workflow
        created = self.workflow_repository.save(workflow)

        self.logger.info(f"Workflow {created.id} created successfully")
        return created

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Retrieve a workflow definition.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        workflow = self.workflow_repository.get(workflow_id)

        if workflow:
            self.logger.debug(f"Retrieved workflow {workflow_id}")
        else:
            self.logger.warning(f"Workflow {workflow_id} not found")

        return workflow

    def execute_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any],
    ) -> WorkflowExecution:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute
            context: Initial execution context

        Returns:
            WorkflowExecution tracking the execution

        Raises:
            ValueError: If workflow not found or invalid
        """
        self.logger.info(f"Starting execution of workflow {workflow_id}")

        # Get workflow definition
        workflow = self.workflow_repository.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.enabled:
            raise ValueError(f"Workflow {workflow_id} is disabled")

        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            context=context.copy(),
        )
        execution.start()
        execution = self.execution_repository.save(execution)

        try:
            # Check trigger conditions
            if workflow.trigger and not workflow.trigger.should_fire(context):
                self.logger.info("Trigger conditions not met, skipping execution")
                execution.complete()
                self.execution_repository.save(execution)
                return execution

            # Execute steps
            current_step_index = 0
            while current_step_index < len(workflow.steps):
                step = workflow.steps[current_step_index]
                execution.current_step_id = step.id
                self.execution_repository.save(execution)

                # Execute step
                success = self._execute_step(step, execution)

                if not success:
                    if step.on_failure_step_id:
                        # Jump to failure handler step
                        failure_step = workflow.get_step(step.on_failure_step_id)
                        if failure_step:
                            current_step_index = workflow.steps.index(failure_step)
                            continue

                    # No failure handler, fail execution
                    execution.fail("Step execution failed")
                    self.execution_repository.save(execution)
                    return execution

                # Move to next step
                if step.next_step_id:
                    next_step = workflow.get_step(step.next_step_id)
                    if next_step:
                        current_step_index = workflow.steps.index(next_step)
                    else:
                        break
                else:
                    break

            # Execution completed successfully
            execution.complete()
            self.execution_repository.save(execution)

            self.logger.info(f"Workflow execution {execution.id} completed successfully")

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exception=e)
            execution.fail(str(e))
            self.execution_repository.save(execution)

        return execution

    def validate_workflow(self, workflow: Workflow) -> tuple[bool, list[str]]:
        """
        Validate a workflow definition.

        Args:
            workflow: Workflow to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        self.logger.debug(f"Validating workflow {workflow.name}")
        return workflow.validate()

    def schedule_workflow(
        self,
        workflow_id: str,
        schedule: str,
    ) -> bool:
        """
        Schedule a workflow for periodic execution.

        Args:
            workflow_id: ID of workflow to schedule
            schedule: Schedule expression (e.g., cron format)

        Returns:
            True if scheduled successfully

        Note:
            This is a placeholder for scheduling logic.
            Actual scheduling would be implemented in infrastructure layer.
        """
        self.logger.info(f"Scheduling workflow {workflow_id} with schedule {schedule}")

        workflow = self.workflow_repository.get(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False

        # Store schedule in workflow metadata
        workflow.set_metadata("schedule", schedule)
        self.workflow_repository.save(workflow)

        self.logger.info(f"Workflow {workflow_id} scheduled successfully")
        return True

    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running workflow execution.

        Args:
            execution_id: ID of execution to cancel

        Returns:
            True if cancelled successfully
        """
        self.logger.info(f"Cancelling execution {execution_id}")

        execution = self.execution_repository.get(execution_id)
        if not execution:
            self.logger.warning(f"Execution {execution_id} not found")
            return False

        if execution.status not in (
            WorkflowStatus.PENDING,
            WorkflowStatus.RUNNING,
            WorkflowStatus.PAUSED,
        ):
            self.logger.warning(
                f"Execution {execution_id} cannot be cancelled (status: {execution.status.value})"
            )
            return False

        execution.cancel()
        self.execution_repository.save(execution)

        self.logger.info(f"Execution {execution_id} cancelled successfully")
        return True

    def pause_execution(self, execution_id: str) -> bool:
        """
        Pause a running workflow execution.

        Args:
            execution_id: ID of execution to pause

        Returns:
            True if paused successfully
        """
        self.logger.info(f"Pausing execution {execution_id}")

        execution = self.execution_repository.get(execution_id)
        if not execution:
            self.logger.warning(f"Execution {execution_id} not found")
            return False

        if execution.status != WorkflowStatus.RUNNING:
            self.logger.warning(
                f"Execution {execution_id} is not running (status: {execution.status.value})"
            )
            return False

        execution.pause()
        self.execution_repository.save(execution)

        self.logger.info(f"Execution {execution_id} paused successfully")
        return True

    def _execute_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> bool:
        """
        Execute a single workflow step.

        Args:
            step: Step to execute
            execution: Current execution context

        Returns:
            True if step executed successfully
        """
        self.logger.debug(f"Executing step {step.name}")

        # Check step conditions
        if not step.should_execute(execution.context):
            execution.log_event(f"Step {step.name} skipped (conditions not met)")
            return True

        if not step.action:
            execution.log_event(f"Step {step.name} has no action", level="warning")
            return True

        # Get action handler
        handler = self._action_handlers.get(step.action.action_type)
        if not handler:
            execution.log_event(
                f"No handler registered for action type {step.action.action_type.value}",
                level="error",
            )
            return False

        # Execute action with retries
        retry_count = 0
        max_retries = step.action.retry_count

        while retry_count <= max_retries:
            try:
                result = handler(step.action, execution.context)
                execution.log_event(f"Step {step.name} completed successfully")

                # Update context with result if provided
                if isinstance(result, dict):
                    execution.context.update(result)

                return True

            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    execution.log_event(
                        f"Step {step.name} failed after {max_retries} retries: {e}",
                        level="error",
                    )
                    return False

                execution.log_event(
                    f"Step {step.name} failed (retry {retry_count}/{max_retries}): {e}",
                    level="warning",
                )

        return False
