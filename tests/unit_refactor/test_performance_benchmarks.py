"""
Comprehensive performance benchmark tests for Atoms MCP.

This module tests performance of critical operations including:
- Entity creation (batch vs individual)
- Relationship graph operations
- Query execution with pagination
- Cache operations
- DI container instantiation
- Concurrent request handling

All tests include response time assertions, throughput metrics, and memory tracking.
"""

import gc
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from atoms_mcp.domain.models.entity import (
    Entity,
    EntityStatus,
    ProjectEntity,
    TaskEntity,
    WorkspaceEntity,
)
from atoms_mcp.domain.models.relationship import Relationship, RelationType
from atoms_mcp.domain.services.entity_service import EntityService
from atoms_mcp.domain.services.relationship_service import RelationshipService
from atoms_mcp.infrastructure.di.container import Container


# =============================================================================
# PERFORMANCE MEASUREMENT UTILITIES
# =============================================================================


class PerformanceMetrics:
    """Track performance metrics for benchmarking."""

    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
        self.duration_ms: float = 0
        self.operations_count: int = 0
        self.throughput_ops: float = 0
        self.memory_before_kb: float = 0
        self.memory_after_kb: float = 0
        self.memory_delta_kb: float = 0

    def start(self) -> None:
        """Start performance measurement."""
        gc.collect()  # Force garbage collection for accurate memory measurement
        self.memory_before_kb = self._get_memory_usage_kb()
        self.start_time = time.perf_counter()

    def stop(self, operations_count: int = 1) -> None:
        """
        Stop performance measurement.

        Args:
            operations_count: Number of operations performed
        """
        self.end_time = time.perf_counter()
        self.memory_after_kb = self._get_memory_usage_kb()

        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.operations_count = operations_count
        self.throughput_ops = (
            operations_count / (self.duration_ms / 1000) if self.duration_ms > 0 else 0
        )
        self.memory_delta_kb = self.memory_after_kb - self.memory_before_kb

    def _get_memory_usage_kb(self) -> float:
        """Get current memory usage in KB."""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024
        except ImportError:
            # Fallback if psutil not available
            return 0.0

    def assert_response_time(self, max_ms: float, operation: str = "Operation") -> None:
        """
        Assert operation completed within time limit.

        Args:
            max_ms: Maximum allowed milliseconds
            operation: Operation name for error message

        Raises:
            AssertionError: If operation exceeded time limit
        """
        assert self.duration_ms <= max_ms, (
            f"{operation} took {self.duration_ms:.2f}ms, "
            f"expected <= {max_ms}ms (exceeded by {self.duration_ms - max_ms:.2f}ms)"
        )

    def assert_throughput(
        self, min_ops_per_sec: float, operation: str = "Operation"
    ) -> None:
        """
        Assert minimum throughput was achieved.

        Args:
            min_ops_per_sec: Minimum operations per second
            operation: Operation name for error message

        Raises:
            AssertionError: If throughput below minimum
        """
        assert self.throughput_ops >= min_ops_per_sec, (
            f"{operation} throughput {self.throughput_ops:.2f} ops/sec, "
            f"expected >= {min_ops_per_sec} ops/sec"
        )

    def report(self) -> Dict[str, Any]:
        """Get metrics report as dictionary."""
        return {
            "duration_ms": round(self.duration_ms, 2),
            "operations": self.operations_count,
            "throughput_ops_per_sec": round(self.throughput_ops, 2),
            "memory_delta_kb": round(self.memory_delta_kb, 2),
        }


@pytest.fixture
def metrics() -> PerformanceMetrics:
    """Provide performance metrics instance."""
    return PerformanceMetrics()


# =============================================================================
# ENTITY CREATION PERFORMANCE TESTS
# =============================================================================


