"""
Relationship commands for the application layer.

This module implements command handlers for relationship operations.
Commands validate inputs before calling domain services.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...domain.models.relationship import Relationship, RelationType
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.relationship_service import RelationshipService
from ..dto import CommandResult, RelationshipDTO, ResultStatus


class RelationshipCommandError(Exception):
    """Base exception for relationship command errors."""

    pass


class RelationshipValidationError(RelationshipCommandError):
    """Exception raised for relationship validation failures."""

    pass


class RelationshipNotFoundError(RelationshipCommandError):
    """Exception raised when relationship is not found."""

    pass


@dataclass
class CreateRelationshipCommand:
    """
    Command to create a new relationship.

    Attributes:
        source_id: Source entity ID
        target_id: Target entity ID
        relationship_type: Type of relationship
        properties: Optional relationship properties
        bidirectional: Whether to create inverse relationship
        created_by: ID of user creating the relationship
    """

    source_id: str
    target_id: str
    relationship_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    bidirectional: bool = False
    created_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            RelationshipValidationError: If validation fails
        """
        if not self.source_id:
            raise RelationshipValidationError("source_id is required")
        if not self.target_id:
            raise RelationshipValidationError("target_id is required")
        if not self.relationship_type:
            raise RelationshipValidationError("relationship_type is required")
        if self.source_id == self.target_id:
            raise RelationshipValidationError(
                "source_id and target_id cannot be the same"
            )

        # Validate relationship type
        try:
            RelationType(self.relationship_type)
        except ValueError:
            raise RelationshipValidationError(
                f"Invalid relationship_type: {self.relationship_type}"
            )


