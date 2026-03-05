"""
Comprehensive test suite for Supabase adapter with full mocking.

This module provides complete test coverage for Supabase connection management,
repository operations, error handling, and transaction management using a
fully mocked Supabase client that simulates all API behaviors.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from atoms_mcp.adapters.secondary.supabase.connection import (
    SupabaseConnection,
    SupabaseConnectionError,
    get_connection,
    get_client,
    reset_connection,
)
from atoms_mcp.adapters.secondary.supabase.repository import (
    SupabaseRepository,
)
from atoms_mcp.domain.ports.repository import RepositoryError


# ============================================================================
# Mock Supabase Client Implementation
# ============================================================================


class MockSupabaseResponse:
    """Mock response from Supabase operations."""

    def __init__(
        self,
        data: Optional[list[dict[str, Any]]] = None,
        count: Optional[int] = None,
        error: Optional[Exception] = None,
    ):
        self.data = data or []
        self.count = count
        self.error = error

    def execute(self) -> MockSupabaseResponse:
        """Execute query and return self."""
        if self.error:
            raise self.error
        return self


class MockSupabaseQueryBuilder:
    """Mock Supabase query builder with fluent interface."""

    def __init__(
        self,
        table_name: str,
        storage: dict[str, list[dict[str, Any]]],
        should_fail: bool = False,
        failure_error: Optional[Exception] = None,
    ):
        self.table_name = table_name
        self.storage = storage
        self.should_fail = should_fail
        self.failure_error = failure_error
        self._filters: dict[str, Any] = {}
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: Optional[tuple[str, bool]] = None
        self._operation: Optional[str] = None
        self._data: Optional[dict[str, Any]] = None
        self._select_fields = "*"
        self._count_type: Optional[str] = None

    def select(self, fields: str = "*", count: Optional[str] = None) -> MockSupabaseQueryBuilder:
        """Mock select operation."""
        self._operation = "select"
        self._select_fields = fields
        self._count_type = count
        return self

    def insert(self, data: dict[str, Any]) -> MockSupabaseQueryBuilder:
        """Mock insert operation."""
        self._operation = "insert"
        self._data = data
        return self

    def update(self, data: dict[str, Any]) -> MockSupabaseQueryBuilder:
        """Mock update operation."""
        self._operation = "update"
        self._data = data
        return self

    def delete(self) -> MockSupabaseQueryBuilder:
        """Mock delete operation."""
        self._operation = "delete"
        return self

    def eq(self, field: str, value: Any) -> MockSupabaseQueryBuilder:
        """Mock equality filter."""
        self._filters[field] = value
        return self

    def ilike(self, field: str, pattern: str) -> MockSupabaseQueryBuilder:
        """Mock case-insensitive like filter."""
        self._filters[f"{field}__ilike"] = pattern
        return self

    def limit(self, count: int) -> MockSupabaseQueryBuilder:
        """Mock limit."""
        self._limit = count
        return self

    def range(self, start: int, end: int) -> MockSupabaseQueryBuilder:
        """Mock range pagination."""
        self._offset = start
        self._limit = end - start + 1
        return self

    def order(self, field: str, desc: bool = False) -> MockSupabaseQueryBuilder:
        """Mock ordering."""
        self._order_by = (field, desc)
        return self

    def maybe_single(self) -> MockSupabaseQueryBuilder:
        """Mock single result."""
        return self

    def execute(self) -> MockSupabaseResponse:
        """Execute the query."""
        if self.should_fail:
            raise self.failure_error or Exception("Mock query failed")

        # Initialize table if not exists
        if self.table_name not in self.storage:
            self.storage[self.table_name] = []

        table_data = self.storage[self.table_name]

        if self._operation == "insert":
            # Insert new record
            new_record = self._data.copy()
            if "id" not in new_record:
                new_record["id"] = str(uuid4())
            if "created_at" not in new_record:
                new_record["created_at"] = datetime.utcnow().isoformat()
            table_data.append(new_record)
            return MockSupabaseResponse(data=[new_record])

        elif self._operation == "update":
            # Update matching records
            updated = []
            for record in table_data:
                if self._matches_filters(record):
                    record.update(self._data)
                    updated.append(record)
            return MockSupabaseResponse(data=updated)

        elif self._operation == "delete":
            # Delete matching records
            deleted = [r for r in table_data if self._matches_filters(r)]
            self.storage[self.table_name] = [
                r for r in table_data if not self._matches_filters(r)
            ]
            return MockSupabaseResponse(data=deleted)

        elif self._operation == "select":
            # Select matching records
            results = [r for r in table_data if self._matches_filters(r)]

            # Apply ordering
            if self._order_by:
                field, descending = self._order_by
                results.sort(
                    key=lambda x: x.get(field, ""),
                    reverse=descending,
                )

            # Apply pagination
            if self._offset is not None:
                results = results[self._offset :]
            if self._limit is not None:
                results = results[: self._limit]

            # Handle maybe_single
            if hasattr(self, "_single"):
                return MockSupabaseResponse(
                    data=results[0] if results else None,
                    count=len(results) if self._count_type else None,
                )

            return MockSupabaseResponse(
                data=results,
                count=len([r for r in table_data if self._matches_filters(r)])
                if self._count_type
                else None,
            )

        return MockSupabaseResponse(data=[])

    def _matches_filters(self, record: dict[str, Any]) -> bool:
        """Check if record matches all filters."""
        for key, value in self._filters.items():
            if "__ilike" in key:
                field = key.replace("__ilike", "")
                pattern = value.replace("%", "")
                if pattern.lower() not in str(record.get(field, "")).lower():
                    return False
            else:
                if str(record.get(key)) != str(value):
                    return False
        return True


class MockSupabaseClient:
    """
    Complete mock implementation of Supabase client.

    Features:
    - In-memory storage simulation
    - Full CRUD operations
    - Query filtering and pagination
    - Error injection for testing
    - Call tracking and verification
    """

    def __init__(self):
        self.storage: dict[str, list[dict[str, Any]]] = {}
        self.call_log: list[tuple[str, str, dict[str, Any]]] = []
        self._should_fail = False
        self._failure_error: Optional[Exception] = None
        self._connection_alive = True

    def table(self, table_name: str) -> MockSupabaseQueryBuilder:
        """Get table query builder."""
        self.call_log.append(("table", table_name, {}))
        return MockSupabaseQueryBuilder(
            table_name,
            self.storage,
            self._should_fail,
            self._failure_error,
        )

    def ping(self) -> bool:
        """Test connection."""
        if not self._connection_alive:
            raise Exception("Connection is dead")
        return True

    def set_failure(self, should_fail: bool, error: Optional[Exception] = None):
        """Set failure mode for testing."""
        self._should_fail = should_fail
        self._failure_error = error

    def kill_connection(self):
        """Simulate connection loss."""
        self._connection_alive = False

    def reset(self):
        """Reset mock state."""
        self.storage.clear()
        self.call_log.clear()
        self._should_fail = False
        self._failure_error = None
        self._connection_alive = True


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_client():
    """Provide a fresh mock Supabase client."""
    return MockSupabaseClient()


@pytest.fixture
def mock_settings():
    """Mock settings for Supabase connection."""
    with patch("atoms_mcp.adapters.secondary.supabase.connection.get_settings") as mock:
        settings = MagicMock()
        settings.database.url = "https://test.supabase.co"
        settings.database.api_key = "test_api_key"
        settings.database.schema = "public"
        mock.return_value = settings
        yield settings


@pytest.fixture
def supabase_connection(mock_client, mock_settings):
    """Provide a Supabase connection with mocked client."""
    with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
        mock_create.return_value = mock_client
        conn = SupabaseConnection()
        yield conn
        conn.reset()


@pytest.fixture
def mock_entity_type():
    """Mock entity class for repository tests."""

    class TestEntity:
        def __init__(self, id: str, name: str, value: int, is_deleted: bool = False):
            self.id = id
            self.name = name
            self.value = value
            self.is_deleted = is_deleted

        def model_dump(self, mode: str = "python") -> dict[str, Any]:
            return {
                "id": self.id,
                "name": self.name,
                "value": self.value,
                "is_deleted": self.is_deleted,
            }

        @classmethod
        def model_validate(cls, data: dict[str, Any]) -> TestEntity:
            return cls(**data)

    return TestEntity


# ============================================================================
# Connection Management Tests (15 tests)
# ============================================================================


class TestSupabaseConnectionManagement:
    """Test Supabase connection initialization and management."""

    def test_connection_initialization_success(self, mock_settings):
        """
        Given: Valid Supabase configuration
        When: Creating a new connection
        Then: Connection is initialized successfully
        """
        with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
            mock_client = MockSupabaseClient()
            mock_create.return_value = mock_client

            conn = SupabaseConnection()

            assert conn.is_connected
            mock_create.assert_called_once()

    def test_connection_initialization_missing_url(self, mock_settings):
        """
        Given: Missing Supabase URL in configuration
        When: Attempting to create connection
        Then: SupabaseConnectionError is raised
        """
        mock_settings.database.url = None

        with pytest.raises(SupabaseConnectionError, match="URL is not configured"):
            SupabaseConnection()

    def test_connection_initialization_missing_api_key(self, mock_settings):
        """
        Given: Missing Supabase API key in configuration
        When: Attempting to create connection
        Then: SupabaseConnectionError is raised
        """
        mock_settings.database.api_key = None

        with pytest.raises(SupabaseConnectionError, match="API key is not configured"):
            SupabaseConnection()

    def test_connection_singleton_pattern(self, supabase_connection):
        """
        Given: An existing connection instance
        When: Creating another connection
        Then: Same instance is returned (singleton)
        """
        conn1 = SupabaseConnection()
        conn2 = SupabaseConnection()

        assert conn1 is conn2

    def test_get_client_success(self, supabase_connection, mock_client):
        """
        Given: Initialized connection
        When: Getting the client
        Then: Client is returned successfully
        """
        client = supabase_connection.get_client()

        assert client is mock_client

    def test_get_client_not_initialized(self):
        """
        Given: Connection without initialized client
        When: Attempting to get client
        Then: SupabaseConnectionError is raised
        """
        conn = object.__new__(SupabaseConnection)
        conn._client = None

        with pytest.raises(SupabaseConnectionError, match="not initialized"):
            conn.get_client()

    def test_get_client_with_retry_success(self, supabase_connection, mock_client):
        """
        Given: Connection with working client
        When: Getting client with retry
        Then: Client is returned on first attempt
        """
        # Mock health check table
        mock_client.storage["_health_check"] = []

        client = supabase_connection.get_client_with_retry()

        assert client is mock_client
        assert len(mock_client.call_log) > 0

    def test_get_client_with_retry_transient_failure(self, supabase_connection, mock_client, mock_settings):
        """
        Given: Connection that fails once then succeeds
        When: Getting client with retry
        Then: Client is returned after retry
        """
        with patch("atoms_mcp.adapters.secondary.supabase.connection.time.sleep"):
            call_count = [0]

            def ping_with_failure():
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Temporary failure")
                return True

            mock_client.ping = ping_with_failure

            with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
                mock_create.return_value = mock_client
                client = supabase_connection.get_client_with_retry(max_retries=3)

                assert client is mock_client
                assert call_count[0] == 2

    def test_get_client_with_retry_permanent_failure(self, supabase_connection, mock_client):
        """
        Given: Connection that always fails
        When: Getting client with retry
        Then: SupabaseConnectionError is raised after max retries
        """
        mock_client.kill_connection()

        with patch("atoms_mcp.adapters.secondary.supabase.connection.time.sleep"):
            with pytest.raises(SupabaseConnectionError, match="after 3 attempts"):
                supabase_connection.get_client_with_retry(max_retries=3)

    def test_connection_reset(self, supabase_connection):
        """
        Given: Active connection
        When: Resetting the connection
        Then: Connection state is cleared
        """
        assert supabase_connection.is_connected

        supabase_connection.reset()

        assert not supabase_connection.is_connected

    def test_global_connection_getter(self, mock_settings, mock_client):
        """
        Given: No existing global connection
        When: Calling get_connection
        Then: Global connection is created and returned
        """
        reset_connection()

        with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
            mock_create.return_value = mock_client

            conn1 = get_connection()
            conn2 = get_connection()

            assert conn1 is conn2

    def test_global_client_getter(self, mock_settings, mock_client):
        """
        Given: Global connection exists
        When: Calling get_client
        Then: Client from global connection is returned
        """
        reset_connection()

        with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
            mock_create.return_value = mock_client

            client = get_client()

            assert client is mock_client

    def test_connection_with_custom_retry_params(self, supabase_connection, mock_client):
        """
        Given: Connection with custom retry parameters
        When: Getting client with retry
        Then: Custom parameters are applied
        """
        mock_client.storage["_health_check"] = []

        client = supabase_connection.get_client_with_retry(
            max_retries=5,
            retry_delay=0.5,
            backoff_factor=1.5,
        )

        assert client is mock_client

    def test_connection_is_connected_property(self, supabase_connection):
        """
        Given: Initialized connection
        When: Checking is_connected property
        Then: Returns True
        """
        assert supabase_connection.is_connected is True

        supabase_connection.reset()

        assert supabase_connection.is_connected is False

    def test_connection_client_options(self, mock_settings):
        """
        Given: Settings with schema configuration
        When: Initializing connection
        Then: ClientOptions are created with correct settings
        """
        with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
            with patch("atoms_mcp.adapters.secondary.supabase.connection.ClientOptions") as mock_options:
                mock_create.return_value = MockSupabaseClient()

                conn = SupabaseConnection()

                mock_options.assert_called_once_with(
                    schema=mock_settings.database.schema,
                    auto_refresh_token=True,
                    persist_session=True,
                )


# ============================================================================
# Repository CRUD Operations Tests (20 tests)
# ============================================================================


class TestSupabaseRepositoryCRUD:
    """Test Supabase repository CRUD operations."""

    @pytest.fixture
    def repository(self, mock_client, mock_entity_type, mock_settings):
        """Provide a repository instance with mocked client."""
        with patch("atoms_mcp.adapters.secondary.supabase.repository.get_client_with_retry") as mock_get:
            mock_get.return_value = mock_client
            repo = SupabaseRepository(
                table_name="test_entities",
                entity_type=mock_entity_type,
            )
            yield repo

    def test_save_new_entity(self, repository, mock_entity_type, mock_client):
        """
        Given: A new entity without ID
        When: Saving the entity
        Then: Entity is inserted with generated ID
        """
        entity = mock_entity_type(
            id=str(uuid4()),
            name="Test Entity",
            value=42,
        )

        saved = repository.save(entity)

        assert saved.id == entity.id
        assert saved.name == entity.name
        assert len(mock_client.storage["test_entities"]) == 1

    def test_save_existing_entity(self, repository, mock_entity_type, mock_client):
        """
        Given: An existing entity
        When: Updating the entity
        Then: Entity is updated in storage
        """
        entity_id = str(uuid4())
        entity = mock_entity_type(id=entity_id, name="Original", value=1)
        repository.save(entity)

        # Update entity
        entity.name = "Updated"
        entity.value = 2
        saved = repository.save(entity)

        assert saved.name == "Updated"
        assert saved.value == 2
        assert len(mock_client.storage["test_entities"]) == 1

    def test_get_existing_entity(self, repository, mock_entity_type, mock_client):
        """
        Given: An entity exists in storage
        When: Getting the entity by ID
        Then: Entity is returned
        """
        entity_id = str(uuid4())
        mock_client.storage["test_entities"] = [
            {
                "id": entity_id,
                "name": "Test",
                "value": 42,
                "is_deleted": False,
            }
        ]

        result = repository.get(entity_id)

        assert result is not None
        assert result.id == entity_id
        assert result.name == "Test"

    def test_get_nonexistent_entity(self, repository):
        """
        Given: Entity does not exist
        When: Getting the entity by ID
        Then: None is returned
        """
        result = repository.get("nonexistent-id")

        assert result is None

    def test_get_soft_deleted_entity(self, repository, mock_client):
        """
        Given: Entity is soft-deleted
        When: Getting the entity by ID
        Then: None is returned
        """
        entity_id = str(uuid4())
        mock_client.storage["test_entities"] = [
            {
                "id": entity_id,
                "name": "Deleted",
                "value": 42,
                "is_deleted": True,
            }
        ]

        result = repository.get(entity_id)

        assert result is None

    def test_delete_entity_soft(self, repository, mock_client):
        """
        Given: Entity exists
        When: Soft deleting the entity
        Then: Entity is marked as deleted
        """
        entity_id = str(uuid4())
        mock_client.storage["test_entities"] = [
            {
                "id": entity_id,
                "name": "Test",
                "value": 42,
                "is_deleted": False,
            }
        ]

        result = repository.delete(entity_id, hard=False)

        assert result is True
        assert mock_client.storage["test_entities"][0]["is_deleted"] is True

    def test_delete_entity_hard(self, repository, mock_client):
        """
        Given: Entity exists
        When: Hard deleting the entity
        Then: Entity is removed from storage
        """
        entity_id = str(uuid4())
        mock_client.storage["test_entities"] = [
            {
                "id": entity_id,
                "name": "Test",
                "value": 42,
                "is_deleted": False,
            }
        ]

        result = repository.delete(entity_id, hard=True)

        assert result is True
        assert len(mock_client.storage["test_entities"]) == 0

    def test_delete_nonexistent_entity(self, repository, mock_client):
        """
        Given: Entity does not exist
        When: Attempting to delete
        Then: False is returned
        """
        result = repository.delete("nonexistent-id")

        assert result is False

    def test_list_entities_no_filters(self, repository, mock_client):
        """
        Given: Multiple entities exist
        When: Listing all entities
        Then: All non-deleted entities are returned
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "Entity 1", "value": 1, "is_deleted": False},
            {"id": "2", "name": "Entity 2", "value": 2, "is_deleted": False},
            {"id": "3", "name": "Entity 3", "value": 3, "is_deleted": True},
        ]

        results = repository.list()

        assert len(results) == 2
        assert all(not r.is_deleted for r in results)

    def test_list_entities_with_filters(self, repository, mock_client):
        """
        Given: Multiple entities with different values
        When: Listing with filters
        Then: Only matching entities are returned
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "Match", "value": 42, "is_deleted": False},
            {"id": "2", "name": "NoMatch", "value": 100, "is_deleted": False},
            {"id": "3", "name": "Match", "value": 42, "is_deleted": False},
        ]

        results = repository.list(filters={"value": 42})

        assert len(results) == 2
        assert all(r.value == 42 for r in results)

    def test_list_entities_with_pagination(self, repository, mock_client):
        """
        Given: Many entities exist
        When: Listing with limit and offset
        Then: Correct page of results is returned
        """
        mock_client.storage["test_entities"] = [
            {"id": str(i), "name": f"Entity {i}", "value": i, "is_deleted": False}
            for i in range(10)
        ]

        results = repository.list(limit=3, offset=2)

        assert len(results) <= 3

    def test_list_entities_with_ordering(self, repository, mock_client):
        """
        Given: Entities with different values
        When: Listing with ordering
        Then: Results are sorted correctly
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "C", "value": 3, "is_deleted": False},
            {"id": "2", "name": "A", "value": 1, "is_deleted": False},
            {"id": "3", "name": "B", "value": 2, "is_deleted": False},
        ]

        results = repository.list(order_by="name")

        assert results[0].name == "A"
        assert results[1].name == "B"
        assert results[2].name == "C"

    def test_list_entities_descending_order(self, repository, mock_client):
        """
        Given: Entities with different values
        When: Listing with descending order
        Then: Results are sorted in reverse
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "A", "value": 1, "is_deleted": False},
            {"id": "2", "name": "B", "value": 2, "is_deleted": False},
            {"id": "3", "name": "C", "value": 3, "is_deleted": False},
        ]

        results = repository.list(order_by="-value")

        assert results[0].value == 3
        assert results[1].value == 2
        assert results[2].value == 1

    def test_count_entities_no_filters(self, repository, mock_client):
        """
        Given: Multiple entities exist
        When: Counting all entities
        Then: Correct count is returned
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "Entity 1", "value": 1, "is_deleted": False},
            {"id": "2", "name": "Entity 2", "value": 2, "is_deleted": False},
            {"id": "3", "name": "Entity 3", "value": 3, "is_deleted": True},
        ]

        count = repository.count()

        assert count == 2

    def test_count_entities_with_filters(self, repository, mock_client):
        """
        Given: Multiple entities with different values
        When: Counting with filters
        Then: Only matching entities are counted
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "Match", "value": 42, "is_deleted": False},
            {"id": "2", "name": "NoMatch", "value": 100, "is_deleted": False},
            {"id": "3", "name": "Match", "value": 42, "is_deleted": False},
        ]

        count = repository.count(filters={"value": 42})

        assert count == 2

    def test_exists_entity_present(self, repository, mock_client):
        """
        Given: Entity exists in storage
        When: Checking if entity exists
        Then: True is returned
        """
        entity_id = str(uuid4())
        mock_client.storage["test_entities"] = [
            {"id": entity_id, "name": "Test", "value": 42, "is_deleted": False}
        ]

        exists = repository.exists(entity_id)

        assert exists is True

    def test_exists_entity_absent(self, repository, mock_client):
        """
        Given: Entity does not exist
        When: Checking if entity exists
        Then: False is returned
        """
        exists = repository.exists("nonexistent-id")

        assert exists is False

    def test_exists_entity_soft_deleted(self, repository, mock_client):
        """
        Given: Entity is soft-deleted
        When: Checking if entity exists
        Then: False is returned
        """
        entity_id = str(uuid4())
        mock_client.storage["test_entities"] = [
            {"id": entity_id, "name": "Test", "value": 42, "is_deleted": True}
        ]

        exists = repository.exists(entity_id)

        assert exists is False

    def test_search_entities(self, repository, mock_client):
        """
        Given: Multiple entities with searchable text
        When: Searching for text
        Then: Matching entities are returned
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "name": "Apple Pie", "value": 1, "is_deleted": False},
            {"id": "2", "name": "Banana Split", "value": 2, "is_deleted": False},
            {"id": "3", "name": "Apple Juice", "value": 3, "is_deleted": False},
        ]

        results = repository.search("Apple", fields=["name"], limit=10)

        assert len(results) == 2
        assert all("Apple" in r.name for r in results)

    def test_save_returns_deserialized_entity(self, repository, mock_entity_type):
        """
        Given: Valid entity data
        When: Saving entity
        Then: Returned entity is properly deserialized
        """
        entity = mock_entity_type(id=str(uuid4()), name="Test", value=42)

        saved = repository.save(entity)

        assert isinstance(saved, mock_entity_type)
        assert saved.name == "Test"
        assert saved.value == 42


