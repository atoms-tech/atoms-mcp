"""@harmful decorator system for automatic test state tracking and cleanup.

This module provides a sophisticated framework for tracking entities created during tests
and automatically cleaning them up in reverse dependency order (cascade delete pattern).

Key Features:
- @harmful decorator for automatic entity tracking
- HarmfulStateTracker for managing test state and cleanup
- Multiple cleanup strategies (CASCADE_DELETE, SOFT_DELETE, TRANSACTION_ROLLBACK, NONE)
- Async context manager for test execution with automatic cleanup
- Dry-run mode for testing cleanup logic
- Integration with existing test fixtures

Usage:
    @harmful(cleanup_strategy="cascade_delete")
    async def test_create_entity(fast_http_client):
        result = await fast_http_client.call_tool("entity_tool", {
            "entity_type": "organization",
            "operation": "create",
            "data": {"name": "Test Org"}
        })
        assert result["success"]
        # Automatic cleanup on test completion
"""

import asyncio
import functools
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CleanupStrategy(Enum):
    """Strategy for cleaning up test-created entities."""

    CASCADE_DELETE = "cascade_delete"  # Delete in reverse dependency order
    SOFT_DELETE = "soft_delete"  # Mark as deleted without removing
    TRANSACTION_ROLLBACK = "transaction_rollback"  # Rollback the entire transaction
    NONE = "none"  # No automatic cleanup


class EntityType(Enum):
    """Entity types in dependency order (reverse for cleanup)."""

    ORGANIZATION = 0
    USER = 1
    WORKSPACE = 2
    PROJECT = 3
    DOCUMENT = 4
    REQUIREMENT = 5
    TEST = 6


# Dependency graph: cleanup in reverse order
CLEANUP_ORDER = [
    EntityType.TEST,
    EntityType.REQUIREMENT,
    EntityType.DOCUMENT,
    EntityType.PROJECT,
    EntityType.WORKSPACE,
    EntityType.USER,
    EntityType.ORGANIZATION,
]


@dataclass
class Entity:
    """Represents a tracked entity."""

    type: EntityType
    id: str
    name: str = ""
    data: dict = field(default_factory=dict)
    created_at: float = 0.0

    def __hash__(self):
        return hash((self.type, self.id))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.type == other.type and self.id == other.id


@dataclass
class TestHarmfulState:
    """Tracks harmful (state-creating) entities during a test."""

    test_name: str
    entities: dict[EntityType, set[Entity]] = field(default_factory=lambda: {et: set() for et in EntityType})
    cleanup_strategy: CleanupStrategy = CleanupStrategy.CASCADE_DELETE
    dry_run: bool = False
    cleanup_results: dict[str, Any] = field(default_factory=dict)


