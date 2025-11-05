"""
Abstract repository interface (port).

This module defines the repository interface that infrastructure
implementations must satisfy. Pure ABC with no external dependencies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """
    Abstract base class for repository pattern.

    Repositories provide persistence operations for domain entities
    without coupling the domain to specific storage implementations.

    Type parameter T represents the entity type managed by this repository.
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Save an entity to the repository.

        Args:
            entity: Entity to save

        Returns:
            Saved entity (may include generated fields)

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def get(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: Unique identifier of the entity

        Returns:
            Entity if found, None otherwise

        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: Unique identifier of the entity

        Returns:
            True if entity was deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        pass

    @abstractmethod
    def list(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> list[T]:
        """
        List entities with optional filtering and pagination.

        Args:
            filters: Dictionary of field:value filters
            limit: Maximum number of results to return
            offset: Number of results to skip
            order_by: Field name to order by (prefix with '-' for descending)

        Returns:
            List of entities matching criteria

        Raises:
            RepositoryError: If list operation fails
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        fields: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[T]:
        """
        Search entities using text search.

        Args:
            query: Search query string
            fields: List of field names to search in (None = search all)
            limit: Maximum number of results to return

        Returns:
            List of entities matching search criteria

        Raises:
            RepositoryError: If search operation fails
        """
        pass

    @abstractmethod
    def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Dictionary of field:value filters

        Returns:
            Number of entities matching criteria

        Raises:
            RepositoryError: If count operation fails
        """
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: Unique identifier of the entity

        Returns:
            True if entity exists, False otherwise

        Raises:
            RepositoryError: If existence check fails
        """
        pass


class RepositoryError(Exception):
    """Exception raised for repository operation errors."""

    pass
