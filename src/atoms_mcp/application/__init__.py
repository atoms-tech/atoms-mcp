"""
Application layer for atoms-mcp.

This layer orchestrates use cases and business logic by coordinating
domain models and services. It exposes commands and queries that are
consumed by the presentation layer (API, CLI, etc.).

Architecture:
- Commands: Write operations (create, update, delete)
- Queries: Read operations (get, list, search)
- Workflows: Complex multi-step operations
- DTOs: Data transfer objects for serialization

All operations use dependency injection for ports (repository, logger, cache)
and return strongly-typed result objects (CommandResult, QueryResult).
"""

from . import commands, dto, queries, workflows

# Re-export main components
from .commands import (
    CreateEntityCommand,
    CreateRelationshipCommand,
    CreateWorkflowCommand,
    DeleteEntityCommand,
    DeleteRelationshipCommand,
    EntityCommandHandler,
    RelationshipCommandHandler,
    WorkflowCommandHandler,
)
from .dto import CommandResult, EntityDTO, QueryResult, RelationshipDTO, ResultStatus
from .queries import (
    EntityQueryHandler,
    GetEntityQuery,
    ListEntitiesQuery,
    RelationshipQueryHandler,
)
from .workflows import (
    BulkOperationsHandler,
    ImportExportHandler,
)

__all__ = [
    # Modules
    "commands",
    "queries",
    "workflows",
    "dto",
    # DTOs
    "CommandResult",
    "QueryResult",
    "ResultStatus",
    "EntityDTO",
    "RelationshipDTO",
    # Command handlers
    "EntityCommandHandler",
    "RelationshipCommandHandler",
    "WorkflowCommandHandler",
    # Query handlers
    "EntityQueryHandler",
    "RelationshipQueryHandler",
    # Workflow handlers
    "BulkOperationsHandler",
    "ImportExportHandler",
    # Common commands
    "CreateEntityCommand",
    "DeleteEntityCommand",
    "CreateRelationshipCommand",
    "DeleteRelationshipCommand",
    "CreateWorkflowCommand",
    # Common queries
    "GetEntityQuery",
    "ListEntitiesQuery",
]
