"""
Supabase repository implementation.

This module provides a concrete implementation of the Repository port
for Supabase, handling CRUD operations with proper serialization and
error handling.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from postgrest.exceptions import APIError

from atoms_mcp.adapters.secondary.supabase.connection import get_client_with_retry
from atoms_mcp.domain.ports.repository import Repository, RepositoryError

T = TypeVar("T")


class SupabaseRepository(Repository[T], Generic[T]):
    """
    Supabase implementation of the Repository port.

    This repository handles:
    - UUID and datetime serialization
    - Soft deletes with is_deleted flag
    - Pagination support
    - Error handling and retries
    - Type-safe entity operations

    Type parameter T represents the entity type managed by this repository.
    """

    def __init__(
        self,
        table_name: str,
        entity_type: type[T],
        id_field: str = "id",
    ) -> None:
        """
        Initialize repository for a specific table.

        Args:
            table_name: Name of the Supabase table
            entity_type: Type of entities stored in this repository
            id_field: Name of the ID field (default: "id")
        """
        self.table_name = table_name
        self.entity_type = entity_type
        self.id_field = id_field

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize Python values for Supabase storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized value suitable for Supabase
        """
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    def _serialize_entity(self, entity: T) -> dict[str, Any]:
        """
        Serialize entity to dictionary for Supabase.

        Args:
            entity: Entity to serialize

        Returns:
            Dictionary representation suitable for Supabase
        """
        if hasattr(entity, "model_dump"):
            # Pydantic model
            data = entity.model_dump(mode="json")
        elif hasattr(entity, "__dict__"):
            # Regular class
            data = {k: v for k, v in entity.__dict__.items() if not k.startswith("_")}
        else:
            raise RepositoryError(f"Cannot serialize entity of type {type(entity)}")

        # Serialize special types
        return {k: self._serialize_value(v) for k, v in data.items()}

    def _deserialize_entity(self, data: dict[str, Any]) -> T:
        """
        Deserialize dictionary from Supabase to entity.

        Args:
            data: Dictionary from Supabase

        Returns:
            Deserialized entity

        Raises:
            RepositoryError: If deserialization fails
        """
        try:
            if hasattr(self.entity_type, "model_validate"):
                # Pydantic model
                return self.entity_type.model_validate(data)
            else:
                # Regular class - try direct instantiation
                return self.entity_type(**data)
        except Exception as e:
            raise RepositoryError(f"Failed to deserialize entity: {e}") from e

    def save(self, entity: T) -> T:
        """
        Save an entity to Supabase.

        Performs upsert operation - inserts new entities or updates existing ones.

        Args:
            entity: Entity to save

        Returns:
            Saved entity with any generated fields

        Raises:
            RepositoryError: If save operation fails
        """
        try:
            client = get_client_with_retry()
            data = self._serialize_entity(entity)

            # Check if entity has ID and exists
            entity_id = data.get(self.id_field)
            if entity_id and self.exists(str(entity_id)):
                # Update existing entity
                response = (
                    client.table(self.table_name)
                    .update(data)
                    .eq(self.id_field, str(entity_id))
                    .execute()
                )
            else:
                # Insert new entity
                response = client.table(self.table_name).insert(data).execute()

            if not response.data:
                raise RepositoryError("Save operation returned no data")

            return self._deserialize_entity(response.data[0])

        except APIError as e:
            raise RepositoryError(f"Supabase API error during save: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to save entity: {e}") from e

    def get(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by ID.

        Args:
            entity_id: Unique identifier of the entity

        Returns:
            Entity if found and not soft-deleted, None otherwise

        Raises:
            RepositoryError: If retrieval operation fails
        """
        try:
            client = get_client_with_retry()

            response = (
                client.table(self.table_name)
                .select("*")
                .eq(self.id_field, entity_id)
                .eq("is_deleted", False)
                .maybe_single()
                .execute()
            )

            if response.data is None:
                return None

            return self._deserialize_entity(response.data)

        except APIError as e:
            raise RepositoryError(f"Supabase API error during get: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to get entity: {e}") from e

    def delete(self, entity_id: str, hard: bool = False) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: Unique identifier of the entity
            hard: If True, perform hard delete; if False, soft delete (default)

        Returns:
            True if entity was deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        try:
            client = get_client_with_retry()

            if hard:
                # Hard delete - remove from database
                response = (
                    client.table(self.table_name)
                    .delete()
                    .eq(self.id_field, entity_id)
                    .execute()
                )
            else:
                # Soft delete - set is_deleted flag
                response = (
                    client.table(self.table_name)
                    .update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()})
                    .eq(self.id_field, entity_id)
                    .eq("is_deleted", False)
                    .execute()
                )

            return len(response.data) > 0

        except APIError as e:
            raise RepositoryError(f"Supabase API error during delete: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to delete entity: {e}") from e

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
        try:
            client = get_client_with_retry()

            # Build query
            query = client.table(self.table_name).select("*")

            # Always filter out soft-deleted entities
            query = query.eq("is_deleted", False)

            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None:
                        query = query.eq(field, self._serialize_value(value))

            # Apply ordering
            if order_by:
                descending = order_by.startswith("-")
                field = order_by.lstrip("-")
                query = query.order(field, desc=descending)

            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.range(offset, offset + (limit or 1000) - 1)

            response = query.execute()

            return [self._deserialize_entity(item) for item in response.data]

        except APIError as e:
            raise RepositoryError(f"Supabase API error during list: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to list entities: {e}") from e

    def search(
        self,
        query: str,
        fields: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[T]:
        """
        Search entities using text search.

        Note: This implementation uses PostgreSQL's ilike operator for simple
        text matching. For full-text search, consider using Supabase's
        text search functions.

        Args:
            query: Search query string
            fields: List of field names to search in (None = search all text fields)
            limit: Maximum number of results to return

        Returns:
            List of entities matching search criteria

        Raises:
            RepositoryError: If search operation fails
        """
        try:
            client = get_client_with_retry()

            # For simple implementation, search in common text fields
            # This should be enhanced based on table schema
            search_fields = fields or ["name", "description", "title", "content"]
            pattern = f"%{query}%"

            # Build OR query for multiple fields
            base_query = client.table(self.table_name).select("*").eq("is_deleted", False)

            # Apply OR conditions for each search field
            results = []
            for field in search_fields:
                try:
                    field_query = base_query.ilike(field, pattern)
                    if limit:
                        field_query = field_query.limit(limit)
                    response = field_query.execute()
                    results.extend(response.data)
                except APIError:
                    # Field might not exist in this table, skip it
                    continue

            # Remove duplicates based on ID
            unique_items = {item[self.id_field]: item for item in results}
            return [self._deserialize_entity(item) for item in unique_items.values()]

        except Exception as e:
            raise RepositoryError(f"Failed to search entities: {e}") from e

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
        try:
            client = get_client_with_retry()

            # Build query with count
            query = client.table(self.table_name).select("*", count="exact")

            # Always filter out soft-deleted entities
            query = query.eq("is_deleted", False)

            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None:
                        query = query.eq(field, self._serialize_value(value))

            response = query.execute()

            return response.count or 0

        except APIError as e:
            raise RepositoryError(f"Supabase API error during count: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to count entities: {e}") from e

    def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists.

        Args:
            entity_id: Unique identifier of the entity

        Returns:
            True if entity exists and is not soft-deleted, False otherwise

        Raises:
            RepositoryError: If existence check fails
        """
        try:
            client = get_client_with_retry()

            response = (
                client.table(self.table_name)
                .select(self.id_field, count="exact")
                .eq(self.id_field, entity_id)
                .eq("is_deleted", False)
                .execute()
            )

            return (response.count or 0) > 0

        except APIError as e:
            raise RepositoryError(f"Supabase API error during exists check: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to check entity existence: {e}") from e
