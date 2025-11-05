"""
Domain models for workflow automation.

This module defines workflow models for automating business processes.
Pure Python implementation with state machine logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4


class TriggerType(Enum):
    """Type enumeration for workflow triggers."""

    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    STATUS_CHANGED = "status_changed"
    FIELD_CHANGED = "field_changed"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    WEBHOOK = "webhook"


class ActionType(Enum):
    """Type enumeration for workflow actions."""

    CREATE_ENTITY = "create_entity"
    UPDATE_ENTITY = "update_entity"
    DELETE_ENTITY = "delete_entity"
    SEND_NOTIFICATION = "send_notification"
    ASSIGN_TASK = "assign_task"
    EXECUTE_SCRIPT = "execute_script"
    CALL_WEBHOOK = "call_webhook"
    WAIT = "wait"


class ConditionOperator(Enum):
    """Operator enumeration for conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    MATCHES = "matches"


class WorkflowStatus(Enum):
    """Status enumeration for workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Condition:
    """
    Conditional expression for workflow control flow.

    Conditions determine whether workflow steps should execute.

    Attributes:
        field: Field name to evaluate
        operator: Comparison operator
        value: Value to compare against
        negate: Whether to negate the condition result
    """

    field: str = ""
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Any = None
    negate: bool = False

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate the condition against a context.

        Args:
            context: Dictionary containing field values

        Returns:
            Boolean result of condition evaluation
        """
        field_value = self._get_nested_value(context, self.field)
        result = self._apply_operator(field_value, self.value)
        return not result if self.negate else result

    def _get_nested_value(self, obj: dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split(".")
        value = obj
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def _apply_operator(self, left: Any, right: Any) -> bool:
        """Apply the comparison operator."""
        if self.operator == ConditionOperator.EQUALS:
            return left == right
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return left != right
        elif self.operator == ConditionOperator.GREATER_THAN:
            return left > right if left is not None and right is not None else False
        elif self.operator == ConditionOperator.LESS_THAN:
            return left < right if left is not None and right is not None else False
        elif self.operator == ConditionOperator.GREATER_OR_EQUAL:
            return left >= right if left is not None and right is not None else False
        elif self.operator == ConditionOperator.LESS_OR_EQUAL:
            return left <= right if left is not None and right is not None else False
        elif self.operator == ConditionOperator.CONTAINS:
            return right in left if left is not None else False
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            return right not in left if left is not None else True
        elif self.operator == ConditionOperator.IN:
            return left in right if right is not None else False
        elif self.operator == ConditionOperator.NOT_IN:
            return left not in right if right is not None else True
        elif self.operator == ConditionOperator.IS_NULL:
            return left is None
        elif self.operator == ConditionOperator.IS_NOT_NULL:
            return left is not None
        return False


@dataclass
class Trigger:
    """
    Workflow trigger definition.

    Triggers define when a workflow should execute.

    Attributes:
        id: Unique identifier
        trigger_type: Type of trigger
        config: Trigger-specific configuration
        conditions: Conditions that must be met
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    trigger_type: TriggerType = TriggerType.MANUAL
    config: dict[str, Any] = field(default_factory=dict)
    conditions: list[Condition] = field(default_factory=list)

    def should_fire(self, context: dict[str, Any]) -> bool:
        """
        Check if trigger should fire given a context.

        Args:
            context: Trigger context data

        Returns:
            True if trigger should fire
        """
        if not self.conditions:
            return True
        return all(condition.evaluate(context) for condition in self.conditions)


@dataclass
class Action:
    """
    Workflow action definition.

    Actions are the operations performed by workflow steps.

    Attributes:
        id: Unique identifier
        action_type: Type of action
        config: Action-specific configuration
        retry_count: Number of times to retry on failure
        timeout_seconds: Timeout for action execution
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    action_type: ActionType = ActionType.EXECUTE_SCRIPT
    config: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    timeout_seconds: int = 300

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate action configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.action_type == ActionType.CREATE_ENTITY:
            if "entity_type" not in self.config:
                return False, "entity_type required for CREATE_ENTITY"
        elif self.action_type == ActionType.UPDATE_ENTITY:
            if "entity_id" not in self.config:
                return False, "entity_id required for UPDATE_ENTITY"
        return True, None


@dataclass
class WorkflowStep:
    """
    Individual step in a workflow.

    Steps define the sequence of actions in a workflow.

    Attributes:
        id: Unique identifier
        name: Step name
        description: Step description
        action: Action to execute
        conditions: Conditions for step execution
        next_step_id: ID of next step (None if last step)
        on_failure_step_id: ID of step to execute on failure
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    action: Optional[Action] = None
    conditions: list[Condition] = field(default_factory=list)
    next_step_id: Optional[str] = None
    on_failure_step_id: Optional[str] = None

    def should_execute(self, context: dict[str, Any]) -> bool:
        """
        Check if step should execute given a context.

        Args:
            context: Execution context data

        Returns:
            True if step should execute
        """
        if not self.conditions:
            return True
        return all(condition.evaluate(context) for condition in self.conditions)


@dataclass
class Workflow:
    """
    Workflow definition for automation.

    Workflows define automated processes with triggers, steps, and actions.

    Attributes:
        id: Unique identifier
        name: Workflow name
        description: Workflow description
        trigger: Workflow trigger
        steps: List of workflow steps
        enabled: Whether workflow is enabled
        created_at: Creation timestamp
        updated_at: Update timestamp
        metadata: Additional metadata
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    trigger: Optional[Trigger] = None
    steps: list[WorkflowStep] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate workflow after initialization."""
        if not self.name:
            raise ValueError("Workflow name cannot be empty")

    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the workflow.

        Args:
            step: Step to add
        """
        self.steps.append(step)
        self.updated_at = datetime.utcnow()

    def remove_step(self, step_id: str) -> bool:
        """
        Remove a step from the workflow.

        Args:
            step_id: ID of step to remove

        Returns:
            True if step was removed
        """
        original_length = len(self.steps)
        self.steps = [step for step in self.steps if step.id != step_id]
        if len(self.steps) < original_length:
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """
        Get a step by ID.

        Args:
            step_id: ID of step to retrieve

        Returns:
            WorkflowStep if found, None otherwise
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the workflow definition.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not self.trigger:
            errors.append("Workflow must have a trigger")

        if not self.steps:
            errors.append("Workflow must have at least one step")

        # Validate step references
        step_ids = {step.id for step in self.steps}
        for step in self.steps:
            if step.next_step_id and step.next_step_id not in step_ids:
                errors.append(f"Step {step.id} references invalid next_step_id")
            if (
                step.on_failure_step_id
                and step.on_failure_step_id not in step_ids
            ):
                errors.append(f"Step {step.id} references invalid on_failure_step_id")

            # Validate action config
            if step.action:
                is_valid, error = step.action.validate_config()
                if not is_valid:
                    errors.append(f"Step {step.id}: {error}")

        return len(errors) == 0, errors


@dataclass
class WorkflowExecution:
    """
    Runtime state for workflow execution.

    Tracks the execution of a workflow instance.

    Attributes:
        id: Unique identifier
        workflow_id: ID of the workflow being executed
        status: Current execution status
        current_step_id: ID of currently executing step
        context: Execution context data
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
        error_message: Error message if failed
        execution_log: Log of execution events
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_log: list[dict[str, Any]] = field(default_factory=list)

    def start(self) -> None:
        """Mark execution as started."""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.log_event("Workflow execution started")

    def complete(self) -> None:
        """Mark execution as completed."""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.log_event("Workflow execution completed")

    def fail(self, error_message: str) -> None:
        """
        Mark execution as failed.

        Args:
            error_message: Error description
        """
        self.status = WorkflowStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.log_event(f"Workflow execution failed: {error_message}")

    def pause(self) -> None:
        """Pause execution."""
        self.status = WorkflowStatus.PAUSED
        self.log_event("Workflow execution paused")

    def cancel(self) -> None:
        """Cancel execution."""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.log_event("Workflow execution cancelled")

    def log_event(self, message: str, level: str = "info") -> None:
        """
        Log an execution event.

        Args:
            message: Event message
            level: Log level (info, warning, error)
        """
        self.execution_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
                "step_id": self.current_step_id,
            }
        )

    def get_duration(self) -> Optional[float]:
        """
        Get execution duration in seconds.

        Returns:
            Duration in seconds, or None if not completed
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
