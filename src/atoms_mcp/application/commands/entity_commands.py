"""
Entity commands for the application layer.

This module implements command handlers for entity operations.
Commands use the domain services and return CommandResult DTOs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ...domain.models.entity import (
    DocumentEntity,
    Entity,
    EntityStatus,
    ProjectEntity,
    TaskEntity,
    WorkspaceEntity,
)
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.entity_service import EntityService
from ..dto import CommandResult, EntityDTO, ResultStatus


class EntityCommandError(Exception):
    """Base exception for entity command errors."""

    pass


class EntityValidationError(EntityCommandError):
    """Exception raised for entity validation failures."""

    pass


class EntityNotFoundError(EntityCommandError):
    """Exception raised when entity is not found."""

    pass


@dataclass
class CreateEntityCommand:
    """
    Command to create a new entity.

    Attributes:
        entity_type: Type of entity to create
        name: Entity name
        description: Optional description
        properties: Entity-specific properties
        metadata: Additional metadata
        created_by: ID of user creating the entity
    """

    entity_type: str
    name: str
    description: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            EntityValidationError: If validation fails
        """
        if not self.entity_type:
            raise EntityValidationError("entity_type is required")
        if not self.name:
            raise EntityValidationError("name is required")
        if len(self.name) > 255:
            raise EntityValidationError("name must be 255 characters or less")


@dataclass
class UpdateEntityCommand:
    """
    Command to update an existing entity.

    Attributes:
        entity_id: ID of entity to update
        updates: Dictionary of field updates
        validate_updates: Whether to validate updates
    """

    entity_id: str
    updates: dict[str, Any] = field(default_factory=dict)
    validate_updates: bool = True

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            EntityValidationError: If validation fails
        """
        if not self.entity_id:
            raise EntityValidationError("entity_id is required")
        if not self.updates:
            raise EntityValidationError("updates cannot be empty")
        if "id" in self.updates:
            raise EntityValidationError("cannot update entity id")


@dataclass
class DeleteEntityCommand:
    """
    Command to delete an entity.

    Attributes:
        entity_id: ID of entity to delete
        soft_delete: Whether to soft delete (default) or hard delete
        deleted_by: ID of user deleting the entity
    """

    entity_id: str
    soft_delete: bool = True
    deleted_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            EntityValidationError: If validation fails
        """
        if not self.entity_id:
            raise EntityValidationError("entity_id is required")


@dataclass
class ArchiveEntityCommand:
    """
    Command to archive an entity.

    Attributes:
        entity_id: ID of entity to archive
        archived_by: ID of user archiving the entity
    """

    entity_id: str
    archived_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            EntityValidationError: If validation fails
        """
        if not self.entity_id:
            raise EntityValidationError("entity_id is required")


@dataclass
class RestoreEntityCommand:
    """
    Command to restore a deleted or archived entity.

    Attributes:
        entity_id: ID of entity to restore
        restored_by: ID of user restoring the entity
    """

    entity_id: str
    restored_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            EntityValidationError: If validation fails
        """
        if not self.entity_id:
            raise EntityValidationError("entity_id is required")