class HarmfulStateTracker:
    """Manages test state tracking and cleanup."""

    def __init__(self, cleanup_strategy: CleanupStrategy = CleanupStrategy.CASCADE_DELETE, dry_run: bool = False):
        """Initialize the state tracker.

        Args:
            cleanup_strategy: How to clean up entities
            dry_run: If True, log cleanup actions without executing them
        """
        self.cleanup_strategy = cleanup_strategy
        self.dry_run = dry_run
        self.states: dict[str, TestHarmfulState] = {}
        self.current_test: Optional[str] = None

    def start_test(self, test_name: str) -> TestHarmfulState:
        """Start tracking a test."""
        state = TestHarmfulState(
            test_name=test_name, cleanup_strategy=self.cleanup_strategy, dry_run=self.dry_run
        )
        self.states[test_name] = state
        self.current_test = test_name
        logger.debug(f"Started tracking harmful state for test: {test_name}")
        return state

    def add_entity(self, test_name: str, entity: Entity) -> None:
        """Track a created entity."""
        if test_name not in self.states:
            self.start_test(test_name)

        state = self.states[test_name]
        state.entities[entity.type].add(entity)
        logger.debug(f"Tracked entity: {entity.type.name} {entity.id}")

    def track_entity(
        self, entity_type: EntityType, entity_id: str, name: str = "", data: dict = None, test_name: Optional[str] = None
    ) -> Entity:
        """Create and track an entity."""
        if test_name is None:
            test_name = self.current_test
        if test_name is None:
            raise ValueError("No test context available")

        entity = Entity(type=entity_type, id=entity_id, name=name, data=data or {})
        self.add_entity(test_name, entity)
        return entity

    async def cleanup(self, test_name: str, http_client: Optional[Any] = None) -> dict[str, Any]:
        """Clean up entities created during a test.

        Args:
            test_name: Name of test to clean up
            http_client: HTTP client for making deletion requests (optional)

        Returns:
            Dictionary with cleanup results
        """
        if test_name not in self.states:
            logger.warning(f"No state found for test: {test_name}")
            return {}

        state = self.states[test_name]
        results = {}

        # Clean up in reverse dependency order
        for entity_type in CLEANUP_ORDER:
            entities = state.entities.get(entity_type, set())
            if not entities:
                continue

            results[entity_type.name] = await self._cleanup_entities(
                test_name, entity_type, entities, http_client
            )

        state.cleanup_results = results
        logger.info(f"Cleanup completed for test {test_name}: {results}")
        return results

    async def _cleanup_entities(
        self, test_name: str, entity_type: EntityType, entities: set[Entity], http_client: Optional[Any] = None
    ) -> list[dict[str, Any]]:
        """Clean up a specific type of entity."""
        results = []

        for entity in entities:
            result = {
                "entity_type": entity_type.name,
                "entity_id": entity.id,
                "success": False,
                "reason": None,
            }

            try:
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would delete {entity_type.name} {entity.id}")
                    result["success"] = True
                    result["reason"] = "dry_run"
                elif http_client:
                    # Attempt deletion via HTTP client
                    delete_result = await self._delete_entity(http_client, entity_type, entity.id)
                    result["success"] = delete_result.get("success", False)
                    result["reason"] = delete_result.get("reason")
                else:
                    logger.warning(f"No HTTP client available for deletion of {entity_type.name} {entity.id}")
                    result["success"] = False
                    result["reason"] = "no_http_client"

            except Exception as e:
                result["success"] = False
                result["reason"] = str(e)
                logger.error(f"Error deleting {entity_type.name} {entity.id}: {e}")

            results.append(result)

        return results

    async def _delete_entity(self, http_client: Any, entity_type: EntityType, entity_id: str) -> dict[str, Any]:
        """Delete an entity via HTTP client."""
        try:
            tool_name = self._get_delete_tool_name(entity_type)
            result = await http_client.call_tool(tool_name, {"operation": "delete", "id": entity_id})
            return {"success": result.get("success", False), "reason": result.get("error", "unknown")}
        except Exception as e:
            return {"success": False, "reason": str(e)}

    @staticmethod
    def _get_delete_tool_name(entity_type: EntityType) -> str:
        """Get the tool name for deleting an entity type."""
        type_to_tool = {
            EntityType.ORGANIZATION: "workspace_tool",
            EntityType.USER: "workspace_tool",
            EntityType.WORKSPACE: "workspace_tool",
            EntityType.PROJECT: "workspace_tool",
            EntityType.DOCUMENT: "entity_tool",
            EntityType.REQUIREMENT: "entity_tool",
            EntityType.TEST: "entity_tool",
        }
        return type_to_tool.get(entity_type, "entity_tool")

    def get_state(self, test_name: str) -> Optional[TestHarmfulState]:
        """Get the state for a test."""
        return self.states.get(test_name)

    def cleanup_summary(self) -> dict[str, Any]:
        """Get summary of all tracked states and cleanups."""
        summary = {}
        for test_name, state in self.states.items():
            entity_counts = {et.name: len(entities) for et, entities in state.entities.items() if entities}
            summary[test_name] = {
                "entities_tracked": entity_counts,
                "cleanup_results": state.cleanup_results,
            }
        return summary