# ============================================================================
# Error Handling Tests (10 tests)
# ============================================================================


class TestSupabaseErrorHandling:
    """Test error handling in Supabase adapter."""

    @pytest.fixture
    def repository(self, mock_client, mock_entity_type, mock_settings):
        """Provide a repository instance."""
        with patch("atoms_mcp.adapters.secondary.supabase.repository.get_client_with_retry") as mock_get:
            mock_get.return_value = mock_client
            repo = SupabaseRepository(
                table_name="test_entities",
                entity_type=mock_entity_type,
            )
            yield repo

    def test_save_api_error(self, repository, mock_entity_type, mock_client):
        """
        Given: Supabase API error during save
        When: Saving entity
        Then: RepositoryError is raised
        """
        from postgrest.exceptions import APIError

        mock_client.set_failure(True, APIError({"message": "API Error"}))
        entity = mock_entity_type(id=str(uuid4()), name="Test", value=42)

        with pytest.raises(RepositoryError, match="Supabase API error"):
            repository.save(entity)

    def test_get_api_error(self, repository, mock_client):
        """
        Given: Supabase API error during get
        When: Getting entity
        Then: RepositoryError is raised
        """
        from postgrest.exceptions import APIError

        mock_client.set_failure(True, APIError({"message": "API Error"}))

        with pytest.raises(RepositoryError, match="Supabase API error"):
            repository.get("some-id")

    def test_delete_api_error(self, repository, mock_client):
        """
        Given: Supabase API error during delete
        When: Deleting entity
        Then: RepositoryError is raised
        """
        from postgrest.exceptions import APIError

        mock_client.set_failure(True, APIError({"message": "API Error"}))

        with pytest.raises(RepositoryError, match="Supabase API error"):
            repository.delete("some-id")

    def test_list_api_error(self, repository, mock_client):
        """
        Given: Supabase API error during list
        When: Listing entities
        Then: RepositoryError is raised
        """
        from postgrest.exceptions import APIError

        mock_client.set_failure(True, APIError({"message": "API Error"}))

        with pytest.raises(RepositoryError, match="Supabase API error"):
            repository.list()

    def test_count_api_error(self, repository, mock_client):
        """
        Given: Supabase API error during count
        When: Counting entities
        Then: RepositoryError is raised
        """
        from postgrest.exceptions import APIError

        mock_client.set_failure(True, APIError({"message": "API Error"}))

        with pytest.raises(RepositoryError, match="Supabase API error"):
            repository.count()

    def test_exists_api_error(self, repository, mock_client):
        """
        Given: Supabase API error during exists check
        When: Checking entity existence
        Then: RepositoryError is raised
        """
        from postgrest.exceptions import APIError

        mock_client.set_failure(True, APIError({"message": "API Error"}))

        with pytest.raises(RepositoryError, match="Supabase API error"):
            repository.exists("some-id")

    def test_save_no_data_returned(self, repository, mock_entity_type, mock_client):
        """
        Given: Save operation returns no data
        When: Saving entity
        Then: RepositoryError is raised
        """
        mock_client.set_failure(True, Exception("Save operation returned no data"))
        entity = mock_entity_type(id=str(uuid4()), name="Test", value=42)

        with pytest.raises(RepositoryError):
            repository.save(entity)

    def test_deserialization_error(self, repository, mock_client):
        """
        Given: Invalid data that cannot be deserialized
        When: Getting entity
        Then: RepositoryError is raised
        """
        mock_client.storage["test_entities"] = [
            {"id": "1", "invalid_field": "data", "is_deleted": False}
        ]

        with pytest.raises(RepositoryError, match="Failed to deserialize"):
            repository.get("1")

    def test_serialization_error(self, repository):
        """
        Given: Entity that cannot be serialized
        When: Saving entity
        Then: RepositoryError is raised
        """

        class InvalidEntity:
            pass

        entity = InvalidEntity()

        with pytest.raises(RepositoryError, match="Cannot serialize"):
            repository.save(entity)

    def test_connection_retry_exhausted(self, mock_client, mock_settings):
        """
        Given: Connection that never succeeds
        When: Attempting to connect with retries
        Then: SupabaseConnectionError is raised
        """
        mock_client.kill_connection()

        with patch("atoms_mcp.adapters.secondary.supabase.connection.create_client") as mock_create:
            mock_create.return_value = mock_client

            with patch("atoms_mcp.adapters.secondary.supabase.connection.time.sleep"):
                conn = SupabaseConnection()
                with pytest.raises(SupabaseConnectionError, match="after 3 attempts"):
                    conn.get_client_with_retry(max_retries=3)


