"""
Bulk operations workflows for the application layer.

This module implements workflows for bulk entity operations
with transaction support and error handling.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...domain.models.entity import Entity
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.entity_service import EntityService
from ..commands.entity_commands import (
    CreateEntityCommand,
    DeleteEntityCommand,
    EntityCommandHandler,
    UpdateEntityCommand,
)
from ..dto import CommandResult, EntityDTO, ResultStatus


class BulkOperationError(Exception):
    """Base exception for bulk operation errors."""

    pass


class BulkOperationValidationError(BulkOperationError):
    """Exception raised for bulk operation validation failures."""

    pass


@dataclass
class BulkCreateEntitiesWorkflow:
    """
    Workflow for bulk creating entities.

    Attributes:
        entities: List of entity creation commands
        stop_on_error: Whether to stop on first error
        transaction: Whether to use transaction (all or nothing)
    """

    entities: list[CreateEntityCommand] = field(default_factory=list)
    stop_on_error: bool = False
    transaction: bool = True

    def validate(self) -> None:
        """
        Validate workflow parameters.

        Raises:
            BulkOperationValidationError: If validation fails
        """
        if not self.entities:
            raise BulkOperationValidationError("entities list cannot be empty")
        if len(self.entities) > 1000:
            raise BulkOperationValidationError(
                "cannot create more than 1000 entities at once"
            )


@dataclass
class BulkUpdateEntitiesWorkflow:
    """
    Workflow for bulk updating entities.

    Attributes:
        updates: List of entity update commands
        stop_on_error: Whether to stop on first error
        transaction: Whether to use transaction (all or nothing)
    """

    updates: list[UpdateEntityCommand] = field(default_factory=list)
    stop_on_error: bool = False
    transaction: bool = True

    def validate(self) -> None:
        """
        Validate workflow parameters.

        Raises:
            BulkOperationValidationError: If validation fails
        """
        if not self.updates:
            raise BulkOperationValidationError("updates list cannot be empty")
        if len(self.updates) > 1000:
            raise BulkOperationValidationError(
                "cannot update more than 1000 entities at once"
            )


@dataclass
class BulkDeleteEntitiesWorkflow:
    """
    Workflow for bulk deleting entities.

    Attributes:
        entity_ids: List of entity IDs to delete
        soft_delete: Whether to soft delete
        stop_on_error: Whether to stop on first error
        transaction: Whether to use transaction (all or nothing)
    """

    entity_ids: list[str] = field(default_factory=list)
    soft_delete: bool = True
    stop_on_error: bool = False
    transaction: bool = True

    def validate(self) -> None:
        """
        Validate workflow parameters.

        Raises:
            BulkOperationValidationError: If validation fails
        """
        if not self.entity_ids:
            raise BulkOperationValidationError("entity_ids list cannot be empty")
        if len(self.entity_ids) > 1000:
            raise BulkOperationValidationError(
                "cannot delete more than 1000 entities at once"
            )


class BulkOperationsHandler:
    """
    Handler for bulk operation workflows.

    This class orchestrates bulk operations with transaction support
    and comprehensive error handling.

    Attributes:
        entity_handler: Command handler for entity operations
        logger: Logger for recording events
    """

    def __init__(
        self,
        repository: Repository[Entity],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize bulk operations handler.

        Args:
            repository: Repository for entity persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.entity_handler = EntityCommandHandler(repository, logger, cache)
        self.logger = logger

    def handle_bulk_create(
        self, workflow: BulkCreateEntitiesWorkflow
    ) -> CommandResult[list[EntityDTO]]:
        """
        Handle bulk create entities workflow.

        Args:
            workflow: Bulk create workflow

        Returns:
            Command result with list of created entity DTOs
        """
        try:
            # Validate workflow
            workflow.validate()

            self.logger.info(
                f"Starting bulk create for {len(workflow.entities)} entities"
            )

            created_entities = []
            failed_entities = []
            errors = []

            # Process each entity
            for i, command in enumerate(workflow.entities):
                try:
                    result = self.entity_handler.handle_create_entity(command)

                    if result.is_success:
                        created_entities.append(result.data)
                        self.logger.debug(
                            f"Created entity {i + 1}/{len(workflow.entities)}"
                        )
                    else:
                        failed_entities.append(i)
                        errors.append(f"Entity {i}: {result.error}")
                        self.logger.warning(
                            f"Failed to create entity {i + 1}: {result.error}"
                        )

                        if workflow.stop_on_error:
                            self.logger.info("Stopping bulk create due to error")
                            break

                except Exception as e:
                    failed_entities.append(i)
                    errors.append(f"Entity {i}: {str(e)}")
                    self.logger.error(f"Unexpected error creating entity {i + 1}: {e}")

                    if workflow.stop_on_error:
                        break

            # Handle transaction mode
            if workflow.transaction and failed_entities:
                self.logger.warning(
                    f"Transaction mode: Rolling back {len(created_entities)} created entities"
                )
                # In a real implementation, this would rollback the transaction
                # For now, we'll delete the created entities
                for entity in created_entities:
                    try:
                        delete_cmd = DeleteEntityCommand(entity_id=entity.id)
                        self.entity_handler.handle_delete_entity(delete_cmd)
                    except Exception as e:
                        self.logger.error(f"Failed to rollback entity {entity.id}: {e}")

                return CommandResult(
                    status=ResultStatus.ERROR,
                    error=f"Bulk create failed: {'; '.join(errors)}",
                    metadata={
                        "total": len(workflow.entities),
                        "failed": len(failed_entities),
                        "rolled_back": len(created_entities),
                    },
                )

            # Determine result status
            if not created_entities:
                status = ResultStatus.ERROR
            elif failed_entities:
                status = ResultStatus.PARTIAL_SUCCESS
            else:
                status = ResultStatus.SUCCESS

            self.logger.info(
                f"Bulk create completed: {len(created_entities)} created, {len(failed_entities)} failed"
            )

            return CommandResult(
                status=status,
                data=created_entities,
                error="; ".join(errors) if errors else None,
                metadata={
                    "total": len(workflow.entities),
                    "created": len(created_entities),
                    "failed": len(failed_entities),
                },
            )

        except BulkOperationValidationError as e:
            self.logger.error(f"Bulk operation validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during bulk create: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_bulk_update(
        self, workflow: BulkUpdateEntitiesWorkflow
    ) -> CommandResult[list[EntityDTO]]:
        """
        Handle bulk update entities workflow.

        Args:
            workflow: Bulk update workflow

        Returns:
            Command result with list of updated entity DTOs
        """
        try:
            # Validate workflow
            workflow.validate()

            self.logger.info(
                f"Starting bulk update for {len(workflow.updates)} entities"
            )

            updated_entities = []
            failed_entities = []
            errors = []

            # Store original states for rollback
            original_states = {}

            # Process each update
            for i, command in enumerate(workflow.updates):
                try:
                    # Store original state if in transaction mode
                    if workflow.transaction:
                        original = self.entity_handler.entity_service.get_entity(
                            command.entity_id
                        )
                        if original:
                            original_states[command.entity_id] = original

                    result = self.entity_handler.handle_update_entity(command)

                    if result.is_success:
                        updated_entities.append(result.data)
                        self.logger.debug(
                            f"Updated entity {i + 1}/{len(workflow.updates)}"
                        )
                    else:
                        failed_entities.append(i)
                        errors.append(f"Entity {i}: {result.error}")
                        self.logger.warning(
                            f"Failed to update entity {i + 1}: {result.error}"
                        )

                        if workflow.stop_on_error:
                            break

                except Exception as e:
                    failed_entities.append(i)
                    errors.append(f"Entity {i}: {str(e)}")
                    self.logger.error(f"Unexpected error updating entity {i + 1}: {e}")

                    if workflow.stop_on_error:
                        break

            # Handle transaction mode rollback
            if workflow.transaction and failed_entities:
                self.logger.warning(
                    f"Transaction mode: Rolling back {len(updated_entities)} updated entities"
                )
                for entity_id, original_state in original_states.items():
                    try:
                        # Restore original state
                        self.entity_handler.entity_service.repository.save(
                            original_state
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to rollback entity {entity_id}: {e}")

                return CommandResult(
                    status=ResultStatus.ERROR,
                    error=f"Bulk update failed: {'; '.join(errors)}",
                    metadata={
                        "total": len(workflow.updates),
                        "failed": len(failed_entities),
                        "rolled_back": len(updated_entities),
                    },
                )

            # Determine result status
            if not updated_entities:
                status = ResultStatus.ERROR
            elif failed_entities:
                status = ResultStatus.PARTIAL_SUCCESS
            else:
                status = ResultStatus.SUCCESS

            self.logger.info(
                f"Bulk update completed: {len(updated_entities)} updated, {len(failed_entities)} failed"
            )

            return CommandResult(
                status=status,
                data=updated_entities,
                error="; ".join(errors) if errors else None,
                metadata={
                    "total": len(workflow.updates),
                    "updated": len(updated_entities),
                    "failed": len(failed_entities),
                },
            )

        except BulkOperationValidationError as e:
            self.logger.error(f"Bulk operation validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during bulk update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_bulk_delete(
        self, workflow: BulkDeleteEntitiesWorkflow
    ) -> CommandResult[dict[str, Any]]:
        """
        Handle bulk delete entities workflow.

        Args:
            workflow: Bulk delete workflow

        Returns:
            Command result with deletion statistics
        """
        try:
            # Validate workflow
            workflow.validate()

            self.logger.info(
                f"Starting bulk delete for {len(workflow.entity_ids)} entities"
            )

            deleted_entities = []
            failed_entities = []
            errors = []

            # Process each delete
            for i, entity_id in enumerate(workflow.entity_ids):
                try:
                    command = DeleteEntityCommand(
                        entity_id=entity_id,
                        soft_delete=workflow.soft_delete,
                    )

                    result = self.entity_handler.handle_delete_entity(command)

                    if result.is_success:
                        deleted_entities.append(entity_id)
                        self.logger.debug(
                            f"Deleted entity {i + 1}/{len(workflow.entity_ids)}"
                        )
                    else:
                        failed_entities.append(entity_id)
                        errors.append(f"Entity {entity_id}: {result.error}")
                        self.logger.warning(
                            f"Failed to delete entity {entity_id}: {result.error}"
                        )

                        if workflow.stop_on_error:
                            break

                except Exception as e:
                    failed_entities.append(entity_id)
                    errors.append(f"Entity {entity_id}: {str(e)}")
                    self.logger.error(f"Unexpected error deleting entity {entity_id}: {e}")

                    if workflow.stop_on_error:
                        break

            # Note: Rollback for delete operations would restore deleted entities
            # This is left as a TODO for implementation with proper transaction support

            # Determine result status
            if not deleted_entities:
                status = ResultStatus.ERROR
            elif failed_entities:
                status = ResultStatus.PARTIAL_SUCCESS
            else:
                status = ResultStatus.SUCCESS

            self.logger.info(
                f"Bulk delete completed: {len(deleted_entities)} deleted, {len(failed_entities)} failed"
            )

            result_data = {
                "deleted_count": len(deleted_entities),
                "failed_count": len(failed_entities),
                "deleted_ids": deleted_entities,
                "failed_ids": failed_entities,
            }

            return CommandResult(
                status=status,
                data=result_data,
                error="; ".join(errors) if errors else None,
                metadata={
                    "total": len(workflow.entity_ids),
                    "soft_delete": workflow.soft_delete,
                },
            )

        except BulkOperationValidationError as e:
            self.logger.error(f"Bulk operation validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during bulk delete: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )


__all__ = [
    "BulkCreateEntitiesWorkflow",
    "BulkUpdateEntitiesWorkflow",
    "BulkDeleteEntitiesWorkflow",
    "BulkOperationsHandler",
    "BulkOperationError",
    "BulkOperationValidationError",
]
