"""
CLI command handlers.

This module provides handlers that bridge CLI commands to application layer
commands and queries. Handlers format responses and handle errors.
"""

from typing import Any, Optional

from ....application.commands import (
    CreateEntityCommand,
    CreateRelationshipCommand,
    CreateWorkflowCommand,
    DeleteEntityCommand,
    DeleteRelationshipCommand,
    EntityCommandHandler,
    ExecuteWorkflowCommand,
    RelationshipCommandHandler,
    UpdateEntityCommand,
    WorkflowCommandHandler,
)
from ....application.queries import (
    AnalyticsQueryHandler,
    CountEntitiesQuery,
    EntityQueryHandler,
    GetEntityQuery,
    GetRelationshipsQuery,
    ListEntitiesQuery,
    RelationshipQueryHandler,
    WorkspaceStatsQuery,
)
from ....domain.models.entity import Entity
from ....domain.models.relationship import Relationship
from ....infrastructure.cache.provider import InMemoryCacheProvider
from ....infrastructure.logging.logger import StdLibLogger
from ....adapters.secondary.supabase.repository import SupabaseRepository


class CLIHandlers:
    """
    CLI handlers for all operations.

    This class initializes all command and query handlers and provides
    methods that CLI commands can call.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        """
        Initialize CLI handlers.

        Args:
            supabase_url: Supabase URL
            supabase_key: Supabase key
        """
        # Setup logger
        self.logger = StdLibLogger("atoms-cli")

        # Setup cache
        self.cache = InMemoryCacheProvider()

        # Initialize repositories
        if supabase_url and supabase_key:
            self.entity_repository = SupabaseRepository[Entity](
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                table_name="entities",
                logger=self.logger,
            )
            self.relationship_repository = SupabaseRepository[Relationship](
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                table_name="relationships",
                logger=self.logger,
            )
        else:
            # Use Supabase as default, no in-memory fallback
            self.entity_repository = SupabaseRepository[Entity](
                supabase_url="http://localhost:54321",
                supabase_key="test-key",
                table_name="entities",
                logger=self.logger,
            )
            self.relationship_repository = SupabaseRepository[Relationship](
                supabase_url="http://localhost:54321",
                supabase_key="test-key",
                table_name="relationships",
                logger=self.logger,
            )

        # Initialize command handlers
        self.entity_command_handler = EntityCommandHandler(
            repository=self.entity_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.relationship_command_handler = RelationshipCommandHandler(
            repository=self.relationship_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.workflow_command_handler = WorkflowCommandHandler(
            entity_repository=self.entity_repository,
            relationship_repository=self.relationship_repository,
            logger=self.logger,
        )

        # Initialize query handlers
        self.entity_query_handler = EntityQueryHandler(
            repository=self.entity_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.relationship_query_handler = RelationshipQueryHandler(
            repository=self.relationship_repository,
            logger=self.logger,
            cache=self.cache,
        )
        self.analytics_query_handler = AnalyticsQueryHandler(
            entity_repository=self.entity_repository,
            relationship_repository=self.relationship_repository,
            logger=self.logger,
            cache=self.cache,
        )

    # Entity Operations
    def create_entity(
        self,
        entity_type: str,
        name: str,
        description: str = "",
        properties: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a new entity.

        Args:
            entity_type: Type of entity
            name: Entity name
            description: Entity description
            properties: Entity properties

        Returns:
            Created entity data

        Raises:
            Exception: If creation fails
        """
        command = CreateEntityCommand(
            entity_type=entity_type,
            name=name,
            description=description,
            properties=properties or {},
        )

        result = self.entity_command_handler.handle_create_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def get_entity(self, entity_id: str) -> dict[str, Any]:
        """Get entity by ID."""
        query = GetEntityQuery(entity_id=entity_id)
        result = self.entity_query_handler.handle_get_entity(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def list_entities(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List entities with filtering."""
        query = ListEntitiesQuery(
            filters=filters or {},
            limit=limit,
        )

        result = self.entity_query_handler.handle_list_entities(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def update_entity(
        self,
        entity_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an entity."""
        command = UpdateEntityCommand(
            entity_id=entity_id,
            updates=updates,
        )

        result = self.entity_command_handler.handle_update_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def delete_entity(
        self,
        entity_id: str,
        soft_delete: bool = True,
    ) -> dict[str, Any]:
        """Delete an entity."""
        command = DeleteEntityCommand(
            entity_id=entity_id,
            soft_delete=soft_delete,
        )

        result = self.entity_command_handler.handle_delete_entity(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def count_entities(
        self,
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Count entities."""
        query = CountEntitiesQuery(filters=filters or {})
        result = self.entity_query_handler.handle_count_entities(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    # Relationship Operations
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[dict[str, Any]] = None,
        bidirectional: bool = False,
    ) -> dict[str, Any]:
        """Create a relationship."""
        command = CreateRelationshipCommand(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            bidirectional=bidirectional,
        )

        result = self.relationship_command_handler.handle_create_relationship(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def list_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """List relationships."""
        query = GetRelationshipsQuery(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )

        result = self.relationship_query_handler.handle_get_relationships(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def delete_relationship(
        self,
        relationship_id: str,
    ) -> dict[str, Any]:
        """Delete a relationship."""
        command = DeleteRelationshipCommand(relationship_id=relationship_id)
        result = self.relationship_command_handler.handle_delete_relationship(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    # Workflow Operations
    def create_workflow(
        self,
        name: str,
        description: str = "",
        trigger_type: str = "manual",
        steps: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Create a workflow."""
        command = CreateWorkflowCommand(
            name=name,
            description=description,
            trigger_type=trigger_type,
            steps=steps or [],
        )

        result = self.workflow_command_handler.handle_create_workflow(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def execute_workflow(
        self,
        workflow_id: str,
        parameters: Optional[dict[str, Any]] = None,
        async_execution: bool = False,
    ) -> dict[str, Any]:
        """Execute a workflow."""
        command = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            parameters=parameters or {},
            async_execution=async_execution,
        )

        result = self.workflow_command_handler.handle_execute_workflow(command)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()

    def list_workflows(
        self,
        enabled_only: bool = False,
    ) -> dict[str, Any]:
        """List workflows."""
        # TODO: Implement workflow query handler
        # For now, return empty list
        return {
            "status": "success",
            "data": [],
            "total_count": 0,
            "page": 1,
            "page_size": 20,
        }

    # Analytics Operations
    def get_workspace_stats(
        self,
        workspace_id: str,
    ) -> dict[str, Any]:
        """Get workspace statistics."""
        query = WorkspaceStatsQuery(workspace_id=workspace_id)
        result = self.analytics_query_handler.handle_workspace_stats(query)

        if result.is_error:
            raise Exception(result.error)

        return result.to_dict()


__all__ = ["CLIHandlers"]
