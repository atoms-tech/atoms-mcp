"""
Domain layer package.

This package contains the core business logic of the Atoms MCP system.
All code in this package is pure Python with zero external dependencies
(except standard library modules).

The domain layer follows Clean Architecture principles:
- Models: Pure domain entities and value objects
- Services: Business logic and use cases
- Ports: Abstract interfaces for external dependencies

Example usage:
    from atoms_mcp.domain import (
        Entity,
        EntityService,
        Repository,
        Logger,
    )

    # Create service with injected dependencies
    service = EntityService(
        repository=my_repository,
        logger=my_logger,
    )

    # Create and persist an entity
    entity = Entity()
    created = service.create_entity(entity)
"""

# Models
from .models import (
    Action,
    ActionType,
    Condition,
    ConditionOperator,
    DocumentEntity,
    Entity,
    EntityStatus,
    EntityType,
    ProjectEntity,
    Relationship,
    RelationshipConstraint,
    RelationshipGraph,
    RelationshipStatus,
    RelationType,
    TaskEntity,
    Trigger,
    TriggerType,
    Workflow,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
    WorkspaceEntity,
)

# Ports
from .ports import Cache, Logger, Repository, RepositoryError

# Services
from .services import EntityService, RelationshipService, WorkflowService

__all__ = [
    # Models - Entity
    "Entity",
    "EntityStatus",
    "EntityType",
    "WorkspaceEntity",
    "ProjectEntity",
    "TaskEntity",
    "DocumentEntity",
    # Models - Relationship
    "Relationship",
    "RelationType",
    "RelationshipStatus",
    "RelationshipConstraint",
    "RelationshipGraph",
    # Models - Workflow
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "WorkflowStatus",
    "Trigger",
    "TriggerType",
    "Action",
    "ActionType",
    "Condition",
    "ConditionOperator",
    # Ports
    "Repository",
    "RepositoryError",
    "Logger",
    "Cache",
    # Services
    "EntityService",
    "RelationshipService",
    "WorkflowService",
]