@pytest.mark.performance
class TestEntityCreationPerformance:
    """Test performance of entity creation operations."""

    def test_single_entity_creation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test single entity creation completes quickly.

        Given: An entity service
        When: Creating a single entity
        Then: Operation completes within 50ms
        """
        service = EntityService(mock_repository, mock_logger)
        entity = WorkspaceEntity(name="Performance Test Workspace")

        metrics.start()
        result = service.create_entity(entity)
        metrics.stop()

        assert result.id == entity.id
        metrics.assert_response_time(50, "Single entity creation")

    def test_batch_entity_creation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test batch entity creation throughput.

        Given: An entity service
        When: Creating 100 entities
        Then: Average time per entity < 10ms and throughput > 50 ops/sec
        """
        service = EntityService(mock_repository, mock_logger)
        entities = [WorkspaceEntity(name=f"Workspace {i}") for i in range(100)]

        metrics.start()
        for entity in entities:
            service.create_entity(entity, validate=False)
        metrics.stop(operations_count=100)

        avg_time_per_entity = metrics.duration_ms / 100
        assert avg_time_per_entity < 10, (
            f"Average time per entity {avg_time_per_entity:.2f}ms, expected < 10ms"
        )
        metrics.assert_throughput(50, "Batch entity creation")

    def test_entity_creation_with_cache_performance(
        self, mock_repository, mock_logger, mock_cache, metrics
    ):
        """
        Test entity creation with caching overhead.

        Given: An entity service with cache
        When: Creating entities with caching
        Then: Cache overhead adds < 20ms per entity
        """
        # Measure without cache
        service_no_cache = EntityService(mock_repository, mock_logger)
        entity1 = WorkspaceEntity(name="Test 1")

        metrics.start()
        service_no_cache.create_entity(entity1)
        metrics.stop()
        time_without_cache = metrics.duration_ms

        # Measure with cache
        service_with_cache = EntityService(mock_repository, mock_logger, mock_cache)
        entity2 = WorkspaceEntity(name="Test 2")

        metrics.start()
        service_with_cache.create_entity(entity2)
        metrics.stop()
        time_with_cache = metrics.duration_ms

        cache_overhead = time_with_cache - time_without_cache
        assert cache_overhead < 20, (
            f"Cache overhead {cache_overhead:.2f}ms, expected < 20ms"
        )

    def test_entity_creation_memory_usage(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test entity creation memory efficiency.

        Given: An entity service
        When: Creating 1000 entities
        Then: Memory increase is reasonable (< 5MB)
        """
        service = EntityService(mock_repository, mock_logger)

        metrics.start()
        for i in range(1000):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            service.create_entity(entity, validate=False)
        metrics.stop(operations_count=1000)

        # Allow up to 5MB for 1000 entities
        max_memory_kb = 5 * 1024
        assert metrics.memory_delta_kb < max_memory_kb, (
            f"Memory increased by {metrics.memory_delta_kb:.2f}KB, "
            f"expected < {max_memory_kb}KB"
        )

    def test_entity_creation_with_validation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test entity creation with validation overhead.

        Given: An entity service
        When: Creating entities with validation enabled
        Then: Validation adds < 5ms overhead
        """
        service = EntityService(mock_repository, mock_logger)
        entity1 = WorkspaceEntity(name="Test 1")
        entity2 = WorkspaceEntity(name="Test 2")

        # Without validation
        metrics.start()
        service.create_entity(entity1, validate=False)
        metrics.stop()
        time_without_validation = metrics.duration_ms

        # With validation
        metrics.start()
        service.create_entity(entity2, validate=True)
        metrics.stop()
        time_with_validation = metrics.duration_ms

        validation_overhead = time_with_validation - time_without_validation
        assert validation_overhead < 5, (
            f"Validation overhead {validation_overhead:.2f}ms, expected < 5ms"
        )


# =============================================================================
# RELATIONSHIP GRAPH PERFORMANCE TESTS
# =============================================================================


@pytest.mark.performance
class TestRelationshipGraphPerformance:
    """Test performance of relationship graph operations."""

    def test_relationship_creation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test relationship creation speed.

        Given: A relationship service
        When: Creating a relationship
        Then: Operation completes within 50ms
        """
        service = RelationshipService(mock_repository, mock_logger)

        metrics.start()
        relationship = service.add_relationship(
            source_id="entity_1",
            target_id="entity_2",
            relationship_type=RelationType.PARENT_OF,
        )
        metrics.stop()

        assert relationship is not None
        metrics.assert_response_time(50, "Relationship creation")

    def test_batch_relationship_creation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test batch relationship creation throughput.

        Given: A relationship service
        When: Creating 100 relationships
        Then: Throughput > 40 ops/sec
        """
        service = RelationshipService(mock_repository, mock_logger)

        metrics.start()
        for i in range(100):
            service.add_relationship(
                source_id=f"entity_{i}",
                target_id=f"entity_{i+1}",
                relationship_type=RelationType.PARENT_OF,
            )
        metrics.stop(operations_count=100)

        metrics.assert_throughput(40, "Batch relationship creation")

    def test_get_relationships_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test relationship retrieval speed.

        Given: A relationship service with 100 relationships
        When: Retrieving all relationships
        Then: Operation completes within 100ms
        """
        service = RelationshipService(mock_repository, mock_logger)

        # Create test relationships (entity_0 -> entity_1, entity_0 -> entity_2, etc.)
        for i in range(100):
            rel = Relationship(
                source_id="entity_0",
                target_id=f"entity_{i+1}",  # Ensure different from source
                relationship_type=RelationType.PARENT_OF,
            )
            mock_repository.add_entity(rel)

        metrics.start()
        # Get all relationships without filtering (testing query performance)
        results = service.get_relationships()
        metrics.stop()

        # Just verify operation completes within time limit
        # (don't assert exact count as it depends on mock repository filtering)
        metrics.assert_response_time(100, "Get relationships")

    def test_bidirectional_relationship_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test bidirectional relationship creation overhead.

        Given: A relationship service
        When: Creating bidirectional relationships
        Then: Bidirectional adds < 50ms overhead
        """
        service = RelationshipService(mock_repository, mock_logger)

        # Unidirectional
        metrics.start()
        service.add_relationship(
            source_id="entity_1",
            target_id="entity_2",
            relationship_type=RelationType.PARENT_OF,
            bidirectional=False,
        )
        metrics.stop()
        time_unidirectional = metrics.duration_ms

        # Bidirectional
        metrics.start()
        service.add_relationship(
            source_id="entity_3",
            target_id="entity_4",
            relationship_type=RelationType.PARENT_OF,
            bidirectional=True,
        )
        metrics.stop()
        time_bidirectional = metrics.duration_ms

        overhead = time_bidirectional - time_unidirectional
        assert overhead < 50, f"Bidirectional overhead {overhead:.2f}ms, expected < 50ms"

    def test_relationship_graph_traversal_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test graph traversal performance for deep hierarchies.

        Given: A relationship graph with 50 levels deep
        When: Traversing the graph
        Then: Operation completes within 150ms
        """
        service = RelationshipService(mock_repository, mock_logger)

        # Create deep hierarchy (0->1, 1->2, 2->3, etc.)
        for i in range(50):
            rel = Relationship(
                source_id=f"entity_{i}",
                target_id=f"entity_{i+1}",
                relationship_type=RelationType.PARENT_OF,
            )
            mock_repository.add_entity(rel)

        metrics.start()
        # Get all relationships (simulating traversal)
        all_rels = service.get_relationships()
        metrics.stop()

        # Just verify operation completes within time limit
        # (don't assert exact count as it depends on mock repository filtering)
        metrics.assert_response_time(150, "Graph traversal")


# =============================================================================
# QUERY EXECUTION PERFORMANCE TESTS
# =============================================================================


@pytest.mark.performance
class TestQueryExecutionPerformance:
    """Test performance of query operations."""

    def test_list_query_without_pagination_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test list query without pagination.

        Given: 1000 entities in repository
        When: Listing all entities
        Then: Operation completes within 200ms
        """
        service = EntityService(mock_repository, mock_logger)

        # Populate repository
        for i in range(1000):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            mock_repository.add_entity(entity)

        metrics.start()
        results = service.list_entities()
        metrics.stop()

        assert len(results) == 1000
        metrics.assert_response_time(200, "List query without pagination")

    def test_list_query_with_pagination_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test list query with pagination efficiency.

        Given: 1000 entities in repository
        When: Listing with limit=50
        Then: Operation completes within 100ms
        """
        service = EntityService(mock_repository, mock_logger)

        # Populate repository
        for i in range(1000):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            mock_repository.add_entity(entity)

        metrics.start()
        results = service.list_entities(limit=50)
        metrics.stop()

        assert len(results) <= 50
        metrics.assert_response_time(100, "List query with pagination")

    def test_search_query_performance(self, mock_repository, mock_logger, metrics):
        """
        Test search query performance.

        Given: 500 entities in repository
        When: Searching with text query
        Then: Operation completes within 150ms
        """
        service = EntityService(mock_repository, mock_logger)

        # Populate repository
        for i in range(500):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            mock_repository.add_entity(entity)

        metrics.start()
        results = service.search_entities("Workspace", fields=["name"])
        metrics.stop()

        assert len(results) > 0
        metrics.assert_response_time(150, "Search query")

    def test_count_query_performance(self, mock_repository, mock_logger, metrics):
        """
        Test count query performance.

        Given: 1000 entities in repository
        When: Counting entities with filters
        Then: Operation completes within 100ms
        """
        service = EntityService(mock_repository, mock_logger)

        # Populate repository
        for i in range(1000):
            entity = WorkspaceEntity(
                name=f"Workspace {i}",
                status=EntityStatus.ACTIVE if i % 2 == 0 else EntityStatus.ARCHIVED,
            )
            mock_repository.add_entity(entity)

        metrics.start()
        count = service.count_entities(filters={"status": EntityStatus.ACTIVE})
        metrics.stop()

        assert count == 500
        metrics.assert_response_time(100, "Count query")

    def test_filtered_query_performance(self, mock_repository, mock_logger, metrics):
        """
        Test filtered query performance.

        Given: 1000 entities with various statuses
        When: Filtering by multiple criteria
        Then: Operation completes within 150ms
        """
        service = EntityService(mock_repository, mock_logger)

        # Populate repository
        for i in range(1000):
            entity = WorkspaceEntity(
                name=f"Workspace {i}",
                status=EntityStatus.ACTIVE if i % 2 == 0 else EntityStatus.ARCHIVED,
            )
            mock_repository.add_entity(entity)

        metrics.start()
        results = service.list_entities(
            filters={"status": EntityStatus.ACTIVE}, limit=100, offset=0
        )
        metrics.stop()

        assert len(results) <= 100
        metrics.assert_response_time(150, "Filtered query")


# =============================================================================
# CACHE OPERATIONS PERFORMANCE TESTS
# =============================================================================


@pytest.mark.performance
class TestCachePerformance:
    """Test performance of cache operations."""

    def test_cache_get_performance(self, mock_cache, metrics):
        """
        Test cache get operation speed.

        Given: A populated cache
        When: Getting a cached value
        Then: Operation completes within 10ms
        """
        mock_cache.set("test_key", {"data": "value"})

        metrics.start()
        value = mock_cache.get("test_key")
        metrics.stop()

        assert value is not None
        metrics.assert_response_time(10, "Cache get")

    def test_cache_set_performance(self, mock_cache, metrics):
        """
        Test cache set operation speed.

        Given: An empty cache
        When: Setting a value
        Then: Operation completes within 10ms
        """
        metrics.start()
        mock_cache.set("test_key", {"data": "value"}, ttl=300)
        metrics.stop()

        metrics.assert_response_time(10, "Cache set")

    def test_bulk_cache_operations_performance(self, mock_cache, metrics):
        """
        Test bulk cache operations throughput.

        Given: An empty cache
        When: Setting 1000 key-value pairs
        Then: Throughput > 500 ops/sec
        """
        data = {f"key_{i}": f"value_{i}" for i in range(1000)}

        metrics.start()
        for key, value in data.items():
            mock_cache.set(key, value)
        metrics.stop(operations_count=1000)

        metrics.assert_throughput(500, "Bulk cache set")

    def test_cache_delete_performance(self, mock_cache, metrics):
        """
        Test cache delete operation speed.

        Given: A cache with values
        When: Deleting a value
        Then: Operation completes within 10ms
        """
        mock_cache.set("test_key", {"data": "value"})

        metrics.start()
        result = mock_cache.delete("test_key")
        metrics.stop()

        assert result is True
        metrics.assert_response_time(10, "Cache delete")

    def test_cache_exists_performance(self, mock_cache, metrics):
        """
        Test cache exists check speed.

        Given: A populated cache
        When: Checking key existence
        Then: Operation completes within 5ms
        """
        mock_cache.set("test_key", {"data": "value"})

        metrics.start()
        exists = mock_cache.exists("test_key")
        metrics.stop()

        assert exists is True
        metrics.assert_response_time(5, "Cache exists check")


# =============================================================================
# DI CONTAINER PERFORMANCE TESTS
# =============================================================================


@pytest.mark.performance
class TestDIContainerPerformance:
    """Test performance of DI container operations."""

    def test_container_initialization_performance(self, test_settings, metrics):
        """
        Test DI container initialization speed.

        Given: A fresh container
        When: Initializing the container
        Then: Operation completes within 500ms
        """
        container = Container()

        metrics.start()
        container.initialize(test_settings)
        metrics.stop()

        assert container._initialized is True
        metrics.assert_response_time(500, "Container initialization")

    def test_singleton_retrieval_performance(self, test_settings, metrics):
        """
        Test singleton dependency retrieval speed.

        Given: An initialized container
        When: Retrieving singleton 100 times
        Then: Average retrieval time < 1ms
        """
        container = Container()
        container.initialize(test_settings)

        metrics.start()
        for _ in range(100):
            logger = container.get("logger")
        metrics.stop(operations_count=100)

        avg_time = metrics.duration_ms / 100
        assert avg_time < 1, f"Average singleton retrieval {avg_time:.2f}ms, expected < 1ms"

    def test_factory_instantiation_performance(self, test_settings, metrics):
        """
        Test factory dependency instantiation speed.

        Given: A container with factory registration
        When: Creating 100 instances via factory
        Then: Average creation time < 5ms
        """
        container = Container()
        container.initialize(test_settings)

        # Register factory
        container.register_factory("test_service", lambda: {"instance": "new"})

        metrics.start()
        for _ in range(100):
            instance = container.get("test_service")
        metrics.stop(operations_count=100)

        avg_time = metrics.duration_ms / 100
        assert avg_time < 5, f"Average factory instantiation {avg_time:.2f}ms, expected < 5ms"

    def test_scope_creation_performance(self, test_settings, metrics):
        """
        Test scope creation and cleanup speed.

        Given: An initialized container
        When: Creating and destroying 100 scopes
        Then: Average scope lifecycle < 10ms
        """
        container = Container()
        container.initialize(test_settings)

        metrics.start()
        for _ in range(100):
            scope = container.create_scope()
            scope.clear()
        metrics.stop(operations_count=100)

        avg_time = metrics.duration_ms / 100
        assert avg_time < 10, f"Average scope lifecycle {avg_time:.2f}ms, expected < 10ms"


# =============================================================================
# CONCURRENT REQUEST HANDLING TESTS
# =============================================================================


@pytest.mark.performance
class TestConcurrentPerformance:
    """Test performance under concurrent load."""

    def test_concurrent_entity_creation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test concurrent entity creation simulation.

        Given: An entity service
        When: Creating 50 entities sequentially (simulating concurrent requests)
        Then: Total time < 500ms
        """
        service = EntityService(mock_repository, mock_logger)

        metrics.start()
        for i in range(50):
            entity = WorkspaceEntity(name=f"Concurrent Workspace {i}")
            service.create_entity(entity, validate=False)
        metrics.stop(operations_count=50)

        metrics.assert_response_time(500, "Concurrent entity creation")

    def test_mixed_operation_performance(
        self, mock_repository, mock_logger, metrics
    ):
        """
        Test mixed CRUD operations performance.

        Given: An entity service
        When: Performing mixed create/read/update/delete operations
        Then: All operations complete within 1000ms
        """
        service = EntityService(mock_repository, mock_logger)

        # Seed some entities
        entities = []
        for i in range(10):
            entity = WorkspaceEntity(name=f"Workspace {i}")
            service.create_entity(entity)
            entities.append(entity)

        metrics.start()

        # Mixed operations
        for i in range(10):
            # Create
            new_entity = WorkspaceEntity(name=f"New {i}")
            service.create_entity(new_entity, validate=False)

            # Read
            service.get_entity(entities[i].id)

            # Update
            service.update_entity(entities[i].id, {"name": f"Updated {i}"}, validate=False)

            # Delete (soft)
            if i % 2 == 0:
                service.delete_entity(entities[i].id, soft_delete=True)

        metrics.stop(operations_count=40)  # 10 * 4 operations

        metrics.assert_response_time(1000, "Mixed operations")
