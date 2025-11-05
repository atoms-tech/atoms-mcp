"""
Application layer commands.

Commands represent write operations (creates, updates, deletes) that change
system state. Each command has validation and returns a CommandResult DTO.
"""

from .entity_commands import (
    ArchiveEntityCommand,
    CreateEntityCommand,
    DeleteEntityCommand,
    EntityCommandHandler,
    RestoreEntityCommand,
    UpdateEntityCommand,
)
from .relationship_commands import (
    CreateRelationshipCommand,
    DeleteRelationshipCommand,
    RelationshipCommandHandler,
    UpdateRelationshipCommand,
)
from .workflow_commands import (
    CancelWorkflowExecutionCommand,
    CreateWorkflowCommand,
    ExecuteWorkflowCommand,
    UpdateWorkflowCommand,
    WorkflowCommandHandler,
)

__all__ = [
    # Entity commands
    "CreateEntityCommand",
    "UpdateEntityCommand",
    "DeleteEntityCommand",
    "ArchiveEntityCommand",
    "RestoreEntityCommand",
    "EntityCommandHandler",
    # Relationship commands
    "CreateRelationshipCommand",
    "DeleteRelationshipCommand",
    "UpdateRelationshipCommand",
    "RelationshipCommandHandler",
    # Workflow commands
    "CreateWorkflowCommand",
    "UpdateWorkflowCommand",
    "ExecuteWorkflowCommand",
    "CancelWorkflowExecutionCommand",
    "WorkflowCommandHandler",
]
