"""
Relationship queries for the application layer.

This module implements query handlers for relationship retrieval and graph operations.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from ...domain.models.relationship import Relationship, RelationType
from ...domain.ports.cache import Cache
from ...domain.ports.logger import Logger
from ...domain.ports.repository import Repository, RepositoryError
from ...domain.services.relationship_service import RelationshipService
from ..dto import QueryResult, RelationshipDTO, ResultStatus


class RelationshipQueryError(Exception):
    """Base exception for relationship query errors."""

    pass


class RelationshipQueryValidationError(RelationshipQueryError):
    """Exception raised for query validation failures."""

    pass


@dataclass
class GetRelationshipsQuery:
    """
    Query to get relationships matching criteria.

    Attributes:
        source_id: Filter by source entity ID
        target_id: Filter by target entity ID
        relationship_type: Filter by relationship type
        page: Page number (1-indexed)
        page_size: Number of items per page
    """

    source_id: Optional[str] = None
    target_id: Optional[str] = None
    relationship_type: Optional[str] = None
    page: int = 1
    page_size: int = 20

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            RelationshipQueryValidationError: If validation fails
        """
        if self.page < 1:
            raise RelationshipQueryValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise RelationshipQueryValidationError(
                "page_size must be between 1 and 1000"
            )

        if self.relationship_type:
            try:
                RelationType(self.relationship_type)
            except ValueError:
                raise RelationshipQueryValidationError(
                    f"Invalid relationship_type: {self.relationship_type}"
                )


@dataclass
class FindPathQuery:
    """
    Query to find a path between two entities.

    Attributes:
        start_id: Starting entity ID
        end_id: Target entity ID
        max_depth: Maximum path length
    """

    start_id: str
    end_id: str
    max_depth: int = 10

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            RelationshipQueryValidationError: If validation fails
        """
        if not self.start_id:
            raise RelationshipQueryValidationError("start_id is required")
        if not self.end_id:
            raise RelationshipQueryValidationError("end_id is required")
        if self.max_depth < 1 or self.max_depth > 100:
            raise RelationshipQueryValidationError(
                "max_depth must be between 1 and 100"
            )


@dataclass
class GetRelatedEntitiesQuery:
    """
    Query to get entities related to a given entity.

    Attributes:
        entity_id: Entity ID to get related entities for
        relationship_type: Filter by relationship type
        direction: "outgoing", "incoming", or "both"
    """

    entity_id: str
    relationship_type: Optional[str] = None
    direction: str = "outgoing"

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            RelationshipQueryValidationError: If validation fails
        """
        if not self.entity_id:
            raise RelationshipQueryValidationError("entity_id is required")
        if self.direction not in ("outgoing", "incoming", "both"):
            raise RelationshipQueryValidationError(
                "direction must be 'outgoing', 'incoming', or 'both'"
            )

        if self.relationship_type:
            try:
                RelationType(self.relationship_type)
            except ValueError:
                raise RelationshipQueryValidationError(
                    f"Invalid relationship_type: {self.relationship_type}"
                )


