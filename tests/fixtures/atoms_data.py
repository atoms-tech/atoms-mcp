"""Atoms-specific data fixtures for test data generation and management."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytest


@pytest.fixture
def sample_workspace_data() -> dict[str, Any]:
    """Sample Atoms workspace data for testing."""
    return {
        "name": f"Test Workspace {uuid.uuid4().hex[:8]}",
        "description": "Test workspace created by automated tests",
        "settings": {
            "privacy": "private",
            "collaboration_enabled": True
        }
    }


@pytest.fixture
def sample_entity_data() -> dict[str, Any]:
    """Sample Atoms entity data for testing."""
    return {
        "title": f"Test Entity {uuid.uuid4().hex[:8]}",
        "content": "This is test content for automated testing",
        "entity_type": "document",
        "metadata": {
            "created_by": "test_user",
            "created_at": datetime.now().isoformat(),
            "tags": ["test", "automated"]
        }
    }


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample Atoms user data for testing."""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "email": f"test.user.{unique_id}@example.com",
        "name": f"Test User {unique_id}",
        "role": "member"
    }


@pytest.fixture
def test_data_factory() -> Callable[[str], dict[str, Any]]:
    """Factory for generating various types of Atoms test data.

    Usage:
        def test_create_entity(test_data_factory):
            entity_data = test_data_factory("entity")
            # Use entity_data in test
    """
    def create_test_data(data_type: str) -> dict[str, Any]:
        unique_id = uuid.uuid4().hex[:8]

        if data_type == "workspace":
            return {
                "name": f"Test Workspace {unique_id}",
                "description": f"Automated test workspace {unique_id}",
                "settings": {"privacy": "private"}
            }

        if data_type == "entity":
            return {
                "title": f"Test Entity {unique_id}",
                "content": f"Test content {unique_id}",
                "entity_type": "document"
            }

        if data_type == "user":
            return {
                "email": f"test.user.{unique_id}@example.com",
                "name": f"Test User {unique_id}",
                "role": "member"
            }

        if data_type == "project":
            return {
                "name": f"Test Project {unique_id}",
                "description": f"Automated test project {unique_id}",
                "status": "active"
            }

        if data_type == "organization":
            # Atoms-specific organization data
            import re
            unique_slug = str(uuid.uuid4())[:8]
            unique_slug = re.sub(r"[^a-z0-9-]", "", unique_slug.lower())
            if not unique_slug or not unique_slug[0].isalpha():
                unique_slug = f"org{unique_slug}"
            return {
                "name": f"Test Organization {unique_id}",
                "slug": unique_slug,
                "description": f"Automated test organization {unique_id}",
                "type": "team"
            }

        return {"id": unique_id, "type": data_type}

    return create_test_data


@pytest.fixture
def bulk_test_data() -> Callable[[str, int], list[dict[str, Any]]]:
    """Factory for generating bulk Atoms test data.

    Usage:
        def test_bulk_operations(bulk_test_data):
            entities = bulk_test_data("entity", 10)
            # Process 10 test entities
    """
    def create_bulk_data(data_type: str, count: int) -> list[dict[str, Any]]:
        # Use the test_data_factory from this module
        from .atoms_data import test_data_factory
        factory = test_data_factory()
        return [factory(data_type) for _ in range(count)]

    return create_bulk_data


@pytest.fixture(scope="session")
def persistent_test_workspace() -> dict[str, Any]:
    """Session-scoped test workspace for tests that need shared Atoms state."""
    return {
        "name": f"Persistent Test Workspace {uuid.uuid4().hex[:8]}",
        "description": "Persistent workspace for session-scoped tests",
        "created_for_session": True
    }


@pytest.fixture
def cleanup_test_data():
    """Fixture that tracks and cleans up Atoms test data.

    Usage:
        def test_create_entity(entity_client, cleanup_test_data):
            result = await entity_client.call("create", {...})
            cleanup_test_data.track("entity", result["id"])
            # Entity will be cleaned up after test
    """
    created_items = []

    class TestDataTracker:
        def track(self, item_type: str, item_id: str):
            created_items.append({"type": item_type, "id": item_id})

        def get_tracked_items(self):
            return created_items.copy()

    tracker = TestDataTracker()
    yield tracker

    # Cleanup logic would go here
    # For now, just log what would be cleaned up
    if created_items:
        print(f"Would clean up {len(created_items)} test items: {created_items}")


# Realistic Atoms test data patterns
@pytest.fixture
def realistic_document_data() -> dict[str, Any]:
    """Realistic Atoms document data with proper structure."""
    return {
        "title": "Product Requirements Document - Q1 2024",
        "content": """
        # Product Requirements Document

        ## Overview
        This document outlines the requirements for our Q1 2024 product release.

        ## Features
        - Feature A: Core functionality improvements
        - Feature B: User experience enhancements
        - Feature C: Performance optimizations

        ## Acceptance Criteria
        - All features must pass automated testing
        - Performance benchmarks must be met
        - User feedback must be incorporated
        """,
        "entity_type": "document",
        "metadata": {
            "department": "Product",
            "priority": "high",
            "status": "draft",
            "reviewers": ["product-team", "engineering-team"],
            "due_date": "2024-03-31"
        }
    }


@pytest.fixture
def realistic_workspace_structure() -> dict[str, Any]:
    """Realistic Atoms workspace with proper project structure."""
    return {
        "workspace": {
            "name": "Acme Corp Product Development",
            "description": "Main workspace for product development activities"
        },
        "projects": [
            {
                "name": "Q1 Product Release",
                "description": "Major product release for Q1 2024",
                "status": "in_progress"
            },
            {
                "name": "Customer Research",
                "description": "Ongoing customer research and feedback collection",
                "status": "active"
            }
        ],
        "members": [
            {"email": "product.manager@acme.com", "role": "admin"},
            {"email": "engineer@acme.com", "role": "member"},
            {"email": "designer@acme.com", "role": "member"}
        ]
    }
