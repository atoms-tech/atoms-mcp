"""
Comprehensive pytest configuration and fixtures for refactored Atoms MCP tests.

This module provides all necessary fixtures for testing the refactored
Atoms MCP application following hexagonal architecture with 100% coverage.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from atoms_mcp.domain.models.entity import (
    DocumentEntity,
    Entity,
    EntityStatus,
    ProjectEntity,
    TaskEntity,
    WorkspaceEntity,
)
from atoms_mcp.domain.models.relationship import Relationship, RelationType
from atoms_mcp.domain.models.workflow import Workflow, WorkflowStatus, WorkflowStep
from atoms_mcp.domain.ports.cache import Cache
from atoms_mcp.domain.ports.logger import Logger
from atoms_mcp.domain.ports.repository import Repository
from atoms_mcp.infrastructure.config.settings import Settings, reset_settings


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "usability: API usability tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Clean environment variables before each test."""
    test_env = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_API_KEY": "test_api_key",
        "VERTEX_AI_PROJECT_ID": "test_project",
        "WORKOS_API_KEY": "test_workos_key",
        "CACHE_BACKEND": "memory",
        "LOG_LEVEL": "ERROR",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    yield
    reset_settings()


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings instance."""
    reset_settings()
    return Settings()


# =============================================================================
# MOCK LOGGER FIXTURE
# =============================================================================


class MockLogger(Logger):
    """Mock logger implementation for testing."""

    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self._context: Dict[str, Any] = {}

    def debug(self, message: str, **kwargs) -> None:
        self.logs.append({"level": "DEBUG", "message": message, **kwargs})

    def info(self, message: str, **kwargs) -> None:
        self.logs.append({"level": "INFO", "message": message, **kwargs})

    def warning(self, message: str, **kwargs) -> None:
        self.logs.append({"level": "WARNING", "message": message, **kwargs})

    def error(self, message: str, **kwargs) -> None:
        self.logs.append({"level": "ERROR", "message": message, **kwargs})

    def critical(self, message: str, **kwargs) -> None:
        self.logs.append({"level": "CRITICAL", "message": message, **kwargs})

    def set_context(self, **kwargs) -> None:
        self._context.update(kwargs)

    def clear_context(self) -> None:
        self._context.clear()

    def get_logs(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        if level:
            return [log for log in self.logs if log["level"] == level]
        return self.logs

    def clear_logs(self) -> None:
        self.logs.clear()


@pytest.fixture
def mock_logger() -> MockLogger:
    """Provide a mock logger instance."""
    return MockLogger()


# =============================================================================
# MOCK CACHE FIXTURE
# =============================================================================


class MockCache(Cache):
    """Mock cache implementation for testing."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttls: Dict[str, datetime] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._ttls and datetime.utcnow() > self._ttls[key]:
            del self._store[key]
            del self._ttls[key]
            return None
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = value
        if ttl:
            self._ttls[key] = datetime.utcnow() + timedelta(seconds=ttl)

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            if key in self._ttls:
                del self._ttls[key]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        self._ttls.clear()

    def exists(self, key: str) -> bool:
        return key in self._store

    def keys(self, pattern: str = "*") -> List[str]:
        if pattern == "*":
            return list(self._store.keys())
        return [k for k in self._store.keys() if pattern in k]

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        return {k: self.get(k) for k in keys if self.get(k) is not None}

    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set multiple values in cache."""
        for key, value in data.items():
            self.set(key, value, ttl)


@pytest.fixture
def mock_cache() -> MockCache:
    """Provide a mock cache instance."""
    return MockCache()


# =============================================================================
# MOCK REPOSITORY FIXTURE
# =============================================================================


class MockRepository(Repository[Entity]):
    """Mock repository implementation for testing."""

    def __init__(self):
        self._store: Dict[str, Entity] = {}
        self.save_called = False
        self.get_called = False
        self.delete_called = False
        self.list_called = False
        self.search_called = False
        self.count_called = False

    def save(self, entity: Entity) -> Entity:
        self.save_called = True
        self._store[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Optional[Entity]:
        self.get_called = True
        return self._store.get(entity_id)

    def delete(self, entity_id: str) -> bool:
        self.delete_called = True
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[Entity]:
        self.list_called = True
        entities = list(self._store.values())
        if filters:
            entities = [e for e in entities if self._matches_filters(e, filters)]
        if offset:
            entities = entities[offset:]
        if limit:
            entities = entities[:limit]
        return entities

    def search(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Entity]:
        self.search_called = True
        results = []
        for entity in self._store.values():
            if self._matches_query(entity, query, fields):
                results.append(entity)
        if limit:
            results = results[:limit]
        return results

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        self.count_called = True
        entities = list(self._store.values())
        if filters:
            entities = [e for e in entities if self._matches_filters(e, filters)]
        return len(entities)

    def _matches_filters(self, entity: Entity, filters: Dict[str, Any]) -> bool:
        for field, value in filters.items():
            if not hasattr(entity, field):
                return False

            attr_value = getattr(entity, field)

            # Handle enum comparisons - compare by value if needed
            if hasattr(attr_value, 'value'):
                attr_value = attr_value.value
            if hasattr(value, 'value'):
                value = value.value

            if attr_value != value:
                return False
        return True

    def _matches_query(self, entity: Entity, query: str, fields: Optional[List[str]]) -> bool:
        query_lower = query.lower()
        if fields:
            for field in fields:
                if hasattr(entity, field):
                    value = str(getattr(entity, field)).lower()
                    if query_lower in value:
                        return True
        return False

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists in repository."""
        return entity_id in self._store

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the repository (alias for save)."""
        self.save(entity)

    def clear(self) -> None:
        self._store.clear()


@pytest.fixture
def mock_repository() -> MockRepository:
    """Provide a mock repository instance."""
    return MockRepository()


# =============================================================================
# ENTITY FIXTURES
# =============================================================================


@pytest.fixture
def sample_workspace() -> WorkspaceEntity:
    """Create a sample workspace entity."""
    return WorkspaceEntity(
        id=str(uuid4()),
        name="Test Workspace",
        description="A test workspace",
        owner_id="owner_123",
        settings={"theme": "dark"},
    )


@pytest.fixture
def sample_project() -> ProjectEntity:
    """Create a sample project entity."""
    return ProjectEntity(
        id=str(uuid4()),
        name="Test Project",
        description="A test project",
        workspace_id="workspace_123",
        priority=4,
        tags=["test"],
    )


@pytest.fixture
def sample_task() -> TaskEntity:
    """Create a sample task entity."""
    return TaskEntity(
        id=str(uuid4()),
        title="Test Task",
        description="A test task",
        project_id="project_123",
        priority=3,
        estimated_hours=8.0,
    )


@pytest.fixture
def sample_document() -> DocumentEntity:
    """Create a sample document entity."""
    return DocumentEntity(
        id=str(uuid4()),
        title="Test Document",
        content="Test content",
        project_id="project_123",
        author_id="user_123",
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_test_entity(entity_type: str = "workspace", **kwargs) -> Entity:
    """Helper to create test entities dynamically."""
    entity_id = kwargs.get("id", str(uuid4()))

    if entity_type == "workspace":
        return WorkspaceEntity(
            id=entity_id,
            name=kwargs.get("name", "Test Workspace"),
            description=kwargs.get("description", ""),
            owner_id=kwargs.get("owner_id", "owner_123"),
        )
    elif entity_type == "project":
        return ProjectEntity(
            id=entity_id,
            name=kwargs.get("name", "Test Project"),
            description=kwargs.get("description", ""),
            workspace_id=kwargs.get("workspace_id", "workspace_123"),
            priority=kwargs.get("priority", 3),
        )
    elif entity_type == "task":
        return TaskEntity(
            id=entity_id,
            title=kwargs.get("title", "Test Task"),
            description=kwargs.get("description", ""),
            project_id=kwargs.get("project_id", "project_123"),
        )
    else:
        return Entity(id=entity_id)