@dataclass
class DeleteRelationshipCommand:
    """
    Command to delete a relationship.

    Attributes:
        relationship_id: ID of relationship to delete (optional if source/target provided)
        source_id: Source entity ID (optional if relationship_id provided)
        target_id: Target entity ID (optional if relationship_id provided)
        relationship_type: Type of relationship (optional if relationship_id provided)
        remove_inverse: Whether to also remove inverse relationship
        deleted_by: ID of user deleting the relationship
    """

    relationship_id: Optional[str] = None
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    relationship_type: Optional[str] = None
    remove_inverse: bool = False
    deleted_by: Optional[str] = None

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            RelationshipValidationError: If validation fails
        """
        if not self.relationship_id and not (self.source_id and self.target_id):
            raise RelationshipValidationError(
                "Either relationship_id or (source_id and target_id) must be provided"
            )


@dataclass
class UpdateRelationshipCommand:
    """
    Command to update a relationship's properties.

    Attributes:
        relationship_id: ID of relationship to update
        properties: Properties to update
    """

    relationship_id: str
    properties: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """
        Validate command parameters.

        Raises:
            RelationshipValidationError: If validation fails
        """
        if not self.relationship_id:
            raise RelationshipValidationError("relationship_id is required")
        if not self.properties:
            raise RelationshipValidationError("properties cannot be empty")


class RelationshipCommandHandler:
    """
    Handler for relationship commands.

    This class orchestrates relationship operations using the domain service
    and returns DTOs suitable for serialization.

    Attributes:
        relationship_service: Domain service for relationship operations
        logger: Logger for recording events
    """

    def __init__(
        self,
        repository: Repository[Relationship],
        logger: Logger,
        cache: Optional[Cache] = None,
    ):
        """
        Initialize relationship command handler.

        Args:
            repository: Repository for relationship persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.relationship_service = RelationshipService(repository, logger, cache)
        self.logger = logger

    def handle_create_relationship(
        self, command: CreateRelationshipCommand
    ) -> CommandResult[RelationshipDTO]:
        """
        Handle create relationship command.

        Args:
            command: Create relationship command

        Returns:
            Command result with relationship DTO
        """
        try:
            # Validate command
            command.validate()

            # Parse relationship type
            relationship_type = RelationType(command.relationship_type)

            # Create relationship using service
            created_relationship = self.relationship_service.add_relationship(
                source_id=command.source_id,
                target_id=command.target_id,
                relationship_type=relationship_type,
                properties=command.properties,
                bidirectional=command.bidirectional,
                created_by=command.created_by,
            )

            # Convert to DTO
            dto = self._relationship_to_dto(created_relationship)

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={
                    "relationship_id": created_relationship.id,
                    "bidirectional": command.bidirectional,
                },
            )

        except RelationshipValidationError as e:
            self.logger.error(f"Relationship validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except ValueError as e:
            self.logger.error(f"Invalid relationship type: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Invalid relationship type: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during relationship creation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to create relationship: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during relationship creation: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_delete_relationship(
        self, command: DeleteRelationshipCommand
    ) -> CommandResult[bool]:
        """
        Handle delete relationship command.

        Args:
            command: Delete relationship command

        Returns:
            Command result with success boolean
        """
        try:
            # Validate command
            command.validate()

            if command.relationship_id:
                # Delete by ID
                success = self.relationship_service.remove_relationship(
                    command.relationship_id,
                    remove_inverse=command.remove_inverse,
                )

                if not success:
                    raise RelationshipNotFoundError(
                        f"Relationship {command.relationship_id} not found"
                    )

                relationship_id = command.relationship_id

            else:
                # Find and delete by source/target
                relationship_type = None
                if command.relationship_type:
                    relationship_type = RelationType(command.relationship_type)

                relationships = self.relationship_service.get_relationships(
                    source_id=command.source_id,
                    target_id=command.target_id,
                    relationship_type=relationship_type,
                )

                if not relationships:
                    raise RelationshipNotFoundError(
                        f"No relationship found between {command.source_id} and {command.target_id}"
                    )

                # Delete first matching relationship
                relationship = relationships[0]
                success = self.relationship_service.remove_relationship(
                    relationship.id,
                    remove_inverse=command.remove_inverse,
                )

                relationship_id = relationship.id

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=True,
                metadata={
                    "relationship_id": relationship_id,
                    "remove_inverse": command.remove_inverse,
                },
            )

        except RelationshipValidationError as e:
            self.logger.error(f"Relationship validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RelationshipNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during relationship deletion: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to delete relationship: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during relationship deletion: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_update_relationship(
        self, command: UpdateRelationshipCommand
    ) -> CommandResult[RelationshipDTO]:
        """
        Handle update relationship command.

        Args:
            command: Update relationship command

        Returns:
            Command result with updated relationship DTO
        """
        try:
            # Validate command
            command.validate()

            # Get existing relationship
            relationships = self.relationship_service.get_relationships()
            relationship = next(
                (r for r in relationships if r.id == command.relationship_id), None
            )

            if not relationship:
                raise RelationshipNotFoundError(
                    f"Relationship {command.relationship_id} not found"
                )

            # Update properties
            for key, value in command.properties.items():
                relationship.set_property(key, value)

            # Save updated relationship
            updated_relationship = self.relationship_service.repository.save(
                relationship
            )

            # Convert to DTO
            dto = self._relationship_to_dto(updated_relationship)

            return CommandResult(
                status=ResultStatus.SUCCESS,
                data=dto,
                metadata={"relationship_id": updated_relationship.id},
            )

        except RelationshipValidationError as e:
            self.logger.error(f"Relationship validation failed: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RelationshipNotFoundError as e:
            self.logger.error(str(e))
            return CommandResult(
                status=ResultStatus.ERROR,
                error=str(e),
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during relationship update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Failed to update relationship: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during relationship update: {e}")
            return CommandResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def _relationship_to_dto(self, relationship: Relationship) -> RelationshipDTO:
        """
        Convert relationship to DTO.

        Args:
            relationship: Relationship to convert

        Returns:
            RelationshipDTO instance
        """
        return RelationshipDTO(
            id=relationship.id,
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            relationship_type=relationship.relationship_type.value,
            status=relationship.status.value,
            created_at=relationship.created_at,
            updated_at=relationship.updated_at,
            created_by=relationship.created_by,
            properties=relationship.properties,
        )


__all__ = [
    "CreateRelationshipCommand",
    "DeleteRelationshipCommand",
    "UpdateRelationshipCommand",
    "RelationshipCommandHandler",
    "RelationshipCommandError",
    "RelationshipValidationError",
    "RelationshipNotFoundError",
]