@dataclass
class GetDescendantsQuery:
    """
    Query to get all descendant entities.

    Attributes:
        entity_id: Root entity ID
        relationship_type: Type of parent-child relationship
        max_depth: Maximum depth to traverse
    """

    entity_id: str
    relationship_type: str = "parent_of"
    max_depth: int = 10

    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            RelationshipQueryValidationError: If validation fails
        """
        if not self.entity_id:
            raise RelationshipQueryValidationError("entity_id is required")
        if self.max_depth < 1 or self.max_depth > 100:
            raise RelationshipQueryValidationError(
                "max_depth must be between 1 and 100"
            )

        try:
            RelationType(self.relationship_type)
        except ValueError:
            raise RelationshipQueryValidationError(
                f"Invalid relationship_type: {self.relationship_type}"
            )


class RelationshipQueryHandler:
    """
    Handler for relationship queries.

    This class handles relationship retrieval and graph operations
    using the domain service.

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
        Initialize relationship query handler.

        Args:
            repository: Repository for relationship persistence
            logger: Logger for recording events
            cache: Optional cache for performance
        """
        self.relationship_service = RelationshipService(repository, logger, cache)
        self.logger = logger

    def handle_get_relationships(
        self, query: GetRelationshipsQuery
    ) -> QueryResult[list[RelationshipDTO]]:
        """
        Handle get relationships query.

        Args:
            query: Get relationships query

        Returns:
            Query result with list of relationship DTOs
        """
        try:
            # Validate query
            query.validate()

            # Parse relationship type
            relationship_type = None
            if query.relationship_type:
                relationship_type = RelationType(query.relationship_type)

            # Get relationships using service
            relationships = self.relationship_service.get_relationships(
                source_id=query.source_id,
                target_id=query.target_id,
                relationship_type=relationship_type,
            )

            # Apply pagination
            total_count = len(relationships)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            paginated_relationships = relationships[start_idx:end_idx]

            # Convert to DTOs
            dtos = [
                self._relationship_to_dto(rel) for rel in paginated_relationships
            ]

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dtos,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                metadata={
                    "source_id": query.source_id,
                    "target_id": query.target_id,
                    "relationship_type": query.relationship_type,
                },
            )

        except RelationshipQueryValidationError as e:
            self.logger.error(f"Relationship query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except RepositoryError as e:
            self.logger.error(f"Repository error during relationship retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Failed to retrieve relationships: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during relationship retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_find_path(
        self, query: FindPathQuery
    ) -> QueryResult[list[RelationshipDTO]]:
        """
        Handle find path query.

        Args:
            query: Find path query

        Returns:
            Query result with path as list of relationship DTOs
        """
        try:
            # Validate query
            query.validate()

            # Find path using service
            path = self.relationship_service.find_path(
                query.start_id, query.end_id, query.max_depth
            )

            if path is None:
                return QueryResult(
                    status=ResultStatus.SUCCESS,
                    data=[],
                    total_count=0,
                    page=1,
                    page_size=1,
                    metadata={
                        "start_id": query.start_id,
                        "end_id": query.end_id,
                        "path_found": False,
                    },
                )

            # Convert to DTOs
            dtos = [self._relationship_to_dto(rel) for rel in path]

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=dtos,
                total_count=len(dtos),
                page=1,
                page_size=len(dtos),
                metadata={
                    "start_id": query.start_id,
                    "end_id": query.end_id,
                    "path_found": True,
                    "path_length": len(dtos),
                },
            )

        except RelationshipQueryValidationError as e:
            self.logger.error(f"Relationship query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during path finding: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_get_related_entities(
        self, query: GetRelatedEntitiesQuery
    ) -> QueryResult[list[str]]:
        """
        Handle get related entities query.

        Args:
            query: Get related entities query

        Returns:
            Query result with list of related entity IDs
        """
        try:
            # Validate query
            query.validate()

            # Parse relationship type
            relationship_type = None
            if query.relationship_type:
                relationship_type = RelationType(query.relationship_type)

            # Get related entities using service
            related_ids = self.relationship_service.get_related_entities(
                query.entity_id,
                relationship_type=relationship_type,
                direction=query.direction,
            )

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=related_ids,
                total_count=len(related_ids),
                page=1,
                page_size=len(related_ids),
                metadata={
                    "entity_id": query.entity_id,
                    "relationship_type": query.relationship_type,
                    "direction": query.direction,
                },
            )

        except RelationshipQueryValidationError as e:
            self.logger.error(f"Relationship query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during related entities retrieval: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_get_descendants(
        self, query: GetDescendantsQuery
    ) -> QueryResult[list[str]]:
        """
        Handle get descendants query.

        Args:
            query: Get descendants query

        Returns:
            Query result with list of descendant entity IDs
        """
        try:
            # Validate query
            query.validate()

            # Parse relationship type
            relationship_type = RelationType(query.relationship_type)

            # Get descendants using service
            descendants = self.relationship_service.get_descendants(
                query.entity_id,
                relationship_type=relationship_type,
                max_depth=query.max_depth,
            )

            # Convert set to list for serialization
            descendant_list = list(descendants)

            return QueryResult(
                status=ResultStatus.SUCCESS,
                data=descendant_list,
                total_count=len(descendant_list),
                page=1,
                page_size=len(descendant_list),
                metadata={
                    "entity_id": query.entity_id,
                    "relationship_type": query.relationship_type,
                    "max_depth": query.max_depth,
                },
            )

        except RelationshipQueryValidationError as e:
            self.logger.error(f"Relationship query validation failed: {e}")
            return QueryResult(
                status=ResultStatus.ERROR,
                error=f"Validation error: {str(e)}",
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during descendants retrieval: {e}")
            return QueryResult(
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
    "GetRelationshipsQuery",
    "FindPathQuery",
    "GetRelatedEntitiesQuery",
    "GetDescendantsQuery",
    "RelationshipQueryHandler",
    "RelationshipQueryError",
    "RelationshipQueryValidationError",
]