class EntityCommandHandler:
    """
    Handler for entity commands.

    This class orchestrates entity operations using the domain service
    and returns DTOs suitable for serialization.

    Attributes:
        entity_service: Domain service for entity operations
        logger: Logger for recording events
    """

    def __init__(
        self,
        repository: Repository[Entity],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize entity command handler.

        Args:
            repository: Repository for entity persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.entity_service = EntityService(repository, logger, cache)
        self.logger = logger

    def handle_create_entity(
        self, command: CreateEntityCommand
    ) -> CommandResult[EntityDTO]:
        """
        Handle create entity command.

        Args:
            command: Create entity command

        Returns:
            Command result with entity DTO
        """
        try:
            # Validate command
            command.validate()

            # Create appropriate entity type
            entity = self._create_entity_instance(command)

            # Add metadata
            if command.created_by:
                entity.set_metadata("created_by", command.created_by)

            # Create entity using service
            created_entity = self.entity_service.create_entity(entity, validate=True)

            # Convert to DTO
            dto = self._entity_to_dto(created_entity)

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"entity_id": created_entity.id},
            )

        except EntityValidationError as e:
            self.logger.error(f"Entity validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity creation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to create entity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity creation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_update_entity(
        self, command: UpdateEntityCommand
    ) -> CommandResult[EntityDTO]:
        """
        Handle update entity command.

        Args:
            command: Update entity command

        Returns:
            Command result with updated entity DTO
        """
        try:
            # Validate command
            command.validate()

            # Update entity using service
            updated_entity = self.entity_service.update_entity(
                command.entity_id,
                command.updates,
                validate=command.validate_updates,
            )

            if not updated_entity:
                raise EntityNotFoundError(f"Entity {command.entity_id} not found")

            # Convert to DTO
            dto = self._entity_to_dto(updated_entity)

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"entity_id": updated_entity.id},
            )

        except EntityValidationError as e:
            self.logger.error(f"Entity validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except EntityNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to update entity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_delete_entity(
        self, command: DeleteEntityCommand
    ) -> CommandResult[bool]:
        """
        Handle delete entity command.

        Args:
            command: Delete entity command

        Returns:
            Command result with success boolean
        """
        try:
            # Validate command
            command.validate()

            # Delete entity using service
            success = self.entity_service.delete_entity(
                command.entity_id,
                soft_delete=command.soft_delete,
            )

            if not success:
                raise EntityNotFoundError(f"Entity {command.entity_id} not found")

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=True,
                metadata={
                    "entity_id": command.entity_id,
                    "soft_delete": command.soft_delete,
                },
            )

        except EntityValidationError as e:
            self.logger.error(f"Entity validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except EntityNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity deletion: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to delete entity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity deletion: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_archive_entity(
        self, command: ArchiveEntityCommand
    ) -> CommandResult[EntityDTO]:
        """
        Handle archive entity command.

        Args:
            command: Archive entity command

        Returns:
            Command result with archived entity DTO
        """
        try:
            # Validate command
            command.validate()

            # Archive entity using service
            archived_entity = self.entity_service.archive_entity(command.entity_id)

            if not archived_entity:
                raise EntityNotFoundError(f"Entity {command.entity_id} not found")

            # Add metadata
            if command.archived_by:
                archived_entity.set_metadata("archived_by", command.archived_by)
                archived_entity.set_metadata(
                    "archived_at", datetime.utcnow().isoformat()
                )

            # Convert to DTO
            dto = self._entity_to_dto(archived_entity)

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"entity_id": archived_entity.id},
            )

        except EntityValidationError as e:
            self.logger.error(f"Entity validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except EntityNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity archival: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to archive entity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity archival: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_restore_entity(
        self, command: RestoreEntityCommand
    ) -> CommandResult[EntityDTO]:
        """
        Handle restore entity command.

        Args:
            command: Restore entity command

        Returns:
            Command result with restored entity DTO
        """
        try:
            # Validate command
            command.validate()

            # Restore entity using service
            restored_entity = self.entity_service.restore_entity(command.entity_id)

            if not restored_entity:
                raise EntityNotFoundError(f"Entity {command.entity_id} not found")

            # Add metadata
            if command.restored_by:
                restored_entity.set_metadata("restored_by", command.restored_by)
                restored_entity.set_metadata(
                    "restored_at", datetime.utcnow().isoformat()
                )

            # Convert to DTO
            dto = self._entity_to_dto(restored_entity)

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"entity_id": restored_entity.id},
            )

        except EntityValidationError as e:
            self.logger.error(f"Entity validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except EntityNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during entity restoration: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to restore entity: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during entity restoration: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def _create_entity_instance(self, command: CreateEntityCommand) -> Entity:
        """
        Create appropriate entity instance based on type.

        Args:
            command: Create entity command

        Returns:
            Entity instance

        Raises:
            EntityValidationError: If entity type is unknown
        """
        entity_type_lower = command.entity_type.lower()

        if entity_type_lower == "workspace":
            return WorkspaceEntity(
                name=command.name,
                description=command.description,
                owner_id=command.properties.get("owner_id"),
                settings=command.properties.get("settings", {}),
            )
        elif entity_type_lower == "project":
            return ProjectEntity(
                name=command.name,
                description=command.description,
                workspace_id=command.properties.get("workspace_id"),
                start_date=command.properties.get("start_date"),
                end_date=command.properties.get("end_date"),
                priority=command.properties.get("priority", 3),
                tags=command.properties.get("tags", []),
            )
        elif entity_type_lower == "task":
            return TaskEntity(
                title=command.name,
                description=command.description,
                project_id=command.properties.get("project_id"),
                assignee_id=command.properties.get("assignee_id"),
                due_date=command.properties.get("due_date"),
                priority=command.properties.get("priority", 3),
                estimated_hours=command.properties.get("estimated_hours", 0.0),
                tags=command.properties.get("tags", []),
            )
        elif entity_type_lower == "document":
            return DocumentEntity(
                title=command.name,
                content=command.properties.get("content", ""),
                project_id=command.properties.get("project_id"),
                author_id=command.properties.get("author_id"),
                document_type=command.properties.get("document_type", "general"),
                tags=command.properties.get("tags", []),
            )
        else:
            # Create generic entity
            entity = Entity()
            entity.set_metadata("name", command.name)
            entity.set_metadata("description", command.description)
            entity.set_metadata("entity_type", command.entity_type)
            for key, value in command.properties.items():
                entity.set_metadata(key, value)
            return entity

    def _entity_to_dto(self, entity: Entity) -> EntityDTO:
        """
        Convert entity to DTO.

        Args:
            entity: Entity to convert

        Returns:
            EntityDTO instance
        """
        # Determine entity type and extract properties
        if isinstance(entity, WorkspaceEntity):
            entity_type = "workspace"
            properties = {
                "name": entity.name,
                "description": entity.description,
                "owner_id": entity.owner_id,
                "settings": entity.settings,
            }
        elif isinstance(entity, ProjectEntity):
            entity_type = "project"
            properties = {
                "name": entity.name,
                "description": entity.description,
                "workspace_id": entity.workspace_id,
                "start_date": entity.start_date.isoformat() if entity.start_date else None,
                "end_date": entity.end_date.isoformat() if entity.end_date else None,
                "priority": entity.priority,
                "tags": entity.tags,
            }
        elif isinstance(entity, TaskEntity):
            entity_type = "task"
            properties = {
                "title": entity.title,
                "description": entity.description,
                "project_id": entity.project_id,
                "assignee_id": entity.assignee_id,
                "due_date": entity.due_date.isoformat() if entity.due_date else None,
                "priority": entity.priority,
                "estimated_hours": entity.estimated_hours,
                "actual_hours": entity.actual_hours,
                "tags": entity.tags,
                "dependencies": entity.dependencies,
            }
        elif isinstance(entity, DocumentEntity):
            entity_type = "document"
            properties = {
                "title": entity.title,
                "content": entity.content,
                "project_id": entity.project_id,
                "author_id": entity.author_id,
                "version": entity.version,
                "document_type": entity.document_type,
                "tags": entity.tags,
            }
        else:
            entity_type = entity.metadata.get("entity_type", "unknown")
            properties = {k: v for k, v in entity.metadata.items() if k != "entity_type"}

        return EntityDTO(
            id=entity.id,
            entity_type=entity_type,
            name=properties.get("name", properties.get("title", "")),
            description=properties.get("description", ""),
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            metadata=entity.metadata,
            properties=properties,
        )


__all__ = [
    "CreateEntityCommand",
    "UpdateEntityCommand",
    "DeleteEntityCommand",
    "ArchiveEntityCommand",
    "RestoreEntityCommand",
    "EntityCommandHandler",
    "EntityCommandError",
    "EntityValidationError",
    "EntityNotFoundError",
]