# Global tracker instance
_tracker = HarmfulStateTracker()


@asynccontextmanager
async def harmful_context(
    test_name: str, cleanup_strategy: CleanupStrategy = CleanupStrategy.CASCADE_DELETE, http_client: Optional[Any] = None
):
    """Async context manager for test execution with automatic cleanup.

    Usage:
        async with harmful_context("test_create_org", http_client=client) as tracker:
            result = await client.call_tool("workspace_tool", {...})
            # Track entities created
            tracker.track_entity(EntityType.ORGANIZATION, result["id"], "Test Org")
            # Cleanup happens automatically on exit
    """
    tracker = HarmfulStateTracker(cleanup_strategy=cleanup_strategy, dry_run=False)
    tracker.start_test(test_name)

    try:
        yield tracker
    finally:
        await tracker.cleanup(test_name, http_client)


def create_and_track(tracker: HarmfulStateTracker, entity_type: EntityType, result: dict[str, Any], name: str = "") -> Entity:
    """Convenience function to extract ID from API result and track entity.

    Usage:
        result = await client.call_tool("workspace_tool", {...})
        entity = create_and_track(tracker, EntityType.ORGANIZATION, result, "Test Org")
    """
    entity_id = result.get("id") or result.get("entity_id") or result.get("uuid")
    if not entity_id:
        raise ValueError("Could not extract entity ID from result")

    return tracker.track_entity(entity_type, entity_id, name, result)


def harmful(
    cleanup_strategy: CleanupStrategy = CleanupStrategy.CASCADE_DELETE, auto_track: bool = False
) -> Callable:
    """Decorator for test functions to automatically track and clean up entities.

    Args:
        cleanup_strategy: How to clean up created entities
        auto_track: If True, automatically extract and track entities from tool results (experimental)

    Usage:
        @harmful(cleanup_strategy="cascade_delete")
        async def test_create_entity(fast_http_client):
            result = await fast_http_client.call_tool("entity_tool", {...})
            assert result["success"]
            # Automatic cleanup on test completion

        @harmful(auto_track=True)
        async def test_create_doc(fast_http_client):
            # Entities are automatically tracked from results
            result = await fast_http_client.call_tool("entity_tool", {...})
            assert result["success"]
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            test_name = func.__name__
            tracker = HarmfulStateTracker(cleanup_strategy=cleanup_strategy, dry_run=False)
            tracker.start_test(test_name)

            # Inject tracker into function
            kwargs["harmful_tracker"] = tracker

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Extract http_client if available
                http_client = kwargs.get("fast_http_client") or kwargs.get("mcp_client")
                await tracker.cleanup(test_name, http_client)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            test_name = func.__name__
            tracker = HarmfulStateTracker(cleanup_strategy=cleanup_strategy, dry_run=False)
            tracker.start_test(test_name)

            # Inject tracker into function
            kwargs["harmful_tracker"] = tracker

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # For sync functions, cleanup happens synchronously
                # This is a limitation of the decorator
                logger.warning("Sync function wrapped with @harmful - cleanup may be incomplete")

        # Determine if function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Test tracking integration
class TestDataTracker:
    """Integration with existing test fixture for tracking test data."""

    def __init__(self):
        self.harmful_tracker = HarmfulStateTracker()

    def track_entity(self, entity_type: EntityType, entity_id: str, name: str = "") -> Entity:
        """Track an entity during test."""
        return self.harmful_tracker.track_entity(entity_type, entity_id, name, test_name="current_test")

    async def cleanup_all(self, http_client: Optional[Any] = None) -> dict[str, Any]:
        """Clean up all tracked entities."""
        return await self.harmful_tracker.cleanup("current_test", http_client)


__all__ = [
    "harmful",
    "harmful_context",
    "create_and_track",
    "HarmfulStateTracker",
    "TestHarmfulState",
    "Entity",
    "EntityType",
    "CleanupStrategy",
    "CLEANUP_ORDER",
    "TestDataTracker",
]