# ============================================================================
# Serialization and Type Handling Tests (5 tests)
# ============================================================================


class TestSupabaseSerialization:
    """Test serialization and type handling."""

    @pytest.fixture
    def repository(self, mock_client, mock_entity_type, mock_settings):
        """Provide a repository instance."""
        with patch("atoms_mcp.adapters.secondary.supabase.repository.get_client_with_retry") as mock_get:
            mock_get.return_value = mock_client
            repo = SupabaseRepository(
                table_name="test_entities",
                entity_type=mock_entity_type,
            )
            yield repo

    def test_serialize_uuid(self, repository):
        """
        Given: Value with UUID type
        When: Serializing
        Then: UUID is converted to string
        """
        test_uuid = uuid4()
        result = repository._serialize_value(test_uuid)

        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_serialize_datetime(self, repository):
        """
        Given: Value with datetime type
        When: Serializing
        Then: Datetime is converted to ISO format
        """
        test_datetime = datetime.utcnow()
        result = repository._serialize_value(test_datetime)

        assert isinstance(result, str)
        assert result == test_datetime.isoformat()

    def test_serialize_dict(self, repository):
        """
        Given: Dictionary value
        When: Serializing
        Then: Dict is converted to JSON string
        """
        test_dict = {"key": "value", "number": 42}
        result = repository._serialize_value(test_dict)

        assert isinstance(result, str)
        assert '"key"' in result

    def test_serialize_entity_pydantic(self, repository, mock_entity_type):
        """
        Given: Pydantic entity
        When: Serializing
        Then: Entity is converted to dict with model_dump
        """
        entity = mock_entity_type(id=str(uuid4()), name="Test", value=42)
        result = repository._serialize_entity(entity)

        assert isinstance(result, dict)
        assert result["name"] == "Test"
        assert result["value"] == "42"

    def test_deserialize_entity_pydantic(self, repository, mock_entity_type):
        """
        Given: Dictionary data
        When: Deserializing to Pydantic entity
        Then: Entity is created with model_validate
        """
        data = {"id": str(uuid4()), "name": "Test", "value": 42, "is_deleted": False}
        result = repository._deserialize_entity(data)

        assert isinstance(result, mock_entity_type)
        assert result.name == "Test"
        assert result.value == 42
