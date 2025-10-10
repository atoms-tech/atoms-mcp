"""Workflow-Kit: Saga patterns, declarative workflows, and orchestration utilities."""

# Pattern-based workflows and saga support
from workflow_kit.patterns.saga import Saga, SagaStep, SagaExecutor
from workflow_kit.patterns.workflow import Workflow, WorkflowStep, WorkflowEngine
from workflow_kit.patterns.state_machine import StateMachine, State, Transition

# Declarative workflow core
from workflow_kit.core.workflow import (
    Workflow as DeclarativeWorkflow,
    Workflow as CoreWorkflow,  # Alias for the new decorator-based workflow
    WorkflowContext,
    WorkflowStatus,
    WorkflowStep as CoreWorkflowStep,
    workflow as workflow_definition,
    step as workflow_step,
)
from workflow_kit.core.engine import WorkflowEngine as DeclarativeWorkflowEngine
from workflow_kit.core.engine import WorkflowEngine as CoreWorkflowEngine  # Alias

# Advanced orchestrators
from workflow_kit.orchestrators.temporal import (
    TemporalWorkflowClient,
    WorkflowExecutionResult,
    HumanApprovalRequest,
    ApprovalDecision,
)

__version__ = "0.1.0"

__all__ = [
    # Pattern-based workflows
    "Saga",
    "SagaStep",
    "SagaExecutor",
    "Workflow",
    "WorkflowStep",
    "WorkflowEngine",
    "StateMachine",
    "State",
    "Transition",
    # Declarative workflows (Core system)
    "DeclarativeWorkflow",
    "CoreWorkflow",  # Alias for new decorator-based system
    "CoreWorkflowStep",
    "CoreWorkflowEngine",
    "WorkflowContext",
    "WorkflowStatus",
    "workflow_definition",
    "workflow_step",
    "DeclarativeWorkflowEngine",
    "workflow",
    "step",
    # Orchestrators
    "TemporalWorkflowClient",
    "WorkflowExecutionResult",
    "HumanApprovalRequest",
    "ApprovalDecision",
]

# Backwards-compatible aliases
workflow = workflow_definition
step = workflow_step
